"""Build a v27 teacher-success retention dataset for Level3 PPO.

The dataset stores student-layout observations from successful teacher rollouts
plus the frozen teacher policy's action distribution at the same states. It is
used by train_CleanRL_ppo_level3.py for KL(pi_teacher || pi_student).
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import gymnasium
import numpy as np
import torch
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.control.ppo_level3_observation import policy_arch_uses_recurrent_state
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]
DEFAULT_EXCLUDED_SEEDS = "1-20,101-200,1001-1200"


def parse_seed_token(token: str) -> list[int]:
    """Parse an integer seed or inclusive seed range."""
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
    """Return seeds from a comma-separated range string."""
    seeds: set[int] = set()
    for token in value.split(","):
        seeds.update(parse_seed_token(token))
    return seeds


def repo_path(path: str | Path) -> Path:
    """Resolve a repo-relative or absolute path."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def repo_rel(path: str | Path) -> str:
    """Render a path relative to the repo when possible."""
    value = repo_path(path).resolve()
    try:
        return str(value.relative_to(ROOT))
    except ValueError:
        return str(value)


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


def controller_from_checkpoint(
    inference_module: Any,
    checkpoint: Path,
    obs: dict[str, np.ndarray],
    info: dict[str, Any],
    config: Any,
):
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


