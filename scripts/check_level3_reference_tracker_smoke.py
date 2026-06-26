"""Smoke-check the v54 Level3 reference-tracker PPO support."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import torch
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_OBS_DIM,
    ReferenceTrackerEnv,
    TrackerPPOAgent,
    gate_local_axis_velocity_x,
    load_tracker_checkpoint,
    quat_to_rotmat,
)
from lsy_drone_racing.envs import race_core
from lsy_drone_racing.utils import load_config, load_controller

ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/level3_ppo_loop/analysis/"
    / "2026-06-25_v54_reference_tracker_smoke.json"
)
CONTROLLER_PATH = ROOT / "lsy_drone_racing/control/level3_reference_tracker_controller.py"
TERMINATION_REASON_NAMES = {
    race_core.TERMINATION_REASON_NONE: "none",
    race_core.TERMINATION_REASON_FINISH: "finish",
    race_core.TERMINATION_REASON_CONTACT: "contact",
    race_core.TERMINATION_REASON_BOUNDS: "bounds",
    race_core.TERMINATION_REASON_TIMEOUT: "timeout",
}


def parse_args() -> argparse.Namespace:
    """Parse smoke-check CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3.toml")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--allow-untrained", action="store_true")
    parser.add_argument("--task-steps", type=int, default=80)
    parser.add_argument("--level3-steps", type=int, default=150)
    parser.add_argument("--level3-seeds", default="101-105")
    parser.add_argument("--early-termination-step-threshold", type=int, default=50)
    parser.add_argument("--require-long-training-ready", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def parse_seed_range(text: str) -> list[int]:
    """Parse comma-separated seeds and inclusive ranges."""
    seeds: list[int] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start, end = token.split("-", 1)
            seeds.extend(range(int(start), int(end) + 1))
        else:
            seeds.append(int(token))
    if not seeds:
        raise ValueError("No Level3 seeds requested.")
    return seeds


def make_agent(checkpoint: Path | None, allow_untrained: bool) -> TrackerPPOAgent:
    """Load a tracker checkpoint or create an untrained finite-action policy."""
    if checkpoint is not None and checkpoint.exists():
        agent, _metadata = load_tracker_checkpoint(checkpoint, "cpu")
        agent.eval()
        return agent
    if allow_untrained:
        agent = TrackerPPOAgent(obs_dim=REFERENCE_TRACKER_OBS_DIM, action_dim=4)
        agent.eval()
        return agent
    raise FileNotFoundError(
        "No v54 tracker checkpoint found. Pass --checkpoint or use --allow-untrained "
        "for finite-action smoke only."
    )


def deterministic_action(agent: TrackerPPOAgent, obs: np.ndarray) -> np.ndarray:
    """Return the deterministic normalized action for a tracker observation."""
    with torch.no_grad():
        tensor = torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0)
        action, _logprob, _entropy, _value = agent.get_action_and_value(
            tensor,
            deterministic=True,
        )
    action_np = action.squeeze(0).detach().cpu().numpy().astype(np.float32)
    return np.clip(action_np, -1.0, 1.0)


def run_tracker_task(
    *,
    agent: TrackerPPOAgent,
    config_name: str,
    task: str,
    seed: int,
    max_steps: int,
) -> dict[str, Any]:
    """Run one native tracker task and collect finite-value diagnostics."""
    env = ReferenceTrackerEnv(
        config_name=config_name,
        task=task,
        seed=seed,
        max_episode_steps=max_steps,
        render=False,
    )
    obs, _info = env.reset(seed=seed)
    finite_obs = bool(np.isfinite(obs).all())
    finite_action = True
    finite_reward = True
    total_reward = 0.0
    steps = 0
    final_target_gate = 0
    for _step in range(max_steps):
        action = deterministic_action(agent, obs)
        finite_action = finite_action and bool(np.isfinite(action).all())
        obs, reward, terminated, truncated, _info = env.step(action)
        finite_obs = finite_obs and bool(np.isfinite(obs).all())
        finite_reward = finite_reward and bool(np.isfinite(reward))
        total_reward += float(reward)
        steps += 1
        raw_obs = env._raw_obs or {}  # noqa: SLF001 - smoke diagnostics only
        if "target_gate" in raw_obs:
            final_target_gate = int(np.asarray(raw_obs["target_gate"]).item())
        if terminated or truncated:
            break
    diagnostics = dict(env.last_diagnostics)
    env.close()
    return {
        "task": task,
        "seed": seed,
        "steps": steps,
        "finite_observation": finite_obs,
        "finite_action": finite_action,
        "finite_reward": finite_reward,
        "total_reward": total_reward,
        "target_gate_after": final_target_gate,
        "last_diagnostics": diagnostics,
    }


