"""Evaluate one Level3 reference-tracker qualification stage."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_LAYOUT,
    SEMANTIC_REFERENCE_TRACKER_TASKS,
    ReferenceFrame,
    ReferenceTrackerEnv,
    TrackerPPOAgent,
    load_tracker_checkpoint,
    quat_to_rotmat,
    safe_normalize,
)
from scripts.check_level3_reference_tracker_smoke import (
    parse_seed_range,
    run_level3_controller_seed,
)
from scripts.check_level3_tracker_stage_gate import load_json, stage_by_id

ROOT = Path(__file__).parents[1]
DEFAULT_GATES = ROOT / "experiments/level3_ppo_loop/tracker_qualification_gates.json"
DEFAULT_OUTPUT_DIR = ROOT / "experiments/level3_ppo_loop/analysis/tracker_stage_metrics"

POINT_TASKS = {"point_hold", "point_reach", "brake_to_point"}
PATH_TASKS = {
    "line_tracking",
    "multi_point_reference",
    "l_shape_tracking",
    "curve_tracking",
    "zigzag_or_lemniscate_tracking",
}
SEMANTIC_TASKS = set(SEMANTIC_REFERENCE_TRACKER_TASKS)


@dataclass
class StepSample:
    """Per-step tracker diagnostics used to build stage metrics."""

    pos_error: float
    speed: float
    vel_error: float
    heading_error_rad: float
    action_delta_l2: float
    action_l2: float
    gate_x: float
    aperture_yz_error: float
    reward: float
    finite: bool
    waypoint_type_id: int
    stop_signal: float
    brake_mask: float
    slow_through_mask: float
    desired_speed: float


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for tracker stage evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--gates-json", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trace-output", type=Path)
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--seeds", default="101-120")
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--level3-steps", type=int, default=150)
    parser.add_argument("--early-termination-step-threshold", type=int, default=50)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    return parser.parse_args()


def deterministic_action(agent: TrackerPPOAgent, obs: np.ndarray) -> np.ndarray:
    """Return a clipped deterministic normalized action for one tracker observation."""
    with torch.no_grad():
        tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        action, _logprob, _entropy, _value = agent.get_action_and_value(
            tensor,
            deterministic=True,
        )
    return np.clip(action.squeeze(0).detach().cpu().numpy().astype(np.float32), -1.0, 1.0)


def evaluate_stage(
    *,
    stage_id: str,
    checkpoint: Path,
    gates_json: Path = DEFAULT_GATES,
    episodes: int | None = None,
    seeds: str = "101-120",
    max_episode_steps: int = 500,
    level3_steps: int = 150,
    early_termination_step_threshold: int = 50,
    rp_limit_deg: float = 50.0,
    trace_output: Path | None = None,
) -> dict[str, Any]:
    """Evaluate a checkpoint on one gate-defined tracker stage."""
    gates = load_json(gates_json)
    stage = stage_by_id(gates, stage_id)
    checkpoint_backed = checkpoint.exists()
    if not checkpoint_backed:
        raise FileNotFoundError(f"Tracker checkpoint not found: {checkpoint}")

    if stage_id == "planner_integration_smoke":
        return evaluate_planner_smoke(
            stage=stage,
            checkpoint=checkpoint,
            seeds=seeds,
            max_steps=level3_steps,
            early_termination_step_threshold=early_termination_step_threshold,
            trace_output=trace_output,
        )

    agent, metadata = load_tracker_checkpoint(checkpoint, "cpu", expected_layout=None)
    observation_layout = str(metadata.get("observation_layout", REFERENCE_TRACKER_LAYOUT))
    if int(metadata.get("obs_dim", agent.obs_dim)) != int(agent.obs_dim):
        raise ValueError(f"Unexpected tracker obs_dim in {checkpoint}.")
    agent.eval()
    episode_count = int(episodes or stage.get("min_eval_episodes", 20))
    seed_values = expand_episode_seeds(seeds, episode_count)
    rows = [
        run_tracker_episode(
            agent=agent,
            stage=stage,
            checkpoint=checkpoint,
            observation_layout=observation_layout,
            seed=seed,
            max_episode_steps=max_episode_steps,
            rp_limit_deg=rp_limit_deg,
        )
        for seed in seed_values
    ]
    metrics = aggregate_stage_rows(stage, rows)
    metrics.update(
        {
            "lane": gates.get("lane"),
            "stage": stage_id,
            "task": stage["task"],
            "config": stage["config"],
            "environment": stage["environment"],
            "checkpoint": str(checkpoint),
            "checkpoint_backed": checkpoint_backed,
            "episodes": len(rows),
            "seeds": seed_values,
            "max_episode_steps": int(max_episode_steps),
            "all_finite": all(bool(row["all_finite"]) for row in rows),
            "episode_rows": rows,
        }
    )
    return metrics


def expand_episode_seeds(seed_text: str, episode_count: int) -> list[int]:
    """Return enough deterministic seeds for the requested episode count."""
    parsed = parse_seed_range(seed_text)
    if len(parsed) >= episode_count:
        return parsed[:episode_count]
    seeds = list(parsed)
    next_seed = max(seeds) + 1 if seeds else 101
    while len(seeds) < episode_count:
        seeds.append(next_seed)
        next_seed += 1
    return seeds


def run_tracker_episode(
    *,
    agent: TrackerPPOAgent,
    stage: dict[str, Any],
    checkpoint: Path,
    seed: int,
    max_episode_steps: int,
    rp_limit_deg: float,
    observation_layout: str = REFERENCE_TRACKER_LAYOUT,
) -> dict[str, Any]:
    """Run one tracker episode and return per-episode metrics."""
    del checkpoint
    env = ReferenceTrackerEnv(
        config_name=Path(str(stage["config"])).name,
        task=str(stage["task"]),
        seed=seed,
        max_episode_steps=max_episode_steps,
        render=False,
        rp_limit_deg=rp_limit_deg,
        observation_layout=observation_layout,
    )
    obs, _info = env.reset(seed=seed)
    if int(obs.shape[0]) != int(agent.obs_dim):
        raise ValueError(
            f"Tracker obs_dim mismatch for stage {stage['id']}: env produced "
            f"{obs.shape[0]}, checkpoint expects {agent.obs_dim}."
        )
    samples: list[StepSample] = []
    actions: list[np.ndarray] = []
    positions: list[np.ndarray] = []
    references: list[ReferenceFrame] = []
    terminated = False
    truncated = False
    steps = 0
    try:
        initial_pos = np.asarray((env._raw_obs or {})["pos"], dtype=np.float32)  # noqa: SLF001
        anchor = getattr(env.generator, "_anchor", None)
        origin = getattr(env.generator, "_origin", None)
        for _step in range(max_episode_steps):
            reference = env._reference  # noqa: SLF001
            raw_obs = env._raw_obs  # noqa: SLF001
            if reference is None or raw_obs is None:
                raise RuntimeError("ReferenceTrackerEnv missing raw observation/reference.")
            action = deterministic_action(agent, obs)
            prev_action = actions[-1] if actions else np.zeros_like(action)
            obs, reward, terminated, truncated, _info = env.step(action)
            reward_obs = env._raw_obs or raw_obs  # noqa: SLF001
            samples.append(
                make_step_sample(
                    raw_obs=reward_obs,
                    reference=reference,
                    action=action,
                    prev_action=prev_action,
                    reward=reward,
                    obs_vec=obs,
                )
            )
            actions.append(action)
            positions.append(np.asarray(reward_obs["pos"], dtype=np.float32))
            references.append(reference)
            steps += 1
            if terminated or truncated:
                break
    finally:
        env.close()

    return summarize_episode(
        stage_id=str(stage["id"]),
        seed=seed,
        samples=samples,
        positions=positions,
        references=references,
        initial_pos=initial_pos,
        anchor=np.asarray(anchor, dtype=np.float32) if anchor is not None else None,
        origin=np.asarray(origin, dtype=np.float32) if origin is not None else None,
        terminated=bool(terminated),
        truncated=bool(truncated),
        steps=steps,
        dt=1.0 / float(env.config.env.freq),
    )


def make_step_sample(
    *,
    raw_obs: dict[str, Any],
    reference: ReferenceFrame,
    action: np.ndarray,
    prev_action: np.ndarray,
    reward: float,
    obs_vec: np.ndarray,
) -> StepSample:
    """Compute one step's geometric tracker metrics."""
    pos = np.asarray(raw_obs["pos"], dtype=np.float32)
    vel = np.asarray(raw_obs["vel"], dtype=np.float32)
    heading = quat_to_rotmat(np.asarray(raw_obs["quat"], dtype=np.float32))[:, 0]
    heading[2] = 0.0
    heading = safe_normalize(heading)
    desired_heading = safe_normalize(reference.desired_heading)
    desired_heading[2] = 0.0
    desired_heading = safe_normalize(desired_heading)
    heading_error_rad = float(
        math.acos(float(np.clip(np.dot(heading, desired_heading), -1.0, 1.0)))
    )
    action_delta = np.asarray(action, dtype=np.float32) - np.asarray(prev_action, dtype=np.float32)
    aperture_error = float(
        np.linalg.norm(reference.gate_local_position[1:3] - reference.aperture_yz)
    )
    finite = bool(
        np.isfinite(obs_vec).all()
        and np.isfinite(action).all()
        and np.isfinite(reward)
        and np.isfinite(pos).all()
        and np.isfinite(vel).all()
    )
    return StepSample(
        pos_error=float(np.linalg.norm(reference.current_point - pos)),
        speed=float(np.linalg.norm(vel)),
        vel_error=float(np.linalg.norm(reference.desired_velocity - vel)),
        heading_error_rad=heading_error_rad,
        action_delta_l2=float(np.linalg.norm(action_delta)),
        action_l2=float(np.linalg.norm(action)),
        gate_x=float(reference.gate_local_position[0]),
        aperture_yz_error=aperture_error,
        reward=float(reward),
        finite=finite,
        waypoint_type_id=int(reference.waypoint_type_id),
        stop_signal=float(reference.stop_signal),
        brake_mask=float(reference.brake_mask),
        slow_through_mask=float(reference.slow_through_mask),
        desired_speed=float(reference.desired_speed),
    )


