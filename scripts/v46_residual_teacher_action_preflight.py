"""Preflight residual-GRU teacher action extraction for the Level3 v46 lane."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import numpy as np
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    POLICY_ARCH_MLP,
    POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
    checkpoint_hidden_dim,
    checkpoint_policy_arch,
    unpack_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Agent,
    Args,
    load_v27_retention_dataset,
    v27_distribution_retention_metrics,
)
from scripts.build_v27_retention_dataset import (
    DEFAULT_EXCLUDED_SEEDS,
    controller_from_checkpoint,
    gate_diagnostics,
    make_env,
    parse_seed_ranges,
    repo_path,
    repo_rel,
    reset_controller,
    teacher_distribution_and_action,
    write_dataset,
)

ROOT = Path(__file__).parents[1]


def _hidden_max_abs_diff(left: Any, right: Any) -> float:
    """Return max absolute hidden-state difference for parity diagnostics."""
    if left is None and right is None:
        return 0.0
    if left is None or right is None:
        return float("inf")
    return float(torch.max(torch.abs(left.detach().cpu() - right.detach().cpu())).item())


def _residual_delta(controller: Any, obs_vec: np.ndarray, action_mean: np.ndarray) -> float:
    """Return max absolute residual contribution to the action mean."""
    if controller.policy_arch != POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256:
        return 0.0
    obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32, device=controller.device).unsqueeze(
        0
    )
    with torch.no_grad():
        base_action = controller.agent.actor_mean(obs_tensor).squeeze(0).detach().cpu().numpy()
    return float(np.max(np.abs(action_mean - base_action)))


def _student_retention_metrics(
    dataset_path: Path,
    student_checkpoint: Path,
    batch_size: int,
) -> dict[str, float | int]:
    """Return deterministic student-vs-residual-teacher retention diagnostics."""
    device = torch.device("cpu")
    checkpoint = torch.load(student_checkpoint, map_location=device)
    state_dict, _observation_layout = unpack_checkpoint(checkpoint)
    student_policy_arch = checkpoint_policy_arch(checkpoint, state_dict)
    if student_policy_arch != POLICY_ARCH_MLP:
        raise RuntimeError(
            "v46 preflight student retention diagnostics expect an MLP student, "
            f"got {student_policy_arch!r}."
        )

    obs_dim = int(state_dict["actor_mean.0.weight"].shape[1])
    action_dim = int(state_dict["actor_mean.4.weight"].shape[0])
    agent = Agent(
        (obs_dim,),
        (action_dim,),
        hidden_dim=checkpoint_hidden_dim(checkpoint, state_dict),
    ).to(device)
    agent.load_state_dict(state_dict)
    agent.eval()

    retention_args = Args.create(
        policy_arch=POLICY_ARCH_MLP,
        v27_teacher_kl_beta=0.03,
        v27_retention_dataset_path=str(dataset_path),
        v27_retention_batch_size=batch_size,
    )
    dataset = load_v27_retention_dataset(
        retention_args,
        (obs_dim,),
        (action_dim,),
        device,
    )
    if dataset is None:
        raise RuntimeError("v46 preflight failed to load the generated retention dataset")

    with torch.no_grad():
        student_mean = agent.actor_mean(dataset.student_obs)
        student_logstd = agent.actor_logstd.expand_as(student_mean)
        teacher_kl, teacher_action_mse, teacher_agreement = (
            v27_distribution_retention_metrics(
                student_mean,
                student_logstd,
                dataset.teacher_action_mean,
                dataset.teacher_action_logstd,
            )
        )
    metrics = {
        "student_teacher_kl": float(teacher_kl.item()),
        "student_teacher_action_mse": float(teacher_action_mse.item()),
        "student_teacher_agreement": float(teacher_agreement.item()),
        "student_retention_sample_size": int(dataset.num_samples),
        "student_retention_batch_size": int(batch_size),
    }
    nonfinite = [
        key
        for key, value in metrics.items()
        if isinstance(value, float) and not np.isfinite(value)
    ]
    if nonfinite:
        raise RuntimeError(f"non-finite student retention metrics: {nonfinite}")
    return metrics


def run_preflight(args: argparse.Namespace) -> dict[str, Any]:
    """Run parity checks and collect a small residual-frontier retention dataset."""
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
    parity_diffs: list[float] = []
    hidden_diffs: list[float] = []
    residual_deltas: list[float] = []
    checked_steps = 0
    max_checked_action_diff = 0.0
    max_hidden_diff = 0.0
    max_residual_delta = 0.0

    extract_teacher = None
    direct_teacher = None
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
            if extract_teacher is None:
                extract_teacher = controller_from_checkpoint(
                    inference_module,
                    teacher_checkpoint,
                    obs,
                    info,
                    config,
                )
                direct_teacher = controller_from_checkpoint(
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
                if (
                    extract_teacher.policy_arch
                    != POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
                ):
                    raise RuntimeError(
                        "v46 preflight expects a residual-GRU teacher, got "
                        f"{extract_teacher.policy_arch!r}"
                    )
            else:
                reset_controller(extract_teacher, obs)
                reset_controller(direct_teacher, obs)
                reset_controller(student_observer, obs)

            episode: list[dict[str, Any]] = []
            steps = 0
            finished = False
            while True:
                target_gate = int(np.asarray(obs["target_gate"]).item())
                student_obs = student_observer._obs_rl(obs)  # noqa: SLF001
                gate_axis, gate_lateral_error, obstacle_min_dist = gate_diagnostics(
                    obs,
                    extract_teacher,
                )
                teacher_obs, teacher_mean, teacher_logstd, extracted_action = (
                    teacher_distribution_and_action(extract_teacher, obs)
                )
                direct_action = direct_teacher.compute_control(obs, info)
                action_diff = float(
                    np.max(np.abs(extracted_action.astype(np.float32) - direct_action))
                )
                hidden_diff = _hidden_max_abs_diff(
                    extract_teacher._recurrent_hidden_state,  # noqa: SLF001
                    direct_teacher._recurrent_hidden_state,  # noqa: SLF001
                )
                residual_delta = _residual_delta(extract_teacher, teacher_obs, teacher_mean)
                parity_diffs.append(action_diff)
                hidden_diffs.append(hidden_diff)
                residual_deltas.append(residual_delta)
                checked_steps += 1
                max_checked_action_diff = max(max_checked_action_diff, action_diff)
                max_hidden_diff = max(max_hidden_diff, hidden_diff)
                max_residual_delta = max(max_residual_delta, residual_delta)

                student_observer._last_action_norm = (  # noqa: SLF001
                    extract_teacher._last_action_norm.copy()  # noqa: SLF001
                )
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
                obs, _reward, terminated, truncated, info = env.step(extracted_action)
                steps += 1
                finished = int(np.asarray(obs["target_gate"]).item()) < 0
                extract_finished = extract_teacher.step_callback(
                    extracted_action,
                    obs,
                    _reward,
                    terminated,
                    truncated,
                    info,
                )
                direct_finished = direct_teacher.step_callback(
                    direct_action,
                    obs,
                    _reward,
                    terminated,
                    truncated,
                    info,
                )
                if extract_finished != direct_finished:
                    raise RuntimeError(
                        f"controller finished parity mismatch at seed={seed} step={steps}"
                    )
                if action_diff > args.action_atol:
                    raise RuntimeError(
                        f"action parity failed at seed={seed} step={steps}: "
                        f"diff={action_diff:.9g} > {args.action_atol}"
                    )
                if hidden_diff > args.hidden_atol:
                    raise RuntimeError(
                        f"hidden parity failed at seed={seed} step={steps}: "
                        f"diff={hidden_diff:.9g} > {args.hidden_atol}"
                    )
                if terminated or truncated or extract_finished:
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
            else:
                print(f"failure seed={seed} steps={steps} target_gate={target_gate}")
            seed += 1
    finally:
        env.close()

    if extract_teacher is None or student_observer is None:
        raise RuntimeError("no teacher/controller was constructed")
    if len(success_seeds) < args.min_successes:
        raise RuntimeError(
            f"only collected {len(success_seeds)} successful teacher episodes; "
            f"min_successes={args.min_successes}"
        )
    if not records["student_obs"]:
        raise RuntimeError("no retention samples collected")
    if max_residual_delta <= args.min_residual_delta:
        raise RuntimeError(
            f"residual branch contribution too small: {max_residual_delta:.9g} "
            f"<= {args.min_residual_delta}"
        )

    metadata = {
        "schema_version": 2,
        "purpose": "v46 residual frontier teacher action extraction preflight",
        "config": args.config,
        "teacher_checkpoint": repo_rel(teacher_checkpoint),
        "student_checkpoint": repo_rel(student_checkpoint),
        "teacher_observation_layout": getattr(extract_teacher, "observation_layout", None),
        "student_observation_layout": getattr(student_observer, "observation_layout", None),
        "teacher_policy_arch": getattr(extract_teacher, "policy_arch", None),
        "student_policy_arch": getattr(student_observer, "policy_arch", None),
        "excluded_seed_ranges": args.exclude_seed_ranges,
        "seed_start": args.seed_start,
        "max_seeds": args.max_seeds,
        "target_successes": args.target_successes,
        "min_successes": args.min_successes,
        "attempted_seeds": attempted_seeds,
        "success_seeds": success_seeds,
        "num_samples": len(records["student_obs"]),
        "checked_steps": checked_steps,
        "max_action_diff": max_checked_action_diff,
        "max_hidden_diff": max_hidden_diff,
        "max_residual_delta": max_residual_delta,
        "mean_residual_delta": float(np.mean(residual_deltas)),
        "p95_residual_delta": float(np.percentile(residual_deltas, 95)),
        "action_atol": args.action_atol,
        "hidden_atol": args.hidden_atol,
    }
    payload = {"records": records, "metadata": metadata}
    out_path = repo_path(args.out)
    write_dataset(out_path, payload)
    metadata["dataset_path"] = repo_rel(out_path)
    metadata.update(
        _student_retention_metrics(
            out_path,
            student_checkpoint,
            args.retention_batch_size,
        )
    )
    return metadata


def write_report(path: Path, metadata: dict[str, Any]) -> None:
    """Write a markdown parity packet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# V46 Residual Frontier Teacher Action Preflight",
        "",
        "Status: passed.",
        "",
        "## Scope",
        "",
        "- Final evaluation target remains unchanged `config/level3.toml`.",
        "- No Level3 track geometry, gate layout, obstacle layout, or randomization changes.",
        "- Teacher data is training-only; deployment remains PPO Actor only.",
        "",
        "## Checks",
        "",
        f"- teacher checkpoint: `{metadata['teacher_checkpoint']}`",
        f"- student checkpoint: `{metadata['student_checkpoint']}`",
        f"- teacher policy arch: `{metadata['teacher_policy_arch']}`",
        f"- student policy arch: `{metadata['student_policy_arch']}`",
        f"- checked steps: `{metadata['checked_steps']}`",
        f"- max extracted-vs-direct scaled action diff: `{metadata['max_action_diff']:.9g}`",
        f"- max extracted-vs-direct hidden-state diff: `{metadata['max_hidden_diff']:.9g}`",
        f"- max residual branch contribution: `{metadata['max_residual_delta']:.9g}`",
        f"- mean residual branch contribution: `{metadata['mean_residual_delta']:.9g}`",
        f"- p95 residual branch contribution: `{metadata['p95_residual_delta']:.9g}`",
        f"- success seeds: `{metadata['success_seeds']}`",
        f"- samples written: `{metadata['num_samples']}`",
        f"- student-vs-teacher KL on generated dataset: "
        f"`{metadata['student_teacher_kl']:.9g}`",
        f"- student-vs-teacher action MSE: "
        f"`{metadata['student_teacher_action_mse']:.9g}`",
        f"- student action agreement within 0.15: "
        f"`{metadata['student_teacher_agreement']:.9g}`",
        f"- dataset path: `{metadata['dataset_path']}`",
        "",
        "## Decision",
        "",
        "Residual-GRU teacher action extraction is parity-proven for loop107/v37 1M:",
        "the dataset path includes the residual branch and matches direct",
        "`ppo_level3_inference` action and hidden-state evolution on ordered",
        "trajectories.",
        "",
        "The generated `.npz` remains a local training artifact and must stay out of git.",
        "",
    ]
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="level3.toml")
    parser.add_argument("--teacher-checkpoint", required=True)
    parser.add_argument("--student-checkpoint", required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/level3_ppo_loop/retention_datasets/"
            "v46_loop107_residual_frontier_diagnostic_v5.npz"
        ),
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path(
            "experiments/level3_ppo_loop/parity/"
            "2026-06-23_v46_residual_frontier_teacher_action_preflight.md"
        ),
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path(
            "experiments/level3_ppo_loop/parity/"
            "2026-06-23_v46_residual_frontier_teacher_action_preflight.json"
        ),
    )
    parser.add_argument("--inference-module", default="ppo_level3_inference")
    parser.add_argument("--seed-start", type=int, default=4501)
    parser.add_argument("--max-seeds", type=int, default=80)
    parser.add_argument("--target-successes", type=int, default=2)
    parser.add_argument("--min-successes", type=int, default=1)
    parser.add_argument("--max-samples", type=int, default=20_000)
    parser.add_argument("--retention-batch-size", type=int, default=512)
    parser.add_argument("--exclude-seed-ranges", default=DEFAULT_EXCLUDED_SEEDS)
    parser.add_argument("--action-atol", type=float, default=1e-6)
    parser.add_argument("--hidden-atol", type=float, default=1e-6)
    parser.add_argument("--min-residual-delta", type=float, default=1e-5)
    return parser.parse_args()


def main() -> None:
    """Run preflight and write artifacts."""
    args = parse_args()
    metadata = run_preflight(args)
    report_json = repo_path(args.report_json)
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    write_report(repo_path(args.report_md), metadata)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
