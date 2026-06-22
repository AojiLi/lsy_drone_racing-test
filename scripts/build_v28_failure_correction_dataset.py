"""Build train-pool failure-correction trajectories for the next Level3 lane.

This script is intentionally offline-data only. It runs an existing checkpoint
on train-pool seeds, records failed episode trajectories, and writes a compressed
dataset plus metadata. It must not use dev_seen, validation_unseen, or
final_locked seeds.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import gymnasium
import numpy as np
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy
from scipy.spatial.transform import Rotation as R

from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCLUDED_SEEDS = "1-20,101-200,1001-1200"
DEFAULT_OUT = (
    "experiments/level3_ppo_loop/failure_datasets/"
    "v28_loop087_train_pool_2112_2211_bounds_failure_trajectories.npz"
)
GATE_BOXES = {
    "top": (np.array([0.0, 0.0, 0.28]), np.array([0.01, 0.36, 0.08])),
    "bottom": (np.array([0.0, 0.0, -0.28]), np.array([0.01, 0.36, 0.08])),
    "left": (np.array([0.0, -0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "right": (np.array([0.0, 0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "stand": (np.array([0.0, 0.0, -0.86]), np.array([0.05, 0.05, 0.5])),
}


def parse_seed_token(token: str) -> list[int]:
    """Parse one integer or inclusive range token."""
    token = token.strip()
    if not token:
        return []
    if "-" in token:
        start_text, end_text = token.split("-", 1)
        start, end = int(start_text), int(end_text)
        if end < start:
            raise ValueError(f"invalid descending seed range: {token}")
        return list(range(start, end + 1))
    return [int(token)]


def parse_seed_ranges(value: str) -> set[int]:
    """Return seeds from a comma-separated integer/range list."""
    seeds: set[int] = set()
    for token in value.split(","):
        seeds.update(parse_seed_token(token))
    return seeds


def repo_path(path: str | Path) -> Path:
    """Resolve a repo-relative or absolute path."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def repo_rel(path: str | Path) -> str:
    """Render a path relative to the repository when possible."""
    value = repo_path(path).resolve()
    try:
        return str(value.relative_to(ROOT))
    except ValueError:
        return str(value)


def point_box_distance(point: np.ndarray, center: np.ndarray, half_size: np.ndarray) -> float:
    """Return distance from a point to an axis-aligned box."""
    return float(np.linalg.norm(np.maximum(np.abs(point - center) - half_size, 0.0)))


def gate_frame_distance(local_pos: np.ndarray) -> tuple[float, str]:
    """Return nearest target-gate-frame distance and frame part."""
    candidates = [
        (point_box_distance(local_pos, center, half_size), part)
        for part, (center, half_size) in GATE_BOXES.items()
    ]
    return min(candidates, key=lambda item: item[0])


def obstacle_cylinder_distance(pos: np.ndarray, obstacle_pos: np.ndarray) -> float:
    """Approximate distance to a vertical obstacle cylinder segment."""
    segment_z = np.clip(pos[2], obstacle_pos[2] - 1.6, obstacle_pos[2])
    segment_distance = np.linalg.norm(pos - np.array([*obstacle_pos[:2], segment_z]))
    return max(float(segment_distance) - 0.015, 0.0)


def nearest_obstacle(pos: np.ndarray, obstacles_pos: np.ndarray) -> tuple[int, float]:
    """Return nearest obstacle id and approximate distance."""
    if obstacles_pos.size == 0:
        return -1, float("nan")
    candidates = [
        (idx, obstacle_cylinder_distance(pos, obstacle_pos))
        for idx, obstacle_pos in enumerate(obstacles_pos)
    ]
    return min(candidates, key=lambda item: item[1])


