"""Sample Level3 first-gate reset geometry without running a policy."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import gymnasium
import numpy as np
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.utils import load_config
from scipy.spatial.transform import Rotation as R

ROOT = Path(__file__).parents[1]
PERCENTILES = (0, 5, 25, 50, 75, 95, 100)


def safe_percentiles(values: list[float]) -> dict[str, float | None]:
    """Return common percentiles, using nulls for empty inputs."""
    if not values:
        return {str(q): None for q in PERCENTILES}
    arr = np.asarray(values, dtype=np.float64)
    return {str(q): float(np.percentile(arr, q)) for q in PERCENTILES}


def safe_mean(values: list[float]) -> float | None:
    """Return a JSON-safe mean."""
    return float(np.mean(values)) if values else None


def point_segment_distance_xy(point: np.ndarray, start: np.ndarray, end: np.ndarray) -> float:
    """Distance from an XY point to a line segment."""
    segment = end - start
    denom = float(np.dot(segment, segment))
    if denom <= 1e-12:
        return float(np.linalg.norm(point - start))
    t = float(np.clip(np.dot(point - start, segment) / denom, 0.0, 1.0))
    closest = start + t * segment
    return float(np.linalg.norm(point - closest))


def load_crash_rows(path: Path | None) -> dict[int, dict[str, str]]:
    """Load optional crash-taxonomy rows keyed by seed."""
    if path is None:
        return {}
    with path.open(newline="") as handle:
        return {int(row["seed"]): row for row in csv.DictReader(handle)}


def sample_rows(
    *,
    config_name: str,
    seed_start: int,
    num_seeds: int,
    crash_csv: Path | None,
) -> list[dict[str, Any]]:
    """Sample reset geometry for a sequence of seeds."""
    config = load_config(ROOT / "config" / config_name)
    config.sim.render = False
    crash_by_seed = load_crash_rows(crash_csv)
    env = gymnasium.make(
        config.env.id,
        freq=config.env.freq,
        sim_config=config.sim,
        sensor_range=config.env.sensor_range,
        control_mode=config.env.control_mode,
        track=config.env.track,
        disturbances=config.env.get("disturbances"),
        randomizations=config.env.get("randomizations"),
        seed=config.env.seed,
    )
    env = JaxToNumpy(env)
    rows: list[dict[str, Any]] = []
    try:
        for seed in range(seed_start, seed_start + num_seeds):
            obs, _ = env.reset(seed=seed)
            base_env = env.unwrapped
            drone_pos = np.asarray(obs["pos"], dtype=np.float64)
            actual_gate0 = np.asarray(base_env.data.gates_pos[0, 0], dtype=np.float64)
            actual_gate0_quat = np.asarray(base_env.data.gates_quat[0, 0], dtype=np.float64)
            observed_gate0 = np.asarray(obs["gates_pos"], dtype=np.float64)[0]
            gate0_visible = bool(np.asarray(obs["gates_visited"])[0])
            obstacle0 = np.asarray(base_env.data.obstacles_pos[0, 0], dtype=np.float64)

            gate_rot = R.from_quat(actual_gate0_quat)
            start_local = gate_rot.inv().apply(drone_pos - actual_gate0)
            start_to_gate = actual_gate0 - drone_pos
            horizontal_distance = float(np.linalg.norm(start_to_gate[:2]))
            distance_3d = float(np.linalg.norm(start_to_gate))
            observed_actual_error = observed_gate0 - actual_gate0
            corridor_distance = point_segment_distance_xy(
                obstacle0[:2], drone_pos[:2], actual_gate0[:2]
            )
            yaw = float(gate_rot.as_euler("xyz", degrees=False)[2])

            row: dict[str, Any] = {
                "seed": seed,
                "drone_x": float(drone_pos[0]),
                "drone_y": float(drone_pos[1]),
                "drone_z": float(drone_pos[2]),
                "gate0_x": float(actual_gate0[0]),
                "gate0_y": float(actual_gate0[1]),
                "gate0_z": float(actual_gate0[2]),
                "observed_gate0_x": float(observed_gate0[0]),
                "observed_gate0_y": float(observed_gate0[1]),
                "observed_gate0_z": float(observed_gate0[2]),
                "gate0_visible": gate0_visible,
                "gate0_inside_sensor_range_xy": horizontal_distance <= float(config.env.sensor_range),
                "gate0_horizontal_distance_m": horizontal_distance,
                "gate0_distance_3d_m": distance_3d,
                "gate0_vertical_offset_m": float(start_to_gate[2]),
                "start_local_x": float(start_local[0]),
                "start_local_y": float(start_local[1]),
                "start_local_z": float(start_local[2]),
                "gate0_yaw_rad": yaw,
                "obstacle0_x": float(obstacle0[0]),
                "obstacle0_y": float(obstacle0[1]),
                "obstacle0_z": float(obstacle0[2]),
                "obstacle0_corridor_distance_xy_m": corridor_distance,
                "obstacle0_start_distance_xy_m": float(
                    np.linalg.norm(obstacle0[:2] - drone_pos[:2])
                ),
                "obstacle0_gate_distance_xy_m": float(
                    np.linalg.norm(obstacle0[:2] - actual_gate0[:2])
                ),
                "observed_actual_gate0_xy_error_m": float(
                    np.linalg.norm(observed_actual_error[:2])
                ),
                "observed_actual_gate0_z_error_m": float(abs(observed_actual_error[2])),
            }
            if seed in crash_by_seed:
                crash = crash_by_seed[seed]
                row.update(
                    {
                        "crash_success": crash.get("success"),
                        "crash_crashed": crash.get("crashed"),
                        "crash_target_gate": crash.get("target_gate"),
                        "crash_gates_passed": crash.get("gates_passed"),
                        "crash_likely_object": crash.get("likely_object"),
                        "crash_target_local_x": crash.get("target_local_x"),
                        "crash_target_local_y": crash.get("target_local_y"),
                        "crash_target_local_z": crash.get("target_local_z"),
                    }
                )
            rows.append(row)
    finally:
        env.close()
    return rows


def summarize(rows: list[dict[str, Any]], config_name: str) -> dict[str, Any]:
    """Summarize sampled first-gate geometry."""
    metrics = {
        "gate0_horizontal_distance_m": [row["gate0_horizontal_distance_m"] for row in rows],
        "gate0_distance_3d_m": [row["gate0_distance_3d_m"] for row in rows],
        "gate0_vertical_offset_m": [row["gate0_vertical_offset_m"] for row in rows],
        "start_local_x": [row["start_local_x"] for row in rows],
        "abs_start_local_y": [abs(row["start_local_y"]) for row in rows],
        "start_local_z": [row["start_local_z"] for row in rows],
        "obstacle0_corridor_distance_xy_m": [
            row["obstacle0_corridor_distance_xy_m"] for row in rows
        ],
        "observed_actual_gate0_xy_error_m": [
            row["observed_actual_gate0_xy_error_m"] for row in rows
        ],
        "observed_actual_gate0_z_error_m": [
            row["observed_actual_gate0_z_error_m"] for row in rows
        ],
    }
    crash_rows = [row for row in rows if row.get("crash_crashed") == "True"]
    target0_crashes = [row for row in crash_rows if row.get("crash_target_gate") == "0"]
    return {
        "config": config_name,
        "samples": len(rows),
        "gate0_visible_rate": safe_mean([float(row["gate0_visible"]) for row in rows]),
        "gate0_inside_sensor_range_xy_rate": safe_mean(
            [float(row["gate0_inside_sensor_range_xy"]) for row in rows]
        ),
        "obstacle0_corridor_lt_0p2_rate": safe_mean(
            [float(row["obstacle0_corridor_distance_xy_m"] < 0.2) for row in rows]
        ),
        "obstacle0_corridor_lt_0p4_rate": safe_mean(
            [float(row["obstacle0_corridor_distance_xy_m"] < 0.4) for row in rows]
        ),
        "percentiles": {key: safe_percentiles(values) for key, values in metrics.items()},
        "crash_overlap": {
            "samples_with_crash_rows": len(crash_rows),
            "target0_crash_rows": len(target0_crashes),
            "target0_crash_gate0_distance_percentiles": safe_percentiles(
                [row["gate0_horizontal_distance_m"] for row in target0_crashes]
            ),
            "target0_crash_abs_start_local_y_percentiles": safe_percentiles(
                [abs(row["start_local_y"]) for row in target0_crashes]
            ),
            "target0_crash_obstacle0_corridor_percentiles": safe_percentiles(
                [row["obstacle0_corridor_distance_xy_m"] for row in target0_crashes]
            ),
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write sampled rows."""
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--num-seeds", type=int, default=500)
    parser.add_argument("--out-prefix", type=Path, required=True)
    parser.add_argument("--crash-csv", type=Path)
    return parser.parse_args()


def main() -> None:
    """Sample first-gate reset geometry and write CSV/JSON artifacts."""
    args = parse_args()
    rows = sample_rows(
        config_name=args.config,
        seed_start=args.seed_start,
        num_seeds=args.num_seeds,
        crash_csv=args.crash_csv,
    )
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_prefix.with_name(args.out_prefix.name + "_samples.csv")
    json_path = args.out_prefix.with_name(args.out_prefix.name + "_summary.json")
    write_csv(csv_path, rows)
    summary = summarize(rows, args.config)
    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