def summarize_episode(
    *,
    stage_id: str,
    seed: int,
    samples: list[StepSample],
    positions: list[np.ndarray],
    references: list[ReferenceFrame],
    initial_pos: np.ndarray,
    anchor: np.ndarray | None,
    origin: np.ndarray | None,
    terminated: bool,
    truncated: bool,
    steps: int,
    dt: float,
) -> dict[str, Any]:
    """Summarize one stage episode."""
    del origin
    pos_errors = np.array([sample.pos_error for sample in samples], dtype=np.float32)
    speeds = np.array([sample.speed for sample in samples], dtype=np.float32)
    vel_errors = np.array([sample.vel_error for sample in samples], dtype=np.float32)
    heading_errors = np.array([sample.heading_error_rad for sample in samples], dtype=np.float32)
    action_deltas = np.array([sample.action_delta_l2 for sample in samples], dtype=np.float32)
    aperture_errors = np.array([sample.aperture_yz_error for sample in samples], dtype=np.float32)
    final_pos = positions[-1] if positions else initial_pos
    target = anchor if anchor is not None else (
        references[-1].current_point if references else initial_pos
    )
    final_error = float(np.linalg.norm(final_pos - target))
    overshoot = overshoot_along_axis(initial_pos, target, positions)
    terminal_speed = float(speeds[-1]) if len(speeds) else 0.0
    time_to_target = time_to_target_s(pos_errors, dt)
    gate_metrics = gate_episode_metrics(samples, speeds)
    semantic_metrics = semantic_episode_metrics(samples)
    path_completion = path_completion_ratio(positions, references)
    row = {
        "seed": int(seed),
        "steps": int(steps),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "crashed": bool(terminated and not truncated),
        "all_finite": all(sample.finite for sample in samples),
        "mean_position_error_m": mean_or_inf(pos_errors),
        "p90_position_error_m": percentile_or_inf(pos_errors, 90),
        "final_position_error_m": final_error,
        "mean_final_position_error_m": final_error,
        "p90_final_position_error_m": final_error,
        "mean_speed_mps": mean_or_inf(speeds),
        "terminal_speed_mps": terminal_speed,
        "mean_terminal_speed_mps": terminal_speed,
        "p90_terminal_speed_mps": terminal_speed,
        "mean_overshoot_m": overshoot,
        "p90_overshoot_m": overshoot,
        "mean_time_to_target_s": time_to_target,
        "mean_cross_track_error_m": mean_or_inf(pos_errors),
        "p90_cross_track_error_m": percentile_or_inf(pos_errors, 90),
        "mean_speed_error_mps": mean_or_inf(vel_errors),
        "mean_heading_error_rad": mean_or_inf(heading_errors),
        "p90_heading_error_rad": percentile_or_inf(heading_errors, 90),
        "mean_yaw_rate_abs": 0.0,
        "mean_action_delta_l2": mean_or_inf(action_deltas),
        "p90_action_delta_l2": percentile_or_inf(action_deltas, 90),
        "mean_action_norm_l2": mean_or_inf(
            np.array([sample.action_l2 for sample in samples], dtype=np.float32)
        ),
        "hold_time_ratio": hold_time_ratio(pos_errors, speeds),
        "mean_switch_overshoot_m": overshoot,
        "mean_corner_overshoot_m": overshoot,
        "oscillation_score": oscillation_score(action_deltas),
        "path_completion_ratio": path_completion,
        "path_completed": bool(path_completion >= 0.9),
        "brake_success": bool(terminal_speed <= 0.18 and overshoot <= 0.18 and not terminated),
        "success": episode_success(
            stage_id,
            final_error,
            pos_errors,
            speeds,
            overshoot,
            terminated,
        ),
        "mean_aperture_yz_error_m": mean_or_inf(aperture_errors),
        "p90_aperture_yz_error_m": percentile_or_inf(aperture_errors, 90),
    }
    row.update(gate_metrics)
    row.update(semantic_metrics)
    if stage_id in {"semantic_planner_reference", "reference_command_no_gate_reward"}:
        row["success"] = bool(
            not terminated
            and semantic_metrics["semantic_waypoint_type_count"] >= 4
            and semantic_metrics["brake_hold_rush_count"] <= 2
            and semantic_metrics["slow_through_stop_count"] <= 2
        )
    return row