def classify_geometry(
    pos: np.ndarray,
    gates_pos: np.ndarray,
    gates_quat: np.ndarray,
    obstacles_pos: np.ndarray,
    target_gate: int,
) -> dict[str, Any]:
    """Classify nearest collision-like geometry for a final episode position."""
    gate_local_all = R.from_quat(gates_quat).inv().apply(pos[None, :] - gates_pos)
    gate_candidates: list[tuple[float, int, str]] = []
    for gate_idx, local in enumerate(gate_local_all):
        for part, (center, half_size) in GATE_BOXES.items():
            gate_candidates.append((point_box_distance(local, center, half_size), gate_idx, part))
    gate_distance, nearest_gate, nearest_gate_part = min(gate_candidates)
    nearest_obstacle_idx, obstacle_distance = nearest_obstacle(pos, obstacles_pos)

    nearest_distance = min(gate_distance, obstacle_distance)
    if nearest_distance > 0.25:
        likely_object = "bounds_or_ground"
    elif gate_distance <= obstacle_distance:
        likely_object = f"gate_{nearest_gate}_{nearest_gate_part}"
    else:
        likely_object = f"obstacle_{nearest_obstacle_idx}"

    if 0 <= target_gate < len(gates_pos):
        target_local = R.from_quat(gates_quat[target_gate]).inv().apply(pos - gates_pos[target_gate])
        target_frame_distance, target_frame_part = gate_frame_distance(target_local)
    else:
        target_local = np.full(3, float("nan"))
        target_frame_distance = float("nan")
        target_frame_part = ""

    return {
        "likely_object": likely_object,
        "nearest_object_distance_m": nearest_distance,
        "nearest_gate": nearest_gate,
        "nearest_gate_part": nearest_gate_part,
        "nearest_gate_distance_m": gate_distance,
        "nearest_obstacle": nearest_obstacle_idx,
        "nearest_obstacle_distance_m": obstacle_distance,
        "target_local_x": float(target_local[0]),
        "target_local_y": float(target_local[1]),
        "target_local_z": float(target_local[2]),
        "target_gate_frame_distance_m": target_frame_distance,
        "target_gate_frame_part": target_frame_part,
    }


def classify_endpoint(row: dict[str, Any]) -> str:
    """Classify episode outcome for aggregate failure taxonomy."""
    if bool(row["success"]):
        return "success"
    if bool(row["timeout"]):
        return "timeout"
    likely_object = str(row.get("likely_object", ""))
    target_local_x = float(row.get("target_local_x", float("nan")))
    if likely_object.startswith("obstacle"):
        if math.isfinite(target_local_x) and target_local_x < -0.75:
            return "pre_plane_obstacle"
        return "near_gate_obstacle"
    if likely_object.endswith("_left") or likely_object.endswith("_right"):
        return "gate_side_frame"
    if likely_object.endswith("_top") or likely_object.endswith("_bottom"):
        return "gate_vertical_frame"
    if likely_object == "bounds_or_ground":
        return "bounds_or_ground"
    return "other_crash"


def gate_diagnostics(obs: dict[str, np.ndarray], controller: Any) -> tuple[float, float, float]:
    """Return target-gate local x, lateral error, and nearest obstacle distance."""
    pos = np.asarray(obs["pos"], dtype=np.float32)
    target_gate = int(np.asarray(obs["target_gate"]).item())
    n_gates = int(np.asarray(obs["gates_pos"]).shape[0])
    gate_idx = max(0, target_gate) % n_gates
    gate_pos = np.asarray(obs["gates_pos"], dtype=np.float32)[gate_idx]
    gate_quat = np.asarray(obs["gates_quat"], dtype=np.float32)[gate_idx]
    gate_rot = controller.quat_to_rotmat(gate_quat)
    gate_local = gate_rot.T @ (pos - gate_pos)
    obstacles_pos = np.asarray(obs["obstacles_pos"], dtype=np.float32)
    obstacle_min_dist = float(np.min(np.linalg.norm(obstacles_pos - pos[None, :], axis=-1)))
    return (
        float(gate_local[0]),
        float(np.linalg.norm(gate_local[1:3])),
        obstacle_min_dist,
    )


def controller_from_checkpoint(
    inference_module: Any,
    checkpoint: Path,
    obs: dict[str, np.ndarray],
    info: dict[str, Any],
    config: Any,
) -> Any:
    """Instantiate PPOLevel2Inference with a specific checkpoint."""
    control_dir = Path(inference_module.__file__).parent
    inference_module.MODEL_NAME = str(checkpoint.resolve().relative_to(control_dir))
    return inference_module.PPOLevel2Inference(obs, info, config)


def reset_controller(controller: Any, obs: dict[str, np.ndarray]) -> None:
    """Reset controller episode state."""
    if hasattr(controller, "reset_episode_state"):
        controller.reset_episode_state(obs)
        return
    controller.episode_callback()


def make_env(config_name: str):
    """Create the single-env Level3 evaluator environment."""
    config = load_config(ROOT / "config" / config_name)
    config.sim.render = False
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
    return JaxToNumpy(env), config