def teacher_distribution_and_action(
    controller: Any,
    obs: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return teacher obs, mean, logstd, and scaled action for one state."""
    obs_vec = controller._obs_rl(obs)  # noqa: SLF001 - intentional data extraction path.
    obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32, device=controller.device).unsqueeze(
        0
    )
    with torch.no_grad():
        if policy_arch_uses_recurrent_state(controller.policy_arch):
            if controller._recurrent_hidden_state is None:  # noqa: SLF001
                controller._recurrent_hidden_state = controller.agent.get_initial_state(  # noqa: SLF001
                    1,
                    controller.device,
                )
            done = torch.zeros(1, dtype=torch.float32, device=controller.device)
            action_mean, _, _, _, controller._recurrent_hidden_state = (  # noqa: SLF001
                controller.agent.get_action_and_value(
                    obs_tensor,
                    controller._recurrent_hidden_state,  # noqa: SLF001
                    done,
                    deterministic=True,
                )
            )
        else:
            action_mean = controller.agent.actor_mean(obs_tensor)
        action_logstd = controller.agent.actor_logstd.expand_as(action_mean)

    action_mean_np = action_mean.squeeze(0).detach().cpu().numpy().astype(np.float32)
    action_logstd_np = action_logstd.squeeze(0).detach().cpu().numpy().astype(np.float32)
    filtered_action_norm = controller._filter_action(action_mean_np)  # noqa: SLF001
    controller._last_action_norm = filtered_action_norm  # noqa: SLF001
    return (
        obs_vec.astype(np.float32),
        action_mean_np,
        action_logstd_np,
        controller._scale_action(filtered_action_norm).astype(np.float32),  # noqa: SLF001
    )


def gate_diagnostics(obs: dict[str, np.ndarray], controller: Any) -> tuple[float, float, float]:
    """Return simple gate and obstacle clearance diagnostics for the state."""
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


def build_dataset(args: argparse.Namespace) -> dict[str, Any]:
    """Run teacher episodes and collect successful trajectories."""
    teacher_checkpoint = repo_path(args.teacher_checkpoint)
    student_checkpoint = repo_path(args.student_checkpoint)
    inference_module = importlib.import_module(f"lsy_drone_racing.control.{args.inference_module}")
    env, config = make_env(args.config)
    excluded_seeds = parse_seed_ranges(args.exclude_seed_ranges)

    records: dict[str, list[Any]] = {
        "student_obs": [],
        "teacher_action_mean": [],
        "teacher_action_logstd": [],
        "target_gate": [],
        "seed": [],
        "episode_step": [],
        "success_time_s": [],
        "gate_axis": [],
        "gate_lateral_error": [],
        "obstacle_min_dist": [],
    }
    attempted_seeds: list[int] = []
    success_seeds: list[int] = []
    teacher = None
    student_observer = None

    try:
        seed = int(args.seed_start)
        while (
            seed < args.seed_start + args.max_seeds
            and len(success_seeds) < args.target_successes
            and len(records["student_obs"]) < args.max_samples
        ):
            if seed in excluded_seeds:
                seed += 1
                continue
            attempted_seeds.append(seed)
            obs, info = env.reset(seed=seed)
            if teacher is None:
                teacher = controller_from_checkpoint(
                    inference_module,
                    teacher_checkpoint,
                    obs,
                    info,
                    config,
                )
                student_observer = controller_from_checkpoint(
                    inference_module,
                    student_checkpoint,
                    obs,
                    info,
                    config,
                )
            else:
                reset_controller(teacher, obs)
                reset_controller(student_observer, obs)

            episode: list[dict[str, Any]] = []
            steps = 0
            finished = False
            while True:
                target_gate = int(np.asarray(obs["target_gate"]).item())
                student_obs = student_observer._obs_rl(obs)  # noqa: SLF001
                gate_axis, gate_lateral_error, obstacle_min_dist = gate_diagnostics(obs, teacher)
                _, teacher_mean, teacher_logstd, action = teacher_distribution_and_action(
                    teacher,
                    obs,
                )
                student_observer._last_action_norm = teacher._last_action_norm.copy()  # noqa: SLF001
                episode.append(
                    {
                        "student_obs": student_obs.astype(np.float32),
                        "teacher_action_mean": teacher_mean.astype(np.float32),
                        "teacher_action_logstd": teacher_logstd.astype(np.float32),
                        "target_gate": target_gate,
                        "seed": seed,
                        "episode_step": steps,
                        "gate_axis": gate_axis,
                        "gate_lateral_error": gate_lateral_error,
                        "obstacle_min_dist": obstacle_min_dist,
                    }
                )
                obs, _reward, terminated, truncated, info = env.step(action)
                steps += 1
                finished = int(np.asarray(obs["target_gate"]).item()) < 0
                controller_finished = teacher.step_callback(
                    action,
                    obs,
                    _reward,
                    terminated,
                    truncated,
                    info,
                )
                if terminated or truncated or controller_finished:
                    break

            if finished:
                success_seeds.append(seed)
                success_time_s = steps / float(config.env.freq)
                for row in episode:
                    if len(records["student_obs"]) >= args.max_samples:
                        break
                    for key in (
                        "student_obs",
                        "teacher_action_mean",
                        "teacher_action_logstd",
                        "target_gate",
                        "seed",
                        "episode_step",
                        "gate_axis",
                        "gate_lateral_error",
                        "obstacle_min_dist",
                    ):
                        records[key].append(row[key])
                    records["success_time_s"].append(success_time_s)
                print(
                    f"success seed={seed} steps={steps} "
                    f"samples={len(records['student_obs'])}/{args.max_samples}"
                )
            seed += 1
    finally:
        env.close()

    if len(success_seeds) < args.min_successes:
        raise RuntimeError(
            f"only collected {len(success_seeds)} successful teacher episodes; "
            f"min_successes={args.min_successes}"
        )
    if not records["student_obs"]:
        raise RuntimeError("no retention samples collected")

    metadata = {
        "schema_version": 1,
        "config": args.config,
        "teacher_checkpoint": repo_rel(teacher_checkpoint),
        "student_checkpoint": repo_rel(student_checkpoint),
        "teacher_observation_layout": getattr(teacher, "observation_layout", None),
        "student_observation_layout": getattr(student_observer, "observation_layout", None),
        "teacher_policy_arch": getattr(teacher, "policy_arch", None),
        "student_policy_arch": getattr(student_observer, "policy_arch", None),
        "excluded_seed_ranges": args.exclude_seed_ranges,
        "seed_start": args.seed_start,
        "max_seeds": args.max_seeds,
        "target_successes": args.target_successes,
        "min_successes": args.min_successes,
        "attempted_seeds": attempted_seeds,
        "success_seeds": success_seeds,
        "num_samples": len(records["student_obs"]),
        "purpose": "v27 teacher-retention KL: KL(pi_teacher || pi_student)",
    }
    return {"records": records, "metadata": metadata}


def write_dataset(path: Path, payload: dict[str, Any]) -> None:
    """Write the compressed retention dataset."""
    records = payload["records"]
    metadata = payload["metadata"]
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        student_obs=np.stack(records["student_obs"]).astype(np.float32),
        teacher_action_mean=np.stack(records["teacher_action_mean"]).astype(np.float32),
        teacher_action_logstd=np.stack(records["teacher_action_logstd"]).astype(np.float32),
        target_gate=np.asarray(records["target_gate"], dtype=np.int16),
        seed=np.asarray(records["seed"], dtype=np.int32),
        episode_step=np.asarray(records["episode_step"], dtype=np.int32),
        success_time_s=np.asarray(records["success_time_s"], dtype=np.float32),
        gate_axis=np.asarray(records["gate_axis"], dtype=np.float32),
        gate_lateral_error=np.asarray(records["gate_lateral_error"], dtype=np.float32),
        obstacle_min_dist=np.asarray(records["obstacle_min_dist"], dtype=np.float32),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True), dtype=np.str_),
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument(
        "--teacher-checkpoint",
        required=True,
        help="Loop052 teacher checkpoint path.",
    )
    parser.add_argument(
        "--student-checkpoint",
        required=True,
        help="Student-layout checkpoint used only to build v8 observations.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/level3_ppo_loop/retention_datasets/"
            "v27_loop052_train_pool_success_v5_teacher_v8_student.npz"
        ),
    )
    parser.add_argument("--inference-module", default="ppo_level3_inference")
    parser.add_argument("--seed-start", type=int, default=2001)
    parser.add_argument("--max-seeds", type=int, default=240)
    parser.add_argument("--target-successes", type=int, default=8)
    parser.add_argument("--min-successes", type=int, default=2)
    parser.add_argument("--max-samples", type=int, default=20_000)
    parser.add_argument("--exclude-seed-ranges", default=DEFAULT_EXCLUDED_SEEDS)
    return parser.parse_args()


def main() -> None:
    """Build and write the dataset."""
    args = parse_args()
    payload = build_dataset(args)
    out_path = repo_path(args.out)
    write_dataset(out_path, payload)
    metadata = payload["metadata"]
    print(
        f"wrote {repo_rel(out_path)} with {metadata['num_samples']} samples "
        f"from {len(metadata['success_seeds'])} successes"
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