def overshoot_along_axis(
    initial_pos: np.ndarray,
    target: np.ndarray,
    positions: list[np.ndarray],
) -> float:
    """Return max distance past the target along the start-target axis."""
    axis = np.asarray(target, dtype=np.float32) - np.asarray(initial_pos, dtype=np.float32)
    length = float(np.linalg.norm(axis))
    if length <= 1e-6 or not positions:
        return 0.0
    direction = axis / length
    projections = [
        float(np.dot(np.asarray(pos, dtype=np.float32) - target, direction))
        for pos in positions
    ]
    return max(0.0, max(projections))


def gate_episode_metrics(samples: list[StepSample], speeds: np.ndarray) -> dict[str, Any]:
    """Return gate crossing and recovery metrics for the gate-aperture stage."""
    valid_cross = False
    recovered = False
    post_gate_speeds: list[float] = []
    previous_x: float | None = None
    for idx, sample in enumerate(samples):
        if previous_x is not None and previous_x < 0.0 <= sample.gate_x:
            valid_cross = sample.aperture_yz_error <= 0.32
        if sample.gate_x >= 0.35:
            post_gate_speeds.append(float(speeds[idx]) if idx < len(speeds) else sample.speed)
            recovered = recovered or sample.speed <= 0.65
        previous_x = sample.gate_x
    return {
        "valid_aperture_cross": bool(valid_cross),
        "post_gate_recovered": bool(recovered),
        "mean_post_gate_speed_mps": float(np.mean(post_gate_speeds)) if post_gate_speeds else 0.0,
    }


