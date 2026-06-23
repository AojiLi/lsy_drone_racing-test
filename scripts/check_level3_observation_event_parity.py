"""Check Level3 PPO training/inference observation and event parity.

This script is diagnostic-only. It does not train, tune, or change configs.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import gymnasium
import jax.numpy as jp
import numpy as np
import torch
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.control import ppo_level3_inference
from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_GATE_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUTS,
    LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUTS,
    LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUTS,
    LOCAL_NEXT_GATE_OBSERVATION_LAYOUTS,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUTS,
    LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUTS,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import Level2RaceReward, RaceObservation
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]


def as_float(value: Any) -> float:
    """Convert scalar array-like values to float."""
    return float(np.asarray(value).reshape(-1)[0])


def as_bool(value: Any) -> bool:
    """Convert scalar array-like values to bool."""
    return bool(np.asarray(value).reshape(-1)[0])


def batch_obs(obs: dict[str, Any]) -> dict[str, Any]:
    """Add a leading batch axis to a single-environment observation."""
    return {key: jp.asarray(np.asarray(value)[None, ...]) for key, value in obs.items()}


def make_training_obs_probe(
    obs: dict[str, Any],
    n_history: int,
    observation_layout: str,
    action_lowpass_alpha: float,
) -> RaceObservation:
    """Create a lightweight RaceObservation instance for direct flatten calls."""
    probe = object.__new__(RaceObservation)
    probe.n_history = n_history
    probe.debug_obs = False
    probe.observation_layout = observation_layout
    probe.critic_observation_mode = CRITIC_OBSERVATION_SAME_AS_ACTOR
    probe.action_lowpass_alpha = action_lowpass_alpha
    probe._printed_obs_debug = False
    probe.n_gates = int(np.asarray(obs["gates_pos"]).shape[0])
    probe.n_obstacles = int(np.asarray(obs["obstacles_pos"]).shape[0])
    probe.action_dim = 4
    probe.n_local_obstacles = min(RaceObservation.N_LOCAL_OBSTACLES, probe.n_obstacles)
    probe._use_local_obstacles = observation_layout in LOCAL_OBSTACLE_OBSERVATION_LAYOUTS
    probe._use_local_next_gate = observation_layout in LOCAL_NEXT_GATE_OBSERVATION_LAYOUTS
    probe._use_local_phase_progress = observation_layout in LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUTS
    probe._use_local_gate_corridor_obstacles = (
        observation_layout in LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUTS
    )
    probe._use_local_gate_aperture_margin = (
        observation_layout in LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUTS
    )
    probe._use_local_gate_aperture_margin_minimal = (
        observation_layout in LOCAL_GATE_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUTS
    )
    probe.history_dim = (
        RaceObservation.LOCAL_HISTORY_DIM
        if probe._use_local_obstacles
        else RaceObservation.WORLD_HISTORY_DIM
    )
    probe.layout = probe._build_layout()
    probe.obs_dim = probe.layout[-1][1].stop
    return probe


def init_training_history(probe: RaceObservation, obs: dict[str, Any]) -> Any:
    """Return the training wrapper's reset-time history."""
    obs_b = batch_obs(obs)
    basic = probe._basic_history(obs_b)
    return jp.repeat(basic[:, None, :], probe.n_history, axis=1)


def update_training_history(probe: RaceObservation, history: Any, obs: dict[str, Any]) -> Any:
    """Mirror RaceObservation.observations history update."""
    if probe.n_history <= 0:
        return history
    obs_b = batch_obs(obs)
    basic = probe._basic_history(obs_b)
    return jp.concatenate([history[:, 1:, :], basic[:, None, :]], axis=1)


def flatten_training_obs(
    probe: RaceObservation,
    obs: dict[str, Any],
    history: Any,
    last_action_norm: np.ndarray,
) -> np.ndarray:
    """Build the training flat observation vector for one raw observation."""
    flat = probe._flatten_observations(
        batch_obs(obs),
        history,
        jp.asarray(last_action_norm[None, :], dtype=jp.float32),
    )
    return np.asarray(flat[0], dtype=np.float32)


