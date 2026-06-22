"""Trace final gate-transition behavior for Level3 PPO checkpoints.

This is diagnostic-only. It does not train, tune, or modify Level3 configs.
"""

from __future__ import annotations

import argparse
import csv
import importlib
import json
import math
import os
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import gymnasium
import numpy as np
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy
from scipy.spatial.transform import Rotation as R

from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]
DEFAULT_OUT_PREFIX = (
    ROOT
    / "experiments"
    / "level3_ppo_loop"
    / "diagnostics"
    / "level3_gate_transition_traces"
)
GATE_APERTURE_HALF_WIDTH_M = 0.2
GATE_BOXES = {
    "top": (np.array([0.0, 0.0, 0.28]), np.array([0.01, 0.36, 0.08])),
    "bottom": (np.array([0.0, 0.0, -0.28]), np.array([0.01, 0.36, 0.08])),
    "left": (np.array([0.0, -0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "right": (np.array([0.0, 0.28, 0.0]), np.array([0.01, 0.08, 0.36])),
    "stand": (np.array([0.0, 0.0, -0.86]), np.array([0.05, 0.05, 0.5])),
}
INFO_KEYS = [
    "race_passed_gate_rate",
    "race_finished_rate",
    "race_crashed_rate",
    "race_timeout_rate",
    "race_gate_plane_cross_rate",
    "race_gate_plane_center_hit_rate",
    "race_wrong_side_gate_rate",
    "race_gate_frame_pressure",
    "race_obstacle_distance",
    "race_tilt_angle_deg",
    "race_cmd_tilt_deg",
]


def scalar(value: Any, default: float = float("nan")) -> float:
    """Convert an array-like scalar to float."""
    if value is None:
        return default
    array = np.asarray(value).reshape(-1)
    if array.size == 0:
        return default
    return float(array[0])


def bool_scalar(value: Any) -> bool:
    """Convert an array-like scalar to bool."""
    return bool(np.asarray(value).reshape(-1)[0])


def safe_mean(values: list[float]) -> float:
    """Return a finite mean or NaN."""
    finite = [value for value in values if math.isfinite(value)]
    return float(np.mean(finite)) if finite else float("nan")


def percentile(values: list[float], q: float) -> float:
    """Return percentile or NaN."""
    finite = [value for value in values if math.isfinite(value)]
    return float(np.percentile(finite, q)) if finite else float("nan")


def count_dict(values: list[Any]) -> dict[str, int]:
    """Return sorted string-keyed counts."""
    counts = Counter(str(value) for value in values)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def checkpoint_label(path: Path) -> str:
    """Return a compact checkpoint label."""
    parent = path.parent.name
    stem = path.stem
    step_match = re.search(r"_step_(\d+)$", stem)
    if step_match:
        return f"{parent}:{int(step_match.group(1)) // 1_000_000}M"
    return f"{parent}:final"


def display_path(path: Path) -> str:
    """Return a stable repo-relative path when possible."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def reset_controller_state(controller: Any, obs: dict[str, Any], n_history: int) -> None:
    """Reset inference-only state between episodes."""
    if hasattr(controller, "reset_episode_state"):
        controller.reset_episode_state(obs)
        return
    controller._history = np.repeat(  # noqa: SLF001
        controller._basic_history(obs)[None, :],  # noqa: SLF001
        n_history,
        axis=0,
    )
    controller._last_action_norm = np.zeros(controller.action_dim, dtype=np.float32)  # noqa: SLF001
    controller._finished = False  # noqa: SLF001


def point_box_distance(point: np.ndarray, center: np.ndarray, half_size: np.ndarray) -> float:
    """Return distance from a point to an axis-aligned box."""
    return float(np.linalg.norm(np.maximum(np.abs(point - center) - half_size, 0.0)))


def gate_frame_distance(local_pos: np.ndarray) -> tuple[float, str]:
    """Return nearest target gate-frame distance and part in gate-local coordinates."""
    candidates = [
        (point_box_distance(local_pos, center, half_size), part)
        for part, (center, half_size) in GATE_BOXES.items()
    ]
    distance, part = min(candidates, key=lambda item: item[0])
    return distance, part


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


def classify_endpoint(row: dict[str, Any]) -> str:
    """Classify an episode endpoint from the final trace row."""
    if bool(row["success"]):
        return "success"
    if bool(row["timeout"]):
        return "timeout"
    likely_object = str(row["likely_object"])
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


def classify_geometry(
    pos: np.ndarray,
    gates_pos: np.ndarray,
    gates_quat: np.ndarray,
    obstacles_pos: np.ndarray,
    target_gate: int,
) -> dict[str, Any]:
    """Classify nearest collision-like geometry for a position."""
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
        target_local = R.from_quat(gates_quat[target_gate]).inv().apply(
            pos - gates_pos[target_gate]
        )
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


def local_state(
    obs: dict[str, Any],
    target_gate: int,
    *,
    pos: np.ndarray | None = None,
    vel: np.ndarray | None = None,
) -> dict[str, float]:
    """Return position and velocity in the target gate frame."""
    if target_gate < 0:
        return {
            "target_local_x": float("nan"),
            "target_local_y": float("nan"),
            "target_local_z": float("nan"),
            "target_local_vx": float("nan"),
            "target_local_vy": float("nan"),
            "target_local_vz": float("nan"),
            "target_centerline_dist_m": float("nan"),
            "target_aperture_margin_m": float("nan"),
        }
    gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64)
    gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64)
    target_gate = int(target_gate) % len(gates_pos)
    gate_rot = R.from_quat(gates_quat[target_gate])
    pos_value = np.asarray(obs["pos"] if pos is None else pos, dtype=np.float64)
    vel_value = np.asarray(obs["vel"] if vel is None else vel, dtype=np.float64)
    local_pos = gate_rot.inv().apply(pos_value - gates_pos[target_gate])
    local_vel = gate_rot.inv().apply(vel_value)
    centerline_dist = float(np.linalg.norm(local_pos[1:3]))
    aperture_margin = GATE_APERTURE_HALF_WIDTH_M - centerline_dist
    return {
        "target_local_x": float(local_pos[0]),
        "target_local_y": float(local_pos[1]),
        "target_local_z": float(local_pos[2]),
        "target_local_vx": float(local_vel[0]),
        "target_local_vy": float(local_vel[1]),
        "target_local_vz": float(local_vel[2]),
        "target_centerline_dist_m": centerline_dist,
        "target_aperture_margin_m": aperture_margin,
    }


def command_tilt_deg(action: np.ndarray) -> float:
    """Return commanded tilt from scaled roll/pitch command."""
    roll_cmd, pitch_cmd = float(action[0]), float(action[1])
    body_z_world_z = np.clip(np.cos(roll_cmd) * np.cos(pitch_cmd), -1.0, 1.0)
    return float(np.rad2deg(np.arccos(body_z_world_z)))


def actual_tilt_deg(controller: Any, obs: dict[str, Any]) -> float:
    """Return vehicle body tilt angle from the observation quaternion."""
    rot = controller.quat_to_rotmat(np.asarray(obs["quat"], dtype=np.float32))
    body_z_world_z = np.clip(float(rot[2, 2]), -1.0, 1.0)
    return float(np.rad2deg(np.arccos(body_z_world_z)))


def info_metrics(info: dict[str, Any]) -> dict[str, float]:
    """Extract diagnostic scalar metrics from env info."""
    return {key: scalar(info.get(key)) for key in INFO_KEYS}


def final_window_stats(trace_rows: list[dict[str, Any]], tilt_limit_deg: float) -> dict[str, Any]:
    """Summarize the final trace window for one episode."""
    if not trace_rows:
        return {}
    action_sat_values = [float(row["action_sat_frac"]) for row in trace_rows]
    cmd_tilt_values = [float(row["cmd_tilt_deg"]) for row in trace_rows]
    tilt_values = [float(row["tilt_deg"]) for row in trace_rows]
    centerline_values = [float(row["target_centerline_dist_m_before"]) for row in trace_rows]
    obstacle_values = [float(row["nearest_obstacle_distance_m"]) for row in trace_rows]
    frame_values = [float(row["target_gate_frame_distance_m"]) for row in trace_rows]
    return {
        "final_window_steps": len(trace_rows),
        "final_window_action_sat_mean": safe_mean(action_sat_values),
        "final_window_cmd_tilt_max_deg": max(cmd_tilt_values),
        "final_window_cmd_tilt_over_limit_frac": safe_mean(
            [float(value > tilt_limit_deg) for value in cmd_tilt_values]
        ),
        "final_window_tilt_max_deg": max(tilt_values),
        "final_window_tilt_over_limit_frac": safe_mean(
            [float(value > tilt_limit_deg) for value in tilt_values]
        ),
        "final_window_min_centerline_dist_m": min(centerline_values),
        "final_window_min_obstacle_distance_m": min(obstacle_values),
        "final_window_min_gate_frame_distance_m": min(frame_values),
        "final_window_plane_cross_forward": sum(
            int(row["plane_cross_forward"]) for row in trace_rows
        ),
        "final_window_plane_cross_backward": sum(
            int(row["plane_cross_backward"]) for row in trace_rows
        ),
        "final_window_wrong_side_events": sum(
            float(row["race_wrong_side_gate_rate"]) for row in trace_rows
        ),
    }


def run_checkpoint(
    checkpoint: Path,
    *,
    config_name: str,
    seed_start: int,
    num_seeds: int,
    inference_module_name: str,
    trace_window_s: float,
    tilt_limit_deg: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Run one checkpoint and return final-window trace rows and episode rows."""
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
    label = checkpoint_label(checkpoint)
    window_steps = max(1, int(round(trace_window_s * float(config.env.freq))))
    trace_rows: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    controller: Any | None = None

    try:
        for seed in range(seed_start, seed_start + num_seeds):
            obs, info = env.reset(seed=seed)
            if controller is None:
                controller = inference_module.PPOLevel2Inference(obs, info, config)
            else:
                reset_controller_state(controller, obs, n_history)

            episode_window: deque[dict[str, Any]] = deque(maxlen=window_steps)
            all_step_metrics: list[dict[str, float]] = []
            steps = 0
            finished = False
            crashed = False
            timeout = False
            last_target_before = int(np.asarray(obs["target_gate"]).item())
            last_target_after = last_target_before
            previous_action_norm = np.zeros(controller.action_dim, dtype=np.float64)
            gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64).copy()
            gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64).copy()
            obstacles_pos = np.asarray(obs["obstacles_pos"], dtype=np.float64).copy()
            n_gates = gates_pos.shape[0]

            while True:
                target_before = int(np.asarray(obs["target_gate"]).item())
                pos_before = np.asarray(obs["pos"], dtype=np.float64).copy()
                vel_before = np.asarray(obs["vel"], dtype=np.float64).copy()
                local_before = local_state(obs, target_before, pos=pos_before, vel=vel_before)
                geometry_before = classify_geometry(
                    pos_before,
                    gates_pos,
                    gates_quat,
                    obstacles_pos,
                    target_before,
                )
                action = np.asarray(controller.compute_control(obs, info), dtype=np.float64)
                action_norm = np.asarray(
                    controller._last_action_norm, dtype=np.float64  # noqa: SLF001
                )
                action_delta = np.clip(action_norm, -1.0, 1.0) - previous_action_norm
                action_sat_frac = float(np.mean(np.abs(action_norm) >= 0.95))
                cmd_tilt = command_tilt_deg(action)

                obs_next, reward, terminated, truncated, info = env.step(action)
                metrics = info_metrics(info)
                steps += 1
                target_after = int(np.asarray(obs_next["target_gate"]).item())
                local_after = local_state(obs_next, target_before)
                crossed_forward = (
                    math.isfinite(local_before["target_local_x"])
                    and math.isfinite(local_after["target_local_x"])
                    and local_before["target_local_x"] < 0.0 <= local_after["target_local_x"]
                )
                crossed_backward = (
                    math.isfinite(local_before["target_local_x"])
                    and math.isfinite(local_after["target_local_x"])
                    and local_before["target_local_x"] > 0.0 >= local_after["target_local_x"]
                )
                hard_target_changed = target_before >= 0 and target_after != target_before
                finished = target_after < 0
                crashed = bool_scalar(terminated) and not finished
                timeout = bool_scalar(truncated) and not finished
                tilt = metrics["race_tilt_angle_deg"]
                if not math.isfinite(tilt):
                    tilt = actual_tilt_deg(controller, obs_next)
                if not math.isfinite(metrics["race_cmd_tilt_deg"]):
                    metrics["race_cmd_tilt_deg"] = cmd_tilt

                step_row: dict[str, Any] = {
                    "checkpoint": label,
                    "checkpoint_file": str(checkpoint.relative_to(ROOT)),
                    "seed": seed,
                    "step": steps,
                    "time_s": steps / float(config.env.freq),
                    "target_gate_before": target_before,
                    "target_gate_after": target_after,
                    "hard_target_changed": int(hard_target_changed),
                    "success": bool(finished),
                    "crashed": bool(crashed),
                    "timeout": bool(timeout),
                    "reward": scalar(reward),
                    "pos_x": float(pos_before[0]),
                    "pos_y": float(pos_before[1]),
                    "pos_z": float(pos_before[2]),
                    "vel_x": float(vel_before[0]),
                    "vel_y": float(vel_before[1]),
                    "vel_z": float(vel_before[2]),
                    "target_local_x_before": local_before["target_local_x"],
                    "target_local_y_before": local_before["target_local_y"],
                    "target_local_z_before": local_before["target_local_z"],
                    "target_local_vx_before": local_before["target_local_vx"],
                    "target_local_vy_before": local_before["target_local_vy"],
                    "target_local_vz_before": local_before["target_local_vz"],
                    "target_centerline_dist_m_before": local_before[
                        "target_centerline_dist_m"
                    ],
                    "target_aperture_margin_m_before": local_before[
                        "target_aperture_margin_m"
                    ],
                    "target_local_x_after": local_after["target_local_x"],
                    "target_local_y_after": local_after["target_local_y"],
                    "target_local_z_after": local_after["target_local_z"],
                    "plane_cross_forward": int(crossed_forward),
                    "plane_cross_backward": int(crossed_backward),
                    "action_norm_roll": float(action_norm[0]),
                    "action_norm_pitch": float(action_norm[1]),
                    "action_norm_yaw": float(action_norm[2]),
                    "action_norm_thrust": float(action_norm[3]),
                    "action_delta_l2": float(np.linalg.norm(action_delta)),
                    "action_sat_frac": action_sat_frac,
                    "cmd_roll_rad": float(action[0]),
                    "cmd_pitch_rad": float(action[1]),
                    "cmd_yaw_rad": float(action[2]),
                    "cmd_thrust": float(action[3]),
                    "cmd_tilt_deg": cmd_tilt,
                    "tilt_deg": tilt,
                    **geometry_before,
                    **metrics,
                }
                episode_window.append(step_row)
                all_step_metrics.append(metrics)

                controller_finished = controller.step_callback(
                    action,
                    obs_next,
                    scalar(reward),
                    bool_scalar(terminated),
                    bool_scalar(truncated),
                    info,
                )
                obs = obs_next
                previous_action_norm = np.clip(action_norm, -1.0, 1.0)
                last_target_before = target_before
                last_target_after = target_after
                if bool_scalar(terminated) or bool_scalar(truncated) or controller_finished:
                    break

            final_rows = list(episode_window)
            trace_rows.extend(final_rows)
            last_row = final_rows[-1]
            endpoint_class = classify_endpoint(last_row)
            stats = final_window_stats(final_rows, tilt_limit_deg)
            metric_sums = defaultdict(float)
            for metrics in all_step_metrics:
                for key, value in metrics.items():
                    if math.isfinite(value):
                        metric_sums[key] += value
            episode_rows.append(
                {
                    "checkpoint": label,
                    "checkpoint_file": str(checkpoint.relative_to(ROOT)),
                    "seed": seed,
                    "success": bool(finished),
                    "crashed": bool(crashed),
                    "timeout": bool(timeout),
                    "steps": steps,
                    "time_s": steps / float(config.env.freq),
                    "target_gate": last_target_before,
                    "target_gate_after": last_target_after,
                    "gates_passed": n_gates if finished else max(last_target_after, 0),
                    "endpoint_class": endpoint_class,
                    "likely_object": last_row["likely_object"],
                    "target_local_x": last_row["target_local_x"],
                    "target_local_y": last_row["target_local_y"],
                    "target_local_z": last_row["target_local_z"],
                    "nearest_obstacle": last_row["nearest_obstacle"],
                    "nearest_obstacle_distance_m": last_row["nearest_obstacle_distance_m"],
                    "target_gate_frame_part": last_row["target_gate_frame_part"],
                    "target_gate_frame_distance_m": last_row[
                        "target_gate_frame_distance_m"
                    ],
                    "passed_gate_events": metric_sums["race_passed_gate_rate"],
                    "plane_cross_events": metric_sums["race_gate_plane_cross_rate"],
                    "center_hit_events": metric_sums["race_gate_plane_center_hit_rate"],
                    "wrong_side_events": metric_sums["race_wrong_side_gate_rate"],
                    "gate_frame_pressure_sum": metric_sums["race_gate_frame_pressure"],
                    **stats,
                }
            )
            print(
                f"{label} seed={seed} success={finished} crash={crashed} "
                f"gates={episode_rows[-1]['gates_passed']} class={endpoint_class}"
            )
    finally:
        env.close()

    summary = summarize_checkpoint(label, checkpoint, episode_rows)
    return trace_rows, episode_rows, summary


def summarize_checkpoint(
    label: str,
    checkpoint: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate episode rows for one checkpoint."""
    successes = [row for row in rows if row["success"]]
    return {
        "checkpoint": label,
        "checkpoint_file": str(checkpoint.relative_to(ROOT)),
        "episodes": len(rows),
        "success_rate": safe_mean([float(row["success"]) for row in rows]),
        "crash_rate": safe_mean([float(row["crashed"]) for row in rows]),
        "timeout_rate": safe_mean([float(row["timeout"]) for row in rows]),
        "mean_gates": safe_mean([float(row["gates_passed"]) for row in rows]),
        "mean_time_s_success": safe_mean([float(row["time_s"]) for row in successes]),
        "endpoint_classes": count_dict([row["endpoint_class"] for row in rows]),
        "likely_objects": count_dict([row["likely_object"] for row in rows if row["crashed"]]),
        "crashes_by_target_gate": count_dict(
            [row["target_gate"] for row in rows if row["crashed"]]
        ),
        "mean_wrong_side_events": safe_mean(
            [float(row["wrong_side_events"]) for row in rows]
        ),
        "mean_plane_cross_events": safe_mean(
            [float(row["plane_cross_events"]) for row in rows]
        ),
        "mean_center_hit_events": safe_mean(
            [float(row["center_hit_events"]) for row in rows]
        ),
        "mean_frame_pressure_sum": safe_mean(
            [float(row["gate_frame_pressure_sum"]) for row in rows]
        ),
        "mean_final_window_cmd_tilt_over_limit_frac": safe_mean(
            [float(row["final_window_cmd_tilt_over_limit_frac"]) for row in rows]
        ),
        "mean_final_window_tilt_over_limit_frac": safe_mean(
            [float(row["final_window_tilt_over_limit_frac"]) for row in rows]
        ),
        "mean_final_window_action_sat": safe_mean(
            [float(row["final_window_action_sat_mean"]) for row in rows]
        ),
        "p10_final_window_min_obstacle_distance_m": percentile(
            [float(row["final_window_min_obstacle_distance_m"]) for row in rows], 10
        ),
        "p10_final_window_min_gate_frame_distance_m": percentile(
            [float(row["final_window_min_gate_frame_distance_m"]) for row in rows], 10
        ),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write CSV rows with union fieldnames."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    """Write JSON data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Build a markdown table."""
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(
    path: Path,
    summaries: list[dict[str, Any]],
    episode_rows: list[dict[str, Any]],
    trace_csv: Path,
    episode_csv: Path,
    summary_json: Path,
) -> None:
    """Write a markdown diagnostic report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for summary in summaries:
        summary_rows.append(
            [
                summary["checkpoint"],
                f"{summary['success_rate']:.2f}",
                f"{summary['mean_gates']:.2f}",
                f"{summary['crash_rate']:.2f}",
                f"{summary['mean_time_s_success']:.3f}"
                if math.isfinite(summary["mean_time_s_success"])
                else "nan",
                summary["endpoint_classes"],
            ]
        )
    metric_rows = []
    for summary in summaries:
        metric_rows.append(
            [
                summary["checkpoint"],
                f"{summary['mean_wrong_side_events']:.3f}",
                f"{summary['mean_plane_cross_events']:.3f}",
                f"{summary['mean_center_hit_events']:.3f}",
                f"{summary['mean_frame_pressure_sum']:.3f}",
                f"{summary['mean_final_window_cmd_tilt_over_limit_frac']:.3f}",
                f"{summary['mean_final_window_action_sat']:.3f}",
            ]
        )
    by_seed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in episode_rows:
        by_seed[int(row["seed"])].append(row)
    seed_rows = []
    for seed in sorted(by_seed):
        entries = sorted(by_seed[seed], key=lambda item: str(item["checkpoint"]))
        seed_rows.append(
            [
                seed,
                " ; ".join(
                    f"{row['checkpoint']}: {row['gates_passed']}g/{row['endpoint_class']}/"
                    f"{row['likely_object']}"
                    for row in entries
                ),
            ]
        )

    text = f"""# Level3 Gate-Transition Trace Diagnosis

## Scope

This is diagnostic-only. It does not train, tune, or modify Level3 track
geometry/randomization. Acceptance still requires hard eval on
`config/level3_dr.toml`.

Trace CSV: `{display_path(trace_csv)}`

Episode CSV: `{display_path(episode_csv)}`

Summary JSON: `{display_path(summary_json)}`

## Replay Summary

{md_table(['Checkpoint', 'Success', 'Mean Gates', 'Crash', 'Mean Success Time', 'Endpoint Classes'], summary_rows)}

## Conversion And Control Metrics

{md_table(['Checkpoint', 'Wrong Side / Ep', 'Plane Cross / Ep', 'Center Hit / Ep', 'Frame Pressure / Ep', 'Cmd Tilt Over Limit', 'Action Sat'], metric_rows)}

## Per-Seed Endpoint Summary

{md_table(['Seed', 'Checkpoint Outcomes'], seed_rows)}

## Interpretation

- Use this report to choose between observation, controller/action smoothing,
  curriculum/seed triage, or continued hold.
- Do not treat this diagnostic replay as replacing official hard-eval summary
  CSVs. The hard-eval CSV remains the metric source for best checkpoint and
  target completion.
"""
    path.write_text(text)


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--num-seeds", type=int, default=20)
    parser.add_argument("--trace-window-s", type=float, default=2.0)
    parser.add_argument("--tilt-limit-deg", type=float, default=40.0)
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument(
        "--inference-module",
        choices=["ppo_level2_inference", "ppo_level3_inference"],
        default="ppo_level3_inference",
    )
    parser.add_argument("checkpoints", nargs="+", type=Path)
    return parser.parse_args()


def main() -> None:
    """Run trace diagnostics."""
    args = parse_args()
    all_trace_rows: list[dict[str, Any]] = []
    all_episode_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for checkpoint in args.checkpoints:
        checkpoint = checkpoint.resolve()
        trace_rows, episode_rows, summary = run_checkpoint(
            checkpoint,
            config_name=args.config,
            seed_start=args.seed_start,
            num_seeds=args.num_seeds,
            inference_module_name=args.inference_module,
            trace_window_s=args.trace_window_s,
            tilt_limit_deg=args.tilt_limit_deg,
        )
        all_trace_rows.extend(trace_rows)
        all_episode_rows.extend(episode_rows)
        summaries.append(summary)

    trace_csv = args.out_prefix.with_name(args.out_prefix.name + "_trace.csv")
    episode_csv = args.out_prefix.with_name(args.out_prefix.name + "_episodes.csv")
    summary_json = args.out_prefix.with_name(args.out_prefix.name + "_summary.json")
    report_md = args.out_prefix.with_name(args.out_prefix.name + "_report.md")
    write_csv(trace_csv, all_trace_rows)
    write_csv(episode_csv, all_episode_rows)
    write_json(summary_json, summaries)
    write_report(report_md, summaries, all_episode_rows, trace_csv, episode_csv, summary_json)
    print(f"wrote {trace_csv}")
    print(f"wrote {episode_csv}")
    print(f"wrote {summary_json}")
    print(f"wrote {report_md}")


if __name__ == "__main__":
    main()