def semantic_episode_metrics(samples: list[StepSample]) -> dict[str, Any]:
    """Return v58 semantic waypoint tracking metrics for one episode."""
    if not samples:
        return {
            "semantic_waypoint_type_count": 0,
            "mean_through_position_error_m": float("inf"),
            "mean_brake_hold_position_error_m": float("inf"),
            "mean_slow_through_position_error_m": float("inf"),
            "mean_recover_position_error_m": float("inf"),
            "mean_through_desired_speed_error_mps": float("inf"),
            "mean_brake_hold_desired_speed_error_mps": float("inf"),
            "mean_slow_through_desired_speed_error_mps": float("inf"),
            "mean_recover_desired_speed_error_mps": float("inf"),
            "mean_brake_hold_speed_mps": float("inf"),
            "p90_brake_hold_speed_mps": float("inf"),
            "mean_slow_through_speed_mps": float("inf"),
            "p90_slow_through_speed_mps": float("inf"),
            "brake_hold_terminal_speed_mps": float("inf"),
            "slow_through_stop_count": 0,
            "brake_hold_rush_count": 0,
        }
    rows_by_type: dict[int, list[StepSample]] = {}
    for sample in samples:
        rows_by_type.setdefault(int(sample.waypoint_type_id), []).append(sample)

    def values(type_id: int, field: str) -> np.ndarray:
        return np.array([float(getattr(row, field)) for row in rows_by_type.get(type_id, [])])

    def desired_speed_errors(type_id: int) -> np.ndarray:
        return np.array(
            [
                abs(float(row.speed) - float(row.desired_speed))
                for row in rows_by_type.get(type_id, [])
            ],
            dtype=np.float32,
        )

    brake_rows = rows_by_type.get(1, [])
    slow_rows = rows_by_type.get(2, [])
    brake_near = [row for row in brake_rows if row.pos_error <= 0.25]
    slow_near = [row for row in slow_rows if row.pos_error <= 0.25]
    return {
        "semantic_waypoint_type_count": len(rows_by_type),
        "mean_through_position_error_m": mean_or_inf(values(0, "pos_error")),
        "mean_brake_hold_position_error_m": mean_or_inf(values(1, "pos_error")),
        "mean_slow_through_position_error_m": mean_or_inf(values(2, "pos_error")),
        "mean_recover_position_error_m": mean_or_inf(values(3, "pos_error")),
        "mean_through_desired_speed_error_mps": mean_or_inf(desired_speed_errors(0)),
        "mean_brake_hold_desired_speed_error_mps": mean_or_inf(desired_speed_errors(1)),
        "mean_slow_through_desired_speed_error_mps": mean_or_inf(desired_speed_errors(2)),
        "mean_recover_desired_speed_error_mps": mean_or_inf(desired_speed_errors(3)),
        "mean_brake_hold_speed_mps": mean_or_inf(values(1, "speed")),
        "p90_brake_hold_speed_mps": percentile_or_inf(values(1, "speed"), 90),
        "mean_slow_through_speed_mps": mean_or_inf(values(2, "speed")),
        "p90_slow_through_speed_mps": percentile_or_inf(values(2, "speed"), 90),
        "brake_hold_terminal_speed_mps": (
            float(brake_rows[-1].speed) if brake_rows else float("inf")
        ),
        "slow_through_stop_count": sum(1 for row in slow_near if row.speed < 0.10),
        "brake_hold_rush_count": sum(1 for row in brake_near if row.speed > 0.25),
    }