def section_diffs(
    layout: list[tuple[str, slice]],
    train_flat: np.ndarray,
    infer_flat: np.ndarray,
) -> tuple[str | None, float, dict[str, float]]:
    """Return worst observation section and per-section max abs diffs."""
    limit = min(train_flat.size, infer_flat.size)
    if limit == 0:
        return None, float("inf"), {}
    diffs: dict[str, float] = {}
    worst_name: str | None = None
    worst_value = -1.0
    for name, slc in layout:
        if slc.start >= limit:
            continue
        stop = min(slc.stop, limit)
        value = float(np.max(np.abs(train_flat[slc.start : stop] - infer_flat[slc.start : stop])))
        diffs[name] = value
        if value > worst_value:
            worst_name = name
            worst_value = value
    return worst_name, worst_value, diffs


def deterministic_action_norm(controller: Any, obs_rl: np.ndarray) -> np.ndarray:
    """Run the deterministic actor without advancing controller observation state."""
    obs_tensor = torch.tensor(obs_rl, dtype=torch.float32, device=controller.device).unsqueeze(0)
    with torch.no_grad():
        action_norm, _, _, _ = controller.agent.get_action_and_value(
            obs_tensor, deterministic=True
        )
    action = action_norm.squeeze(0).cpu().numpy().astype(np.float32)
    if not np.isfinite(action).all():
        return np.zeros(controller.action_dim, dtype=np.float32)
    return np.clip(action, -1.0, 1.0).astype(np.float32)


def make_reward_probe(obs: dict[str, Any], controller: Any) -> Level2RaceReward:
    """Create a lightweight Level2RaceReward instance for direct metric calls."""
    probe = object.__new__(Level2RaceReward)
    probe.progress_coef = 0.0
    probe.near_gate_coef = 0.0
    probe.gate_bonus = 1.0
    probe.finish_bonus = 1.0
    probe.crash_penalty = 1.0
    probe.rpy_coef = 1.0
    probe.tilt_limit_rad = float(np.deg2rad(40.0))
    probe.tilt_excess_coef = 1.0
    probe.cmd_tilt_coef = 1.0
    probe.act_coef = 1.0
    probe.d_act_th_coef = 1.0
    probe.d_act_xy_coef = 1.0
    probe.gate_axis_coef = 1.0
    probe.gate_stage_coef = 1.0
    probe.gate_front_bonus = 1.0
    probe.gate_plane_bonus = 1.0
    probe.gate_back_bonus = 1.0
    probe.gate_stage_offset = 0.35
    probe.gate_stage_radius = 0.24
    probe.wrong_side_penalty = 1.0
    probe.missed_gate_penalty = 1.0
    probe.obstacle_coef = 1.0
    probe.obstacle_margin = 0.2
    probe.obstacle_clearance_coef = 0.0
    probe.timeout_penalty = 1.0
    probe.time_penalty = 0.0
    probe.reward_structure = "legacy_staged"
    probe.shaping_gamma = 0.99
    probe.debug_every = 0
    probe._action_scale = jp.asarray(controller.action_scale, dtype=jp.float32)
    probe._action_mean = jp.asarray(controller.action_mean, dtype=jp.float32)
    probe._debug_step = 0

    obs_b = batch_obs(obs)
    probe._last_action = jp.zeros((1, 4), dtype=jp.float32)
    probe._prev_gate_dist = probe._gate_distance(obs_b)
    probe._prev_gate_local = probe._gate_frame_pos(obs_b)
    probe._prev_gate_x = probe._prev_gate_local[:, 0]
    probe._prev_target_gate = obs_b["target_gate"]
    probe._gate_stage = jp.zeros((1,), dtype=jp.int32)
    probe._prev_stage_dist = probe._gate_stage_distance(
        obs_b, probe._gate_stage, obs_b["target_gate"]
    )
    probe._back_gate_active = jp.zeros((1,), dtype=bool)
    probe._back_gate_idx = jp.zeros((1,), dtype=jp.int32)
    probe._prev_back_gate_local = jp.zeros((1, 3), dtype=jp.float32)
    probe._prev_obstacle_dist = probe._closest_obstacle_distance(obs_b)
    return probe