def run_level3_controller_seed(
    *,
    config_name: str,
    seed: int,
    max_steps: int,
    checkpoint: Path | None,
    allow_untrained: bool,
    early_termination_step_threshold: int,
    trace_steps: bool = False,
) -> dict[str, Any]:
    """Run the deployed controller path on one unchanged Level3 seed."""
    previous_checkpoint_env = os.environ.get("V54_REFERENCE_TRACKER_CHECKPOINT")
    previous_allow_env = os.environ.get("V54_REFERENCE_TRACKER_ALLOW_UNTRAINED")
    env = None
    try:
        if checkpoint is not None:
            os.environ["V54_REFERENCE_TRACKER_CHECKPOINT"] = str(checkpoint.resolve())
        elif allow_untrained:
            os.environ["V54_REFERENCE_TRACKER_ALLOW_UNTRAINED"] = "1"

        config = load_config(ROOT / "config" / config_name)
        config.sim.render = False
        config.env.seed = int(seed)
        env = gym.make(
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
        obs, info = env.reset(seed=seed)
        controller_cls = load_controller(CONTROLLER_PATH)
        controller = controller_cls(obs, info, config)

        finite_action = True
        initial_local_x = first_gate_local_x(obs)
        max_local_x = initial_local_x
        max_gate_index = 0
        final_target_gate = 0
        diagnostics: dict[str, float] = {}
        terminated = False
        truncated = False
        controller_finished = False
        steps = 0
        trace: list[dict[str, Any]] = []
        for _step in range(max_steps):
            pre_target_gate = int(np.asarray(obs["target_gate"]).item())
            action = controller.compute_control(obs, info)
            finite_action = finite_action and bool(np.isfinite(action).all())
            diagnostics = dict(controller.mppi_diagnostics())
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            target_gate = int(np.asarray(obs["target_gate"]).item())
            final_target_gate = target_gate
            max_gate_index = max(
                max_gate_index,
                target_gate if target_gate >= 0 else len(obs["gates_pos"]),
            )
            current_local_x = first_gate_local_x(obs)
            if np.isfinite(current_local_x):
                max_local_x = max(max_local_x, current_local_x)
            controller_finished = controller.step_callback(
                action,
                obs,
                reward,
                bool(terminated),
                bool(truncated),
                info,
            )
            if trace_steps:
                trace.append(
                    make_level3_trace_row(
                        seed=seed,
                        step=steps,
                        pre_target_gate=pre_target_gate,
                        post_target_gate=target_gate,
                        max_gate_index=max_gate_index,
                        obs=obs,
                        info=info,
                        action=action,
                        diagnostics=diagnostics,
                        terminated=bool(terminated),
                        truncated=bool(truncated),
                        controller_finished=bool(controller_finished),
                    )
                )
            if terminated or truncated or controller_finished:
                break
    finally:
        if env is not None:
            env.close()
        if previous_checkpoint_env is None:
            os.environ.pop("V54_REFERENCE_TRACKER_CHECKPOINT", None)
        else:
            os.environ["V54_REFERENCE_TRACKER_CHECKPOINT"] = previous_checkpoint_env
        if previous_allow_env is None:
            os.environ.pop("V54_REFERENCE_TRACKER_ALLOW_UNTRAINED", None)
        else:
            os.environ["V54_REFERENCE_TRACKER_ALLOW_UNTRAINED"] = previous_allow_env

    first_gate_axis_gain = float(max_local_x - initial_local_x)
    ended_before_max_steps = bool(terminated or truncated or controller_finished)
    early_termination = bool(
        ended_before_max_steps
        and steps < min(max_steps, int(early_termination_step_threshold))
    )
    termination_reason = level3_termination_reason(
        info=info,
        terminated=bool(terminated),
        truncated=bool(truncated),
        controller_finished=bool(controller_finished),
        ended_by_max_steps=not ended_before_max_steps,
    )
    result = {
        "seed": seed,
        "steps": steps,
        "finite_action": finite_action,
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "controller_finished": bool(controller_finished),
        "termination_reason": termination_reason,
        "termination_reason_code": level3_termination_reason_code(info),
        "ended_before_max_steps": ended_before_max_steps,
        "early_termination": early_termination,
        "early_termination_step_threshold": int(early_termination_step_threshold),
        "final_target_gate": int(final_target_gate),
        "max_gate_index": int(max_gate_index),
        "initial_first_gate_local_x": float(initial_local_x),
        "max_first_gate_local_x": float(max_local_x),
        "first_gate_axis_gain": first_gate_axis_gain,
        "nonzero_first_gate_progress": bool(
            first_gate_axis_gain > 0.05 or max_gate_index > 0
        ),
        "last_diagnostics": diagnostics,
    }
    if trace_steps:
        result["trace"] = trace
    return result


def make_level3_trace_row(
    *,
    seed: int,
    step: int,
    pre_target_gate: int,
    post_target_gate: int,
    max_gate_index: int,
    obs: dict[str, Any],
    info: dict[str, Any],
    action: np.ndarray,
    diagnostics: dict[str, float],
    terminated: bool,
    truncated: bool,
    controller_finished: bool,
) -> dict[str, Any]:
    """Build one compact per-step planner+tracker trace row."""
    pos = np.asarray(obs["pos"], dtype=np.float32)
    gate_local = target_gate_local_xyz(obs, post_target_gate)
    first_local = target_gate_local_xyz(obs, 0)
    aperture_y = float(diagnostics.get("v54_tracker_aperture_y", 0.0))
    aperture_z = float(diagnostics.get("v54_tracker_aperture_z", 0.0))
    aperture_yz_error = float(
        np.hypot(float(gate_local[1]) - aperture_y, float(gate_local[2]) - aperture_z)
    )
    return {
        "seed": int(seed),
        "step": int(step),
        "pre_target_gate": int(pre_target_gate),
        "post_target_gate": int(post_target_gate),
        "max_gate_index": int(max_gate_index),
        "pos_x": float(pos[0]),
        "pos_y": float(pos[1]),
        "pos_z": float(pos[2]),
        "gate_local_x": float(gate_local[0]),
        "gate_local_y": float(gate_local[1]),
        "gate_local_z": float(gate_local[2]),
        "gate_local_vx": float(
            diagnostics.get("v54_tracker_gate_local_vx", gate_local_axis_velocity_x(obs))
        ),
        "aperture_y": aperture_y,
        "aperture_z": aperture_z,
        "aperture_yz_error": aperture_yz_error,
        "first_gate_local_x": float(first_local[0]),
        "first_gate_local_y": float(first_local[1]),
        "first_gate_local_z": float(first_local[2]),
        "reference_x": float(diagnostics.get("v54_tracker_reference_x", float("nan"))),
        "reference_y": float(diagnostics.get("v54_tracker_reference_y", float("nan"))),
        "reference_z": float(diagnostics.get("v54_tracker_reference_z", float("nan"))),
        "phase_id": int(diagnostics.get("v54_tracker_phase_id", -1.0)),
        "desired_speed": float(
            diagnostics.get("v54_tracker_desired_speed", float("nan"))
        ),
        "action_roll": float(action[0]),
        "action_pitch": float(action[1]),
        "action_yaw": float(action[2]),
        "action_thrust": float(action[3]),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
        "controller_finished": bool(controller_finished),
        "termination_reason_code": level3_termination_reason_code(info),
        "termination_reason": level3_termination_reason(
            info=info,
            terminated=terminated,
            truncated=truncated,
            controller_finished=controller_finished,
            ended_by_max_steps=False,
        ),
    }


def level3_termination_reason(
    *,
    info: dict[str, Any],
    terminated: bool,
    truncated: bool,
    controller_finished: bool,
    ended_by_max_steps: bool,
) -> str:
    """Return a stable termination label for trace and episode summaries."""
    code = level3_termination_reason_code(info)
    if code in TERMINATION_REASON_NAMES and code != race_core.TERMINATION_REASON_NONE:
        return TERMINATION_REASON_NAMES[code]
    if controller_finished:
        return "controller_finished"
    if terminated:
        return "terminated"
    if truncated:
        return "truncated"
    if ended_by_max_steps:
        return "max_steps"
    return "running"


def level3_termination_reason_code(info: dict[str, Any]) -> int:
    """Extract the race-core termination reason code if present."""
    if isinstance(info, dict) and "termination_reason" in info:
        value = np.asarray(info["termination_reason"])
        if value.size:
            return int(value.reshape(-1)[0])
    return int(race_core.TERMINATION_REASON_NONE)


def first_gate_local_x(obs: dict[str, Any]) -> float:
    """Return drone x-position in the first gate frame."""
    return float(target_gate_local_xyz(obs, 0)[0])


def target_gate_local_xyz(obs: dict[str, Any], gate_index: int) -> np.ndarray:
    """Return the drone position in a requested gate frame."""
    gates_pos = np.asarray(obs["gates_pos"], dtype=np.float32)
    gates_quat = np.asarray(obs["gates_quat"], dtype=np.float32)
    if len(gates_pos) == 0:
        return np.full(3, np.nan, dtype=np.float32)
    gate = int(np.clip(gate_index, 0, len(gates_pos) - 1))
    pos = np.asarray(obs["pos"], dtype=np.float32)
    gate_rot = quat_to_rotmat(gates_quat[gate])
    return (gate_rot.T @ (pos - gates_pos[gate])).astype(np.float32)


def main() -> None:
    """Run all v54 smoke checks and write a JSON report."""
    args = parse_args()
    agent = make_agent(args.checkpoint, args.allow_untrained)
    level3_seeds = parse_seed_range(args.level3_seeds)
    task_results = [
        run_tracker_task(
            agent=agent,
            config_name=args.config,
            task=task,
            seed=seed,
            max_steps=args.task_steps,
        )
        for task, seed in (("hover", 1), ("point", 2), ("gate_aperture", 3))
    ]
    level3_results = [
        run_level3_controller_seed(
            config_name=args.config,
            seed=seed,
            max_steps=args.level3_steps,
            checkpoint=args.checkpoint,
            allow_untrained=args.allow_untrained,
            early_termination_step_threshold=args.early_termination_step_threshold,
        )
        for seed in level3_seeds
    ]
    task_all_finite = all(
        row["finite_observation"] and row["finite_action"] and row["finite_reward"]
        for row in task_results
    )
    level3_all_finite_actions = all(row["finite_action"] for row in level3_results)
    all_finite = all(
        row["finite_observation"] and row["finite_action"] and row["finite_reward"]
        for row in task_results
    ) and all(row["finite_action"] for row in level3_results)
    checkpoint_backed = args.checkpoint is not None and args.checkpoint.exists()
    progress_count = sum(
        1 for row in level3_results if row["nonzero_first_gate_progress"]
    )
    majority_required = len(level3_results) // 2 + 1
    progress_majority = progress_count >= majority_required
    gate0_pass_count = sum(1 for row in level3_results if int(row["max_gate_index"]) > 0)
    any_gate0_passed = gate0_pass_count > 0
    early_termination_count = sum(1 for row in level3_results if row["early_termination"])
    ended_before_max_steps_count = sum(
        1 for row in level3_results if row["ended_before_max_steps"]
    )
    step_values = [int(row["steps"]) for row in level3_results]
    readiness_failures: list[str] = []
    if not all_finite:
        readiness_failures.append("non_finite_task_or_level3_values")
    if not checkpoint_backed:
        readiness_failures.append("missing_checkpoint_backing")
    if not progress_majority:
        readiness_failures.append(
            "nonzero_first_gate_progress_not_majority"
        )
    if not any_gate0_passed:
        readiness_failures.append("no_seed_passed_gate_0")
    long_training_gate = bool(
        all_finite
        and checkpoint_backed
        and progress_majority
        and any_gate0_passed
    )
    output = {
        "config": args.config,
        "checkpoint": str(args.checkpoint) if args.checkpoint else None,
        "allow_untrained": bool(args.allow_untrained),
        "task_steps": int(args.task_steps),
        "level3_steps": int(args.level3_steps),
        "level3_seeds": level3_seeds,
        "all_finite": all_finite,
        "task_all_finite": task_all_finite,
        "level3_all_finite_actions": level3_all_finite_actions,
        "any_nonzero_first_gate_progress": progress_count > 0,
        "nonzero_first_gate_progress_count": progress_count,
        "nonzero_first_gate_progress_ratio": (
            progress_count / len(level3_results) if level3_results else 0.0
        ),
        "nonzero_first_gate_progress_majority": progress_majority,
        "nonzero_first_gate_progress_majority_required": majority_required,
        "gate0_pass_count": gate0_pass_count,
        "any_gate0_passed": any_gate0_passed,
        "early_termination_step_threshold": int(args.early_termination_step_threshold),
        "early_termination_count": early_termination_count,
        "early_termination_ratio": (
            early_termination_count / len(level3_results) if level3_results else 0.0
        ),
        "ended_before_max_steps_count": ended_before_max_steps_count,
        "min_level3_steps": min(step_values) if step_values else 0,
        "mean_level3_steps": float(np.mean(step_values)) if step_values else 0.0,
        "checkpoint_backed": checkpoint_backed,
        "long_training_gate_passed": long_training_gate,
        "promotion_ready_for_long_training": long_training_gate,
        "readiness_failures": readiness_failures,
        "tasks": task_results,
        "level3": level3_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
    if not all_finite:
        raise SystemExit(1)
    if args.require_long_training_ready and not long_training_gate:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