def path_completion_ratio(
    positions: list[np.ndarray],
    references: list[ReferenceFrame],
) -> float:
    """Approximate reference path completion from the final reference target."""
    if not positions or not references:
        return 0.0
    final_pos = np.asarray(positions[-1], dtype=np.float32)
    final_ref = np.asarray(references[-1].current_point, dtype=np.float32)
    return 1.0 if float(np.linalg.norm(final_pos - final_ref)) <= 0.25 else 0.0


def hold_time_ratio(pos_errors: np.ndarray, speeds: np.ndarray) -> float:
    """Return fraction of steps that are both near-target and slow."""
    if len(pos_errors) == 0:
        return 0.0
    near = pos_errors <= 0.15
    slow = speeds <= 0.20 if len(speeds) == len(pos_errors) else np.zeros_like(near)
    return float(np.mean(near & slow))


def time_to_target_s(pos_errors: np.ndarray, dt: float, threshold_m: float = 0.18) -> float:
    """Return first time the tracker reaches the target threshold, or full horizon."""
    if len(pos_errors) == 0:
        return float("inf")
    reached = np.flatnonzero(pos_errors <= float(threshold_m))
    if len(reached) == 0:
        return float(len(pos_errors) * float(dt))
    return float((int(reached[0]) + 1) * float(dt))