def update_reward_probe_state(
    probe: Level2RaceReward,
    obs: dict[str, Any],
    action_norm: np.ndarray,
    new_gate_stage: Any,
    new_back_gate_active: Any,
    new_back_gate_idx: Any,
    new_prev_back_gate_local: Any,
) -> None:
    """Mirror Level2RaceReward.step state updates after a metric call."""
    obs_b = batch_obs(obs)
    probe._prev_gate_dist = probe._gate_distance(obs_b)
    probe._prev_gate_local = probe._gate_frame_pos(obs_b)
    probe._prev_gate_x = probe._prev_gate_local[:, 0]
    probe._prev_target_gate = obs_b["target_gate"]
    probe._gate_stage = new_gate_stage
    probe._prev_stage_dist = probe._gate_stage_distance(
        obs_b, probe._gate_stage, obs_b["target_gate"]
    )
    probe._back_gate_active = new_back_gate_active
    probe._back_gate_idx = new_back_gate_idx
    probe._prev_back_gate_local = new_prev_back_gate_local
    probe._prev_obstacle_dist = probe._closest_obstacle_distance(obs_b)
    probe._last_action = jp.asarray(action_norm[None, :], dtype=jp.float32)


def reward_metrics_for_step(
    probe: Level2RaceReward,
    obs: dict[str, Any],
    action_norm: np.ndarray,
    terminated: bool,
    truncated: bool,
) -> tuple[dict[str, float], tuple[Any, Any, Any, Any]]:
    """Compute reward metrics and return state updates needed by the probe."""
    (
        _reward,
        _components,
        metrics,
        new_gate_stage,
        new_back_gate_active,
        new_back_gate_idx,
        new_prev_back_gate_local,
    ) = probe._reward_components(
        batch_obs(obs),
        jp.asarray(action_norm[None, :], dtype=jp.float32),
        jp.asarray([terminated]),
        jp.asarray([truncated]),
    )
    scalar_metrics = {name: as_float(value) for name, value in metrics.items()}
    return scalar_metrics, (
        new_gate_stage,
        new_back_gate_active,
        new_back_gate_idx,
        new_prev_back_gate_local,
    )


def synthetic_gate_threshold_grid(points_per_axis: int) -> dict[str, Any]:
    """Compare hard gate-box pass area with current and legacy shaped thresholds."""
    coords = np.linspace(-0.35, 0.35, points_per_axis)
    y_grid, z_grid = np.meshgrid(coords, coords, indexing="ij")
    radius = np.sqrt(y_grid**2 + z_grid**2)
    hard_box = (np.abs(y_grid) < 0.225) & (np.abs(z_grid) < 0.225)
    shaped_box = hard_box
    legacy_stage_radius = radius < 0.24
    legacy_missed_radius = radius > 0.25
    hard_fail = ~hard_box
    return {
        "points_per_axis": points_per_axis,
        "grid_points": int(points_per_axis * points_per_axis),
        "hard_box_pass_points": int(np.sum(hard_box)),
        "current_shaped_box_points": int(np.sum(shaped_box)),
        "current_hard_pass_outside_shaped_points": int(np.sum(hard_box & ~shaped_box)),
        "current_shaped_outside_hard_box_points": int(np.sum(shaped_box & hard_fail)),
        "current_hard_fail_not_missed_points": int(np.sum(hard_fail & shaped_box)),
        "hard_gate_half_width_m": 0.225,
        "legacy_reward_stage_radius_m": 0.24,
        "legacy_reward_missed_radius_m": 0.25,
        "legacy_stage_radius_points": int(np.sum(legacy_stage_radius)),
        "legacy_hard_pass_outside_stage_radius_points": int(
            np.sum(hard_box & ~legacy_stage_radius)
        ),
        "legacy_stage_radius_outside_hard_box_points": int(
            np.sum(legacy_stage_radius & hard_fail)
        ),
        "legacy_hard_fail_not_missed_by_radius_points": int(
            np.sum(hard_fail & ~legacy_missed_radius)
        ),
        "legacy_hard_fail_missed_by_radius_points": int(
            np.sum(hard_fail & legacy_missed_radius)
        ),
    }


def make_env(config_name: str) -> Any:
    """Create the single hard-eval environment."""
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


def inject_checkpoint(checkpoint: Path) -> None:
    """Point ppo_level3_inference at an explicit checkpoint."""
    control_dir = Path(ppo_level3_inference.__file__).parent
    ppo_level3_inference.MODEL_NAME = str(checkpoint.resolve().relative_to(control_dir))