def parse_seed_list(value: str | None, start: int, count: int) -> list[int]:
    """Return explicit seeds or a contiguous range."""
    if value:
        seeds: list[int] = []
        for token in value.split(","):
            seeds.extend(parse_seed_token(token))
        return seeds
    return list(range(start, start + count))


def build_dataset(args: argparse.Namespace) -> dict[str, Any]:
    """Collect failed train-pool trajectories."""
    checkpoint = repo_path(args.checkpoint)
    inference_module = importlib.import_module(f"lsy_drone_racing.control.{args.inference_module}")
    env, config = make_env(args.config)
    seeds = parse_seed_list(args.seeds, args.seed_start, args.num_seeds)
    excluded = parse_seed_ranges(args.exclude_seed_ranges)
    bad_seeds = sorted(set(seeds) & excluded)
    if bad_seeds:
        raise ValueError(f"requested seeds include excluded seeds: {bad_seeds[:20]}")
    include_classes = {
        item.strip() for item in args.include_classes.split(",") if item.strip()
    }

    records: dict[str, list[Any]] = {
        "student_obs": [],
        "action_norm": [],
        "action_scaled": [],
        "seed": [],
        "episode_step": [],
        "target_gate": [],
        "gate_axis": [],
        "gate_lateral_error": [],
        "obstacle_min_dist": [],
        "endpoint_class_id": [],
    }
    endpoint_class_names: list[str] = []
    class_to_id: dict[str, int] = {}
    episodes: list[dict[str, Any]] = []
    controller = None

    def endpoint_id(name: str) -> int:
        if name not in class_to_id:
            class_to_id[name] = len(endpoint_class_names)
            endpoint_class_names.append(name)
        return class_to_id[name]

    try:
        for seed in seeds:
            obs, info = env.reset(seed=seed)
            if controller is None:
                controller = controller_from_checkpoint(
                    inference_module,
                    checkpoint,
                    obs,
                    info,
                    config,
                )
            else:
                reset_controller(controller, obs)

            episode: list[dict[str, Any]] = []
            steps = 0
            last_target_before = int(np.asarray(obs["target_gate"]).item())
            last_target_after = last_target_before
            endpoint_pos = np.asarray(obs["pos"], dtype=np.float64).copy()
            gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64).copy()
            gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64).copy()
            obstacles_pos = np.asarray(obs["obstacles_pos"], dtype=np.float64).copy()
            finished = False
            crashed = False
            timeout = False

            while True:
                last_target_before = int(np.asarray(obs["target_gate"]).item())
                student_obs = controller._obs_rl(obs).astype(np.float32)  # noqa: SLF001
                gate_axis, gate_lateral_error, obstacle_min_dist = gate_diagnostics(
                    obs,
                    controller,
                )
                action = controller.compute_control(obs, info)
                action_norm = np.asarray(controller._last_action_norm, dtype=np.float32)  # noqa: SLF001
                episode.append(
                    {
                        "student_obs": student_obs,
                        "action_norm": action_norm,
                        "action_scaled": np.asarray(action, dtype=np.float32),
                        "seed": int(seed),
                        "episode_step": int(steps),
                        "target_gate": int(last_target_before),
                        "gate_axis": gate_axis,
                        "gate_lateral_error": gate_lateral_error,
                        "obstacle_min_dist": obstacle_min_dist,
                    }
                )
                obs, reward, terminated, truncated, info = env.step(action)
                steps += 1
                endpoint_pos = np.asarray(obs["pos"], dtype=np.float64).copy()
                last_target_after = int(np.asarray(obs["target_gate"]).item())
                finished = last_target_after < 0
                crashed = bool(terminated and not finished)
                timeout = bool(truncated and not finished)
                controller_finished = controller.step_callback(
                    action,
                    obs,
                    reward,
                    terminated,
                    truncated,
                    info,
                )
                if terminated or truncated or controller_finished:
                    break

            row: dict[str, Any] = {
                "seed": int(seed),
                "success": bool(finished),
                "crashed": bool(crashed),
                "timeout": bool(timeout),
                "steps": int(steps),
                "time_s": float(steps / float(config.env.freq)),
                "target_gate": int(last_target_before),
                "target_gate_after": int(last_target_after),
                "samples": len(episode),
            }
            row.update(
                classify_geometry(
                    endpoint_pos,
                    gates_pos,
                    gates_quat,
                    obstacles_pos,
                    last_target_before,
                )
            )
            row["endpoint_class"] = classify_endpoint(row)
            episodes.append(row)

            if row["success"] or row["endpoint_class"] not in include_classes:
                continue
            class_id = endpoint_id(row["endpoint_class"])
            for item in episode:
                if len(records["seed"]) >= args.max_samples:
                    break
                for key in (
                    "student_obs",
                    "action_norm",
                    "action_scaled",
                    "seed",
                    "episode_step",
                    "target_gate",
                    "gate_axis",
                    "gate_lateral_error",
                    "obstacle_min_dist",
                ):
                    records[key].append(item[key])
                records["endpoint_class_id"].append(class_id)
    finally:
        env.close()

    if not records["seed"]:
        raise RuntimeError("no failure trajectory samples collected")

    endpoint_counts = Counter(str(row["endpoint_class"]) for row in episodes)
    failure_target_counts = Counter(
        str(row["target_gate"]) for row in episodes if not row["success"]
    )
    selected_seed_counts = Counter(int(seed) for seed in records["seed"])
    metadata = {
        "schema_version": 1,
        "config": args.config,
        "checkpoint": repo_rel(checkpoint),
        "inference_module": args.inference_module,
        "seed_start": args.seed_start,
        "num_seeds": args.num_seeds,
        "seeds": seeds,
        "excluded_seed_ranges": args.exclude_seed_ranges,
        "include_classes": sorted(include_classes),
        "num_samples": len(records["seed"]),
        "num_episodes": len(episodes),
        "num_failure_episodes_recorded": len(selected_seed_counts),
        "endpoint_class_names": endpoint_class_names,
        "endpoint_counts": dict(sorted(endpoint_counts.items())),
        "failures_by_target_gate": dict(sorted(failure_target_counts.items())),
        "selected_failure_seeds": sorted(int(seed) for seed in selected_seed_counts),
        "samples_by_selected_seed": {
            str(seed): int(count) for seed, count in sorted(selected_seed_counts.items())
        },
        "purpose": (
            "v28 failure-correction train-pool trajectories; hard eval remains "
            "config/level3_dr.toml and final_locked seeds are excluded"
        ),
    }
    return {"records": records, "metadata": metadata, "episodes": episodes}