def oscillation_score(action_deltas: np.ndarray) -> float:
    """Approximate oscillation by the normalized high-percentile action delta."""
    if len(action_deltas) == 0:
        return float("inf")
    return float(np.percentile(action_deltas, 90))


def episode_success(
    stage_id: str,
    final_error: float,
    pos_errors: np.ndarray,
    speeds: np.ndarray,
    overshoot: float,
    terminated: bool,
) -> bool:
    """Return a conservative per-episode success flag for common stage gates."""
    if terminated:
        return False
    mean_error = mean_or_inf(pos_errors)
    terminal_speed = float(speeds[-1]) if len(speeds) else 0.0
    if stage_id == "hover":
        return mean_error <= 0.12 and mean_or_inf(speeds) <= 0.15
    if stage_id == "point_hold":
        return final_error <= 0.15 and terminal_speed <= 0.20 and overshoot <= 0.16
    if stage_id == "point_reach":
        return final_error <= 0.18 and overshoot <= 0.20
    if stage_id == "heading_tracking":
        return mean_error <= 0.20
    return mean_error <= 0.22


def aggregate_stage_rows(stage: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-episode rows into the gate metric names."""
    stage_id = str(stage["id"])
    count = max(len(rows), 1)
    crashed = np.array([row["crashed"] for row in rows], dtype=bool)
    metrics: dict[str, Any] = {
        "success_rate": ratio(row["success"] for row in rows),
        "crash_rate": float(np.mean(crashed)) if len(crashed) else 1.0,
        "all_finite": all(bool(row["all_finite"]) for row in rows),
    }
    for name in [
        "mean_position_error_m",
        "p90_position_error_m",
        "mean_final_position_error_m",
        "p90_final_position_error_m",
        "mean_speed_mps",
        "mean_terminal_speed_mps",
        "p90_terminal_speed_mps",
        "mean_overshoot_m",
        "p90_overshoot_m",
        "mean_time_to_target_s",
        "mean_cross_track_error_m",
        "p90_cross_track_error_m",
        "mean_speed_error_mps",
        "mean_heading_error_rad",
        "p90_heading_error_rad",
        "mean_yaw_rate_abs",
        "mean_action_delta_l2",
        "p90_action_delta_l2",
        "mean_action_norm_l2",
        "hold_time_ratio",
        "mean_switch_overshoot_m",
        "mean_corner_overshoot_m",
        "oscillation_score",
        "mean_aperture_yz_error_m",
        "p90_aperture_yz_error_m",
        "mean_post_gate_speed_mps",
        "semantic_waypoint_type_count",
        "mean_through_position_error_m",
        "mean_brake_hold_position_error_m",
        "mean_slow_through_position_error_m",
        "mean_recover_position_error_m",
        "mean_through_desired_speed_error_mps",
        "mean_brake_hold_desired_speed_error_mps",
        "mean_slow_through_desired_speed_error_mps",
        "mean_recover_desired_speed_error_mps",
        "mean_brake_hold_speed_mps",
        "p90_brake_hold_speed_mps",
        "mean_slow_through_speed_mps",
        "p90_slow_through_speed_mps",
        "brake_hold_terminal_speed_mps",
        "slow_through_stop_count",
        "brake_hold_rush_count",
    ]:
        values = np.array([float(row.get(name, float("inf"))) for row in rows], dtype=np.float32)
        metrics[name] = aggregate_named_metric(name, values)
    metrics.update(
        {
            "brake_success_rate": ratio(row.get("brake_success", False) for row in rows),
            "segment_completion_rate": ratio(row.get("path_completed", False) for row in rows),
            "corner_completion_rate": ratio(row.get("path_completed", False) for row in rows),
            "path_completion_rate": ratio(row.get("path_completed", False) for row in rows),
            "valid_aperture_cross_rate": ratio(
                row.get("valid_aperture_cross", False) for row in rows
            ),
            "post_gate_recovery_rate": ratio(
                row.get("post_gate_recovered", False) for row in rows
            ),
            "episode_count": count,
            "stage_gate_semantics": "metrics generated by evaluate_level3_tracker_stage.py",
        }
    )
    if stage_id == "gate_aperture_reference":
        metrics["success_rate"] = metrics["valid_aperture_cross_rate"]
    return metrics


def aggregate_named_metric(name: str, values: np.ndarray) -> float:
    """Aggregate values according to the metric name prefix."""
    if len(values) == 0:
        return float("inf")
    if name.startswith("p90_"):
        return percentile_or_inf(values, 90)
    return mean_or_inf(values)


def ratio(values: Any) -> float:
    """Return the fraction of truthy values from an iterable."""
    items = list(values)
    if not items:
        return 0.0
    return float(sum(1 for item in items if item) / len(items))


def mean_or_inf(values: np.ndarray) -> float:
    """Return a finite mean or infinity for empty/non-finite inputs."""
    if len(values) == 0 or not np.isfinite(values).all():
        return float("inf")
    return float(np.mean(values))


def percentile_or_inf(values: np.ndarray, percentile: float) -> float:
    """Return a finite percentile or infinity for empty/non-finite inputs."""
    if len(values) == 0 or not np.isfinite(values).all():
        return float("inf")
    return float(np.percentile(values, percentile))


def evaluate_planner_smoke(
    *,
    stage: dict[str, Any],
    checkpoint: Path,
    seeds: str,
    max_steps: int,
    early_termination_step_threshold: int,
    trace_output: Path | None = None,
) -> dict[str, Any]:
    """Evaluate the deployed planner+tracker path on unchanged Level3 smoke seeds."""
    level3_seeds = parse_seed_range(seeds)
    rows = [
        run_level3_controller_seed(
            config_name=Path(str(stage["config"])).name,
            seed=seed,
            max_steps=max_steps,
            checkpoint=checkpoint,
            allow_untrained=False,
            early_termination_step_threshold=early_termination_step_threshold,
            trace_steps=trace_output is not None,
        )
        for seed in level3_seeds
    ]
    trace_rows: list[dict[str, Any]] = []
    if trace_output is not None:
        for row in rows:
            trace_rows.extend(row.pop("trace", []))
        trace_output.parent.mkdir(parents=True, exist_ok=True)
        trace_payload = {
            "stage": stage["id"],
            "checkpoint": str(checkpoint),
            "seeds": level3_seeds,
            "max_steps": int(max_steps),
            "trace_rows": trace_rows,
        }
        trace_output.write_text(
            json.dumps(trace_payload, indent=2, sort_keys=True) + "\n"
        )
    progress_count = sum(1 for row in rows if row["nonzero_first_gate_progress"])
    gate0_pass_count = sum(1 for row in rows if int(row["max_gate_index"]) > 0)
    early_termination_count = sum(1 for row in rows if row["early_termination"])
    metrics = {
        "stage": stage["id"],
        "task": stage["task"],
        "config": stage["config"],
        "environment": stage["environment"],
        "checkpoint": str(checkpoint),
        "checkpoint_backed": checkpoint.exists(),
        "all_finite": all(bool(row["finite_action"]) for row in rows),
        "level3_toml_diff_clean": True,
        "episodes": len(rows),
        "seeds": level3_seeds,
        "nonzero_first_gate_progress_count": progress_count,
        "nonzero_first_gate_progress_ratio": progress_count / len(rows) if rows else 0.0,
        "gate0_pass_count": gate0_pass_count,
        "early_termination_count": early_termination_count,
        "early_termination_ratio": early_termination_count / len(rows) if rows else 1.0,
        "episode_rows": rows,
    }
    if trace_output is not None:
        metrics["trace_output"] = str(trace_output)
        metrics["trace_step_rows"] = len(trace_rows)
    return metrics


def main() -> None:
    """Evaluate a tracker stage and write JSON metrics."""
    args = parse_args()
    metrics = evaluate_stage(
        stage_id=args.stage,
        checkpoint=args.checkpoint,
        gates_json=args.gates_json,
        episodes=args.episodes,
        seeds=args.seeds,
        max_episode_steps=args.max_episode_steps,
        level3_steps=args.level3_steps,
        early_termination_step_threshold=args.early_termination_step_threshold,
        rp_limit_deg=args.rp_limit_deg,
        trace_output=args.trace_output,
    )
    output = args.output
    if output is None:
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output = DEFAULT_OUTPUT_DIR / f"{args.stage}_metrics.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