def run_diagnostic(
    *,
    config_name: str,
    checkpoint: Path,
    seed_start: int,
    num_seeds: int,
    max_steps: int,
    tolerance: float,
    synthetic_grid_points: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Run observation and event parity diagnostics."""
    inject_checkpoint(checkpoint)
    env, config = make_env(config_name)
    observation_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    section_max: dict[str, float] = {}
    obs_dim_train: int | None = None
    obs_dim_inference: int | None = None
    controller_layout: str | None = None
    include_prev_gate: bool | None = None

    try:
        for seed in range(seed_start, seed_start + num_seeds):
            obs, info = env.reset(seed=seed)
            controller = ppo_level3_inference.PPOLevel2Inference(obs, info, config)
            obs_probe = make_training_obs_probe(
                obs,
                ppo_level3_inference.N_HISTORY,
                controller.observation_layout,
                controller.action_lowpass_alpha,
            )
            reward_probe = make_reward_probe(obs, controller)
            history = init_training_history(obs_probe, obs)
            last_action_norm = np.zeros(controller.action_dim, dtype=np.float32)
            prev_target_gate = int(np.asarray(obs["target_gate"]).item())

            obs_dim_train = obs_probe.obs_dim
            obs_dim_inference = controller.obs_dim
            controller_layout = str(controller.observation_layout)
            include_prev_gate = bool(controller._include_prev_gate)

            for step in range(max_steps + 1):
                train_flat = flatten_training_obs(obs_probe, obs, history, last_action_norm)
                infer_flat = controller._obs_rl(obs)
                same_dim = train_flat.size == infer_flat.size
                if same_dim:
                    max_abs = float(np.max(np.abs(train_flat - infer_flat)))
                    mean_abs = float(np.mean(np.abs(train_flat - infer_flat)))
                else:
                    limit = min(train_flat.size, infer_flat.size)
                    max_abs = (
                        float(np.max(np.abs(train_flat[:limit] - infer_flat[:limit])))
                        if limit > 0
                        else float("inf")
                    )
                    mean_abs = (
                        float(np.mean(np.abs(train_flat[:limit] - infer_flat[:limit])))
                        if limit > 0
                        else float("inf")
                    )
                worst_section, worst_section_diff, per_section = section_diffs(
                    obs_probe.layout, train_flat, infer_flat
                )
                for name, value in per_section.items():
                    section_max[name] = max(section_max.get(name, 0.0), value)
                observation_rows.append(
                    {
                        "seed": seed,
                        "step": step,
                        "target_gate": int(np.asarray(obs["target_gate"]).item()),
                        "same_dim": same_dim,
                        "train_dim": int(train_flat.size),
                        "inference_dim": int(infer_flat.size),
                        "max_abs_diff": max_abs,
                        "mean_abs_diff": mean_abs,
                        "within_tolerance": same_dim and max_abs <= tolerance,
                        "worst_section": worst_section,
                        "worst_section_max_abs_diff": worst_section_diff,
                    }
                )
                history = update_training_history(obs_probe, history, obs)

                action_norm = deterministic_action_norm(controller, infer_flat)
                controller._last_action_norm = action_norm
                if step >= max_steps:
                    break

                action = controller._scale_action(action_norm)
                obs, _reward, terminated, truncated, _info = env.step(action)
                terminated_bool = as_bool(terminated)
                truncated_bool = as_bool(truncated)
                target_gate = int(np.asarray(obs["target_gate"]).item())
                hard_target_changed = (target_gate != prev_target_gate) and prev_target_gate >= 0
                hard_finished = target_gate < 0
                metrics, reward_state = reward_metrics_for_step(
                    reward_probe,
                    obs,
                    action_norm,
                    terminated_bool,
                    truncated_bool,
                )
                reward_passed = metrics["passed_gate_rate"] > 0.5
                reward_finished = metrics["finished_rate"] > 0.5
                reward_timeout = metrics["timeout_rate"] > 0.5
                event_rows.append(
                    {
                        "seed": seed,
                        "step": step + 1,
                        "prev_target_gate": prev_target_gate,
                        "target_gate": target_gate,
                        "hard_target_changed": hard_target_changed,
                        "reward_passed_gate": reward_passed,
                        "passed_gate_mismatch": hard_target_changed != reward_passed,
                        "hard_finished": hard_finished,
                        "reward_finished": reward_finished,
                        "finished_mismatch": hard_finished != reward_finished,
                        "hard_terminated": terminated_bool,
                        "hard_truncated": truncated_bool,
                        "reward_timeout": reward_timeout,
                        "timeout_mismatch": truncated_bool != reward_timeout,
                        "gate_plane_cross": metrics["gate_plane_cross_rate"] > 0.5,
                        "missed_gate": metrics["missed_gate_rate"] > 0.5,
                        "front_hit": metrics["gate_front_hit_rate"] > 0.5,
                        "pass_hit": metrics["gate_pass_hit_rate"] > 0.5,
                        "back_hit": metrics["gate_back_hit_rate"] > 0.5,
                        "wrong_side_gate": metrics["wrong_side_gate_rate"] > 0.5,
                        "gate_plane_dist": metrics["gate_plane_dist"],
                        "gate_axis_x": metrics["gate_axis_x"],
                        "gate_centerline_dist": metrics["gate_centerline_dist"],
                    }
                )
                update_reward_probe_state(reward_probe, obs, action_norm, *reward_state)
                last_action_norm = action_norm
                prev_target_gate = target_gate
                if terminated_bool or truncated_bool:
                    break
    finally:
        env.close()

    observation_failures = [
        row for row in observation_rows if not bool(row["within_tolerance"])
    ]
    event_pass_mismatches = [row for row in event_rows if bool(row["passed_gate_mismatch"])]
    event_finish_mismatches = [row for row in event_rows if bool(row["finished_mismatch"])]
    event_timeout_mismatches = [row for row in event_rows if bool(row["timeout_mismatch"])]
    synthetic = synthetic_gate_threshold_grid(synthetic_grid_points)
    summary = {
        "config": config_name,
        "checkpoint": str(checkpoint),
        "seed_start": seed_start,
        "num_seeds": num_seeds,
        "max_steps": max_steps,
        "tolerance": tolerance,
        "observation": {
            "samples": len(observation_rows),
            "train_dim": obs_dim_train,
            "inference_dim": obs_dim_inference,
            "controller_observation_layout": controller_layout,
            "controller_include_prev_gate": include_prev_gate,
            "max_abs_diff": max(
                (float(row["max_abs_diff"]) for row in observation_rows), default=None
            ),
            "mean_abs_diff_max": max(
                (float(row["mean_abs_diff"]) for row in observation_rows), default=None
            ),
            "failure_count": len(observation_failures),
            "section_max_abs_diff": section_max,
            "clean": len(observation_failures) == 0,
        },
        "events": {
            "steps": len(event_rows),
            "passed_gate_events": sum(bool(row["reward_passed_gate"]) for row in event_rows),
            "hard_target_changes": sum(bool(row["hard_target_changed"]) for row in event_rows),
            "passed_gate_mismatch_count": len(event_pass_mismatches),
            "finished_mismatch_count": len(event_finish_mismatches),
            "timeout_mismatch_count": len(event_timeout_mismatches),
            "gate_plane_crosses": sum(bool(row["gate_plane_cross"]) for row in event_rows),
            "missed_gate_events": sum(bool(row["missed_gate"]) for row in event_rows),
            "front_hits": sum(bool(row["front_hit"]) for row in event_rows),
            "pass_hits": sum(bool(row["pass_hit"]) for row in event_rows),
            "back_hits": sum(bool(row["back_hit"]) for row in event_rows),
            "wrong_side_gate_events": sum(bool(row["wrong_side_gate"]) for row in event_rows),
            "clean": (
                len(event_pass_mismatches) == 0
                and len(event_finish_mismatches) == 0
                and len(event_timeout_mismatches) == 0
            ),
        },
        "synthetic_gate_thresholds": synthetic,
    }
    summary["clean"] = bool(summary["observation"]["clean"] and summary["events"]["clean"])
    return observation_rows, event_rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write diagnostic rows to CSV."""
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--num-seeds", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--tolerance", type=float, default=1e-5)
    parser.add_argument("--synthetic-grid-points", type=int, default=141)
    parser.add_argument("--out-prefix", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Run diagnostics and write artifacts."""
    args = parse_args()
    observation_rows, event_rows, summary = run_diagnostic(
        config_name=args.config,
        checkpoint=args.checkpoint,
        seed_start=args.seed_start,
        num_seeds=args.num_seeds,
        max_steps=args.max_steps,
        tolerance=args.tolerance,
        synthetic_grid_points=args.synthetic_grid_points,
    )
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    observation_path = args.out_prefix.with_name(args.out_prefix.name + "_observation_rows.csv")
    event_path = args.out_prefix.with_name(args.out_prefix.name + "_event_rows.csv")
    summary_path = args.out_prefix.with_name(args.out_prefix.name + "_summary.json")
    write_csv(observation_path, observation_rows)
    write_csv(event_path, event_rows)
    summary["artifacts"] = {
        "observation_rows_csv": str(observation_path),
        "event_rows_csv": str(event_path),
        "summary_json": str(summary_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
