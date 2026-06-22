"""Evaluate selected PPO checkpoints through an inference controller.

This path supports both current and legacy observation-layout checkpoints because
``PPOLevel2Inference`` already contains the compatibility logic used for deployment.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import gymnasium
import numpy as np
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy
from scipy.spatial.transform import Rotation as R

from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]
GATE_APERTURE_HALF_WIDTH_M = 0.2
GATE_BOXES = {
    "top": (np.array([0.0, 0.0, 0.28]), np.array([0.01, 0.36, 0.08])),
    "bottom": (np.array([0.0, 0.0, -0.28]), np.array([0.01, 0.36, 0.08])),
    "left": (np.array([0.0, -0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "right": (np.array([0.0, 0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "stand": (np.array([0.0, 0.0, -0.86]), np.array([0.05, 0.05, 0.5])),
}


def safe_mean(values: list[float]) -> float:
    """Return NaN for empty lists."""
    return float(np.mean(values)) if values else float("nan")


def safe_percentile(values: list[float], percentile: float) -> float:
    """Return percentile or NaN for empty lists."""
    return float(np.percentile(values, percentile)) if values else float("nan")


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return Wilson score confidence interval for a Bernoulli proportion."""
    if total <= 0:
        return float("nan"), float("nan")
    proportion = successes / total
    denominator = 1.0 + z**2 / total
    center = (proportion + z**2 / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt((proportion * (1.0 - proportion) + z**2 / (4.0 * total)) / total)
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def parse_seed_token(token: str) -> list[int]:
    """Parse one seed token, including inclusive ranges such as 101-200."""
    token = token.strip()
    if not token:
        return []
    match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", token)
    if match:
        start, end = int(match.group(1)), int(match.group(2))
        if end < start:
            raise ValueError(f"invalid descending seed range: {token}")
        return list(range(start, end + 1))
    return [int(token)]


def load_seed_file(path: Path) -> list[int]:
    """Load seeds from newline/comma/range text, JSON list, or JSON object with seeds."""
    text = path.read_text().strip()
    if not text:
        raise ValueError(f"seed file is empty: {path}")
    if text[0] in "[{":
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get("seeds")
        if not isinstance(data, list):
            raise ValueError(f"JSON seed file must be a list or object with seeds: {path}")
        return [int(seed) for seed in data]
    seeds: list[int] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in line.split(","):
            seeds.extend(parse_seed_token(token))
    if not seeds:
        raise ValueError(f"seed file did not contain any seeds: {path}")
    return seeds


def count_dict(values: list[Any]) -> str:
    """Return deterministic JSON counts for a CSV cell."""
    counts = Counter(str(value) for value in values)
    return json.dumps(dict(sorted(counts.items())), sort_keys=True)


def point_box_distance(point: np.ndarray, center: np.ndarray, half_size: np.ndarray) -> float:
    """Return distance from a point to an axis-aligned box."""
    return float(np.linalg.norm(np.maximum(np.abs(point - center) - half_size, 0.0)))


def gate_frame_distance(local_pos: np.ndarray) -> tuple[float, str]:
    """Return nearest target-gate-frame distance and part in gate-local coordinates."""
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


def label_for_checkpoint(path: Path) -> str:
    """Make a compact label that remains unique across checkpoint families."""
    parent = path.parent.name.removeprefix("ppo_level2_")
    stem = path.stem
    step_match = re.search(r"_step_(\d+)$", stem)
    if step_match:
        step = int(step_match.group(1)) // 1_000_000
        return f"{parent}:{step}M"
    return f"{parent}:final"


def reset_controller_state(controller: Any, obs: dict[str, Any], n_history: int) -> None:
    """Reset inference-only recurrent state between episodes."""
    if hasattr(controller, "reset_episode_state"):
        controller.reset_episode_state(obs)
        return
    controller._history = np.repeat(  # noqa: SLF001
        controller._basic_history(obs)[None, :], n_history, axis=0  # noqa: SLF001
    )
    controller._last_action_norm = np.zeros(controller.action_dim, dtype=np.float32)  # noqa: SLF001
    controller._finished = False  # noqa: SLF001


def run_checkpoint(
    checkpoint: Path,
    *,
    config_name: str,
    seeds: list[int],
    seed_split_name: str,
    smooth_coef_rpy: float,
    smooth_coef_thrust: float,
    tilt_limit_deg: float,
    inference_module_name: str,
    confidence_interval: str,
    failure_taxonomy: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run exact single-env episodes for one checkpoint."""
    config = load_config(ROOT / "config" / config_name)
    config.sim.render = False
    inference_module = importlib.import_module(f"lsy_drone_racing.control.{inference_module_name}")
    control_dir = Path(inference_module.__file__).parent
    inference_module.MODEL_NAME = str(checkpoint.resolve().relative_to(control_dir))
    n_history = int(getattr(inference_module, "N_HISTORY", 2))
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
    label = label_for_checkpoint(checkpoint)
    rows: list[dict[str, Any]] = []
    controller = None
    try:
        for seed in seeds:
            obs, info = env.reset(seed=seed)
            if controller is None:
                controller = inference_module.PPOLevel2Inference(obs, info, config)
            else:
                reset_controller_state(controller, obs, n_history)

            steps = 0
            previous_action_norm = np.zeros(controller.action_dim, dtype=np.float64)
            smooth_sum = 0.0
            action_delta_l2: list[float] = []
            tilt_values: list[float] = []
            cmd_tilt_values: list[float] = []
            target_gate = int(np.asarray(obs["target_gate"]).item())
            last_target_before = target_gate
            last_target_after = target_gate
            last_pos = np.asarray(obs["pos"], dtype=np.float64).copy()
            endpoint_pos = last_pos.copy()
            gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64).copy()
            gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64).copy()
            obstacles_pos = np.asarray(obs["obstacles_pos"], dtype=np.float64).copy()
            finished = False
            crashed = False
            timeout = False

            while True:
                last_target_before = int(np.asarray(obs["target_gate"]).item())
                last_pos = np.asarray(obs["pos"], dtype=np.float64).copy()
                action = controller.compute_control(obs, info)
                roll_cmd, pitch_cmd = float(action[0]), float(action[1])
                cmd_body_z_world_z = np.clip(np.cos(roll_cmd) * np.cos(pitch_cmd), -1.0, 1.0)
                cmd_tilt_values.append(float(np.rad2deg(np.arccos(cmd_body_z_world_z))))
                action_norm = np.asarray(controller._last_action_norm, dtype=np.float64)  # noqa: SLF001
                delta = np.clip(action_norm, -1.0, 1.0) - previous_action_norm
                smooth_sum += (
                    smooth_coef_rpy * float(np.sum(delta[:3] ** 2))
                    + smooth_coef_thrust * float(delta[3] ** 2)
                )
                action_delta_l2.append(float(np.linalg.norm(delta)))
                obs, reward, terminated, truncated, info = env.step(action)
                steps += 1
                endpoint_pos = np.asarray(obs["pos"], dtype=np.float64).copy()
                rot = controller.quat_to_rotmat(np.asarray(obs["quat"], dtype=np.float32))
                body_z_world_z = np.clip(float(rot[2, 2]), -1.0, 1.0)
                tilt_values.append(float(np.rad2deg(np.arccos(body_z_world_z))))
                target_gate = int(np.asarray(obs["target_gate"]).item())
                last_target_after = target_gate
                finished = target_gate < 0
                crashed = bool(terminated and not finished)
                timeout = bool(truncated and not finished)
                controller_finished = controller.step_callback(
                    action, obs, reward, terminated, truncated, info
                )
                if terminated or truncated or controller_finished:
                    break
                previous_action_norm = np.clip(action_norm, -1.0, 1.0)

            n_gates = int(np.asarray(obs["gates_pos"]).shape[0])
            row = {
                "checkpoint": label,
                "checkpoint_file": str(checkpoint.relative_to(ROOT)),
                "inference_module": inference_module_name,
                "seed_split": seed_split_name,
                "seed": seed,
                "success": finished,
                "crashed": crashed,
                "timeout": timeout,
                "steps": steps,
                "time_s": steps / float(config.env.freq),
                "target_gate": last_target_before,
                "target_gate_after": last_target_after,
                "total_gates": n_gates,
                "gates": n_gates if finished else max(last_target_after, 0),
                "smooth_penalty_per_step": smooth_sum / steps,
                "mean_action_delta_l2": safe_mean(action_delta_l2),
                "max_tilt_deg": max(tilt_values),
                "tilt_over_limit_frac": safe_mean(
                    [float(value > tilt_limit_deg) for value in tilt_values]
                ),
                "max_cmd_tilt_deg": max(cmd_tilt_values),
                "cmd_tilt_over_limit_frac": safe_mean(
                    [float(value > tilt_limit_deg) for value in cmd_tilt_values]
                ),
            }
            if failure_taxonomy:
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
            rows.append(row)
    finally:
        env.close()

    successes = [row for row in rows if row["success"]]
    success_count = len(successes)
    success_ci_low, success_ci_high = (
        wilson_interval(success_count, len(rows))
        if confidence_interval == "wilson"
        else (float("nan"), float("nan"))
    )
    summary = {
        "checkpoint": label,
        "checkpoint_file": str(checkpoint.relative_to(ROOT)),
        "inference_module": inference_module_name,
        "seed_split": seed_split_name,
        "episodes": len(rows),
        "success_count": success_count,
        "success_rate": safe_mean([float(row["success"]) for row in rows]),
        "success_ci95_low": success_ci_low,
        "success_ci95_high": success_ci_high,
        "crash_rate": safe_mean([float(row["crashed"]) for row in rows]),
        "timeout_rate": safe_mean([float(row["timeout"]) for row in rows]),
        "mean_gates": safe_mean([float(row["gates"]) for row in rows]),
        "mean_time_s_success": safe_mean([float(row["time_s"]) for row in successes]),
        "median_time_s_success": safe_percentile(
            [float(row["time_s"]) for row in successes], 50
        ),
        "p90_time_s_success": safe_percentile([float(row["time_s"]) for row in successes], 90),
        "mean_smooth_penalty_per_step": safe_mean(
            [float(row["smooth_penalty_per_step"]) for row in rows]
        ),
        "mean_action_delta_l2": safe_mean([float(row["mean_action_delta_l2"]) for row in rows]),
        "mean_max_tilt_deg": safe_mean([float(row["max_tilt_deg"]) for row in rows]),
        "worst_tilt_deg": max(float(row["max_tilt_deg"]) for row in rows),
        "tilt_over_limit_frac": safe_mean(
            [float(row["tilt_over_limit_frac"]) for row in rows]
        ),
        "mean_max_cmd_tilt_deg": safe_mean([float(row["max_cmd_tilt_deg"]) for row in rows]),
        "worst_cmd_tilt_deg": max(float(row["max_cmd_tilt_deg"]) for row in rows),
        "cmd_tilt_over_limit_frac": safe_mean(
            [float(row["cmd_tilt_over_limit_frac"]) for row in rows]
        ),
        "success_seeds": json.dumps([int(row["seed"]) for row in successes]),
    }
    if failure_taxonomy:
        failed_rows = [row for row in rows if not row["success"]]
        summary["endpoint_classes"] = count_dict([row["endpoint_class"] for row in rows])
        summary["likely_objects"] = count_dict([row["likely_object"] for row in failed_rows])
        summary["failures_by_target_gate"] = count_dict(
            [row["target_gate"] for row in failed_rows]
        )
        n_gates = int(rows[0].get("total_gates", 0)) if rows else 0
        for gate_idx in range(max(n_gates, 0)):
            gate_failures = [
                row
                for row in failed_rows
                if int(row.get("target_gate", -1)) == gate_idx
            ]
            summary[f"failure_rate_gate_{gate_idx}"] = len(gate_failures) / len(rows)
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write CSV when rows are present."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level2_dr.toml")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--num-seeds", type=int, default=10)
    parser.add_argument(
        "--seed-file",
        type=Path,
        help="Optional seed manifest. Supports integers, comma lists, inclusive ranges, or JSON.",
    )
    parser.add_argument(
        "--seed-split-name",
        help="Label written into episode and summary CSVs, e.g. dev_seen or validation_unseen.",
    )
    parser.add_argument(
        "--confidence-interval",
        choices=["none", "wilson"],
        default="wilson",
        help="Confidence interval method for success_rate.",
    )
    parser.add_argument(
        "--failure-taxonomy",
        action="store_true",
        help="Add endpoint/failure taxonomy columns based on final episode geometry.",
    )
    parser.add_argument("--out-prefix", type=Path, default=ROOT / "evaluation_level2_selected")
    parser.add_argument("--smooth-coef-rpy", type=float, default=0.15)
    parser.add_argument("--smooth-coef-thrust", type=float, default=0.15)
    parser.add_argument("--tilt-limit-deg", type=float, default=30.0)
    parser.add_argument(
        "--inference-module",
        choices=["ppo_level2_inference", "ppo_level3_inference"],
        default="ppo_level2_inference",
        help="Controller module to load and inject the checkpoint into.",
    )
    parser.add_argument("checkpoints", nargs="+", type=Path)
    return parser.parse_args()


def main() -> None:
    """Evaluate selected checkpoints and write summary/episode CSV files."""
    args = parse_args()
    seeds = (
        load_seed_file(args.seed_file)
        if args.seed_file is not None
        else list(range(args.seed_start, args.seed_start + args.num_seeds))
    )
    seed_split_name = args.seed_split_name or (
        args.seed_file.stem if args.seed_file is not None else f"range_{seeds[0]}_{seeds[-1]}"
    )
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for checkpoint in args.checkpoints:
        checkpoint = checkpoint.resolve()
        print(f"evaluating {checkpoint}")
        rows, summary = run_checkpoint(
            checkpoint,
            config_name=args.config,
            seeds=seeds,
            seed_split_name=seed_split_name,
            smooth_coef_rpy=args.smooth_coef_rpy,
            smooth_coef_thrust=args.smooth_coef_thrust,
            tilt_limit_deg=args.tilt_limit_deg,
            inference_module_name=args.inference_module,
            confidence_interval=args.confidence_interval,
            failure_taxonomy=args.failure_taxonomy,
        )
        all_rows.extend(rows)
        summaries.append(summary)
        print(
            f"  success={summary['success_rate']:.2%} "
            f"crash={summary['crash_rate']:.2%} "
            f"time_success={summary['mean_time_s_success']:.2f}s "
            f"smooth={summary['mean_smooth_penalty_per_step']:.4f} "
            f"max_tilt={summary['mean_max_tilt_deg']:.1f}deg "
            f"max_cmd_tilt={summary['mean_max_cmd_tilt_deg']:.1f}deg"
        )

    write_csv(args.out_prefix.with_name(args.out_prefix.name + "_episodes.csv"), all_rows)
    write_csv(args.out_prefix.with_name(args.out_prefix.name + "_summary.csv"), summaries)


if __name__ == "__main__":
    main()