def write_dataset(path: Path, payload: dict[str, Any]) -> None:
    """Write compressed trajectory arrays."""
    records = payload["records"]
    metadata = payload["metadata"]
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        student_obs=np.stack(records["student_obs"]).astype(np.float32),
        action_norm=np.stack(records["action_norm"]).astype(np.float32),
        action_scaled=np.stack(records["action_scaled"]).astype(np.float32),
        seed=np.asarray(records["seed"], dtype=np.int32),
        episode_step=np.asarray(records["episode_step"], dtype=np.int32),
        target_gate=np.asarray(records["target_gate"], dtype=np.int16),
        gate_axis=np.asarray(records["gate_axis"], dtype=np.float32),
        gate_lateral_error=np.asarray(records["gate_lateral_error"], dtype=np.float32),
        obstacle_min_dist=np.asarray(records["obstacle_min_dist"], dtype=np.float32),
        endpoint_class_id=np.asarray(records["endpoint_class_id"], dtype=np.int16),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True), dtype=np.str_),
    )


def write_episode_csv(path: Path, episodes: list[dict[str, Any]]) -> None:
    """Write episode summaries for review."""
    import csv

    if not episodes:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in episodes for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(episodes)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--inference-module", default="ppo_level3_inference")
    parser.add_argument("--seed-start", type=int, default=2112)
    parser.add_argument("--num-seeds", type=int, default=100)
    parser.add_argument("--seeds")
    parser.add_argument("--exclude-seed-ranges", default=DEFAULT_EXCLUDED_SEEDS)
    parser.add_argument("--include-classes", default="bounds_or_ground")
    parser.add_argument("--max-samples", type=int, default=80_000)
    parser.add_argument("--out", type=Path, default=Path(DEFAULT_OUT))
    return parser.parse_args()


def main() -> None:
    """Build and write the dataset."""
    args = parse_args()
    payload = build_dataset(args)
    out_path = repo_path(args.out)
    write_dataset(out_path, payload)
    episode_csv = out_path.with_name(out_path.stem + "_episodes.csv")
    write_episode_csv(episode_csv, payload["episodes"])
    print(
        f"wrote {repo_rel(out_path)} with "
        f"{payload['metadata']['num_samples']} samples from "
        f"{payload['metadata']['num_failure_episodes_recorded']} failure episodes"
    )
    print(f"wrote {repo_rel(episode_csv)}")
    print(json.dumps(payload["metadata"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
