"""Audit the v27 teacher-retention dataset and student checkpoints.

This is an offline data/implementation audit. It does not run Level3 hard eval
and must not inspect final_locked seeds. The goal is to verify that the
train-pool retention dataset is well-formed and to measure, per retained
teacher-success episode, how closely student checkpoints match the frozen
teacher action distribution stored in the dataset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from lsy_drone_racing.control.ppo_level3_inference import PPOAgent
from lsy_drone_racing.control.ppo_level3_observation import (
    POLICY_ARCH_MLP,
    checkpoint_hidden_dim,
    checkpoint_policy_arch,
    unpack_checkpoint,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = (
    "experiments/level3_ppo_loop/retention_datasets/"
    "v27_loop052_train_pool_success_v5_teacher_v8_student.npz"
)
DEFAULT_EXCLUDED_SEEDS = "1-20,101-200,1001-1200"
DEFAULT_OUT_PREFIX = (
    "experiments/level3_ppo_loop/analysis/"
    "v27_retention_dataset_audit"
)
REQUIRED_ARRAYS = (
    "student_obs",
    "teacher_action_mean",
    "teacher_action_logstd",
    "target_gate",
    "seed",
    "episode_step",
    "success_time_s",
    "gate_axis",
    "gate_lateral_error",
    "obstacle_min_dist",
    "metadata_json",
)


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def round_float(value: float | np.floating[Any], digits: int = 6) -> float:
    """Round finite floats for stable JSON/CSV output."""
    parsed = float(value)
    if not math.isfinite(parsed):
        return parsed
    return round(parsed, digits)


def load_dataset(path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Load a v27 retention dataset with strict array presence checks."""
    if not path.exists():
        raise FileNotFoundError(f"dataset not found: {path}")
    data = np.load(path, allow_pickle=False)
    missing = [key for key in REQUIRED_ARRAYS if key not in data.files]
    if missing:
        raise ValueError(f"dataset missing required arrays: {missing}")
    arrays = {key: np.asarray(data[key]) for key in REQUIRED_ARRAYS if key != "metadata_json"}
    metadata = json.loads(str(data["metadata_json"].item()))
    return arrays, metadata


def validate_dataset(
    arrays: dict[str, np.ndarray],
    metadata: dict[str, Any],
    *,
    expected_student_obs_dim: int | None,
    exclude_seed_ranges: str,
) -> dict[str, Any]:
    """Return validation diagnostics and raise on hard integrity failures."""
    student_obs = np.asarray(arrays["student_obs"], dtype=np.float32)
    teacher_mean = np.asarray(arrays["teacher_action_mean"], dtype=np.float32)
    teacher_logstd = np.asarray(arrays["teacher_action_logstd"], dtype=np.float32)
    seeds = np.asarray(arrays["seed"], dtype=np.int64)
    target_gate = np.asarray(arrays["target_gate"], dtype=np.int64)
    episode_step = np.asarray(arrays["episode_step"], dtype=np.int64)
    success_time_s = np.asarray(arrays["success_time_s"], dtype=np.float32)
    gate_axis = np.asarray(arrays["gate_axis"], dtype=np.float32)
    gate_lateral_error = np.asarray(arrays["gate_lateral_error"], dtype=np.float32)
    obstacle_min_dist = np.asarray(arrays["obstacle_min_dist"], dtype=np.float32)

    n = int(student_obs.shape[0])
    errors: list[str] = []
    warnings: list[str] = []
    if student_obs.ndim != 2:
        errors.append(f"student_obs must be 2-D, got {student_obs.shape}")
    if expected_student_obs_dim is not None and student_obs.shape[1] != expected_student_obs_dim:
        errors.append(
            f"student_obs dim mismatch: got {student_obs.shape[1]}, "
            f"expected {expected_student_obs_dim}"
        )
    if teacher_mean.shape != (n, 4):
        errors.append(f"teacher_action_mean must be ({n}, 4), got {teacher_mean.shape}")
    if teacher_logstd.shape != teacher_mean.shape:
        errors.append(
            "teacher_action_logstd shape mismatch: "
            f"got {teacher_logstd.shape}, expected {teacher_mean.shape}"
        )
    for key, array in (
        ("student_obs", student_obs),
        ("teacher_action_mean", teacher_mean),
        ("teacher_action_logstd", teacher_logstd),
        ("success_time_s", success_time_s),
        ("gate_axis", gate_axis),
        ("gate_lateral_error", gate_lateral_error),
        ("obstacle_min_dist", obstacle_min_dist),
    ):
        if not np.isfinite(array).all():
            errors.append(f"{key} contains non-finite values")
    for key, array in (
        ("target_gate", target_gate),
        ("seed", seeds),
        ("episode_step", episode_step),
        ("success_time_s", success_time_s),
        ("gate_axis", gate_axis),
        ("gate_lateral_error", gate_lateral_error),
        ("obstacle_min_dist", obstacle_min_dist),
    ):
        if array.shape[0] != n:
            errors.append(f"{key} length mismatch: got {array.shape[0]}, expected {n}")

    excluded = parse_seed_ranges(exclude_seed_ranges)
    unique_seeds = sorted(int(seed) for seed in np.unique(seeds))
    overlap = sorted(set(unique_seeds) & excluded)
    if overlap:
        errors.append(f"dataset includes excluded seeds: {overlap[:20]}")

    meta_num_samples = metadata.get("num_samples")
    if meta_num_samples is not None and int(meta_num_samples) != n:
        errors.append(f"metadata num_samples={meta_num_samples} but arrays have {n}")
    meta_success_seeds = sorted(int(seed) for seed in metadata.get("success_seeds", []))
    if meta_success_seeds and meta_success_seeds != unique_seeds:
        errors.append(
            "metadata success_seeds do not match dataset seeds: "
            f"metadata={meta_success_seeds}, data={unique_seeds}"
        )
    if len(unique_seeds) < 8:
        warnings.append(
            f"retention dataset has only {len(unique_seeds)} successful episodes"
        )

    seed_counts = Counter(int(seed) for seed in seeds.tolist())
    gate_counts = Counter(int(gate) for gate in target_gate.tolist())
    summary = {
        "status": "failed" if errors else "passed",
        "errors": errors,
        "warnings": warnings,
        "num_samples": n,
        "student_obs_dim": int(student_obs.shape[1]) if student_obs.ndim == 2 else None,
        "num_success_episodes": len(unique_seeds),
        "unique_seeds": unique_seeds,
        "excluded_seed_ranges": exclude_seed_ranges,
        "excluded_seed_overlap": overlap,
        "samples_by_seed": {str(seed): int(count) for seed, count in sorted(seed_counts.items())},
        "samples_by_target_gate": {
            str(gate): int(count) for gate, count in sorted(gate_counts.items())
        },
        "success_time_s_min": round_float(float(np.min(success_time_s))),
        "success_time_s_max": round_float(float(np.max(success_time_s))),
        "success_time_s_mean": round_float(float(np.mean(success_time_s))),
        "gate_axis_mean": round_float(float(np.mean(gate_axis))),
        "gate_lateral_error_mean": round_float(float(np.mean(gate_lateral_error))),
        "obstacle_min_dist_mean": round_float(float(np.mean(obstacle_min_dist))),
        "metadata": metadata,
    }
    if errors:
        raise ValueError("v27 retention dataset validation failed: " + "; ".join(errors))
    return summary


def load_mlp_agent(checkpoint_path: Path, obs_dim: int) -> tuple[PPOAgent, dict[str, Any]]:
    """Load a feed-forward PPO checkpoint for offline action-mean comparison."""
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model_state_dict, observation_layout = unpack_checkpoint(checkpoint)
    policy_arch = checkpoint_policy_arch(checkpoint, model_state_dict)
    if policy_arch != POLICY_ARCH_MLP:
        raise NotImplementedError(
            f"offline v27 retention audit currently supports MLP checkpoints only, got {policy_arch}"
        )
    hidden_dim = checkpoint_hidden_dim(checkpoint, model_state_dict)
    model_obs_dim = int(model_state_dict["actor_mean.0.weight"].shape[1])
    if model_obs_dim != obs_dim:
        raise ValueError(
            f"checkpoint {checkpoint_path} obs_dim={model_obs_dim}, dataset obs_dim={obs_dim}"
        )
    agent = PPOAgent((obs_dim,), (4,), hidden_dim=hidden_dim)
    agent.load_state_dict(model_state_dict)
    agent.eval()
    metadata = {
        "checkpoint_file": repo_rel(checkpoint_path),
        "observation_layout": observation_layout,
        "policy_arch": policy_arch,
        "hidden_dim": hidden_dim,
    }
    return agent, metadata


def retention_metrics_for_checkpoint(
    label: str,
    checkpoint_path: Path,
    arrays: dict[str, np.ndarray],
    *,
    agreement_threshold: float,
    batch_size: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Compute overall and per-episode teacher-retention metrics."""
    student_obs = np.asarray(arrays["student_obs"], dtype=np.float32)
    teacher_mean = np.asarray(arrays["teacher_action_mean"], dtype=np.float32)
    teacher_logstd = np.asarray(arrays["teacher_action_logstd"], dtype=np.float32)
    seeds = np.asarray(arrays["seed"], dtype=np.int64)
    success_time_s = np.asarray(arrays["success_time_s"], dtype=np.float32)
    target_gate = np.asarray(arrays["target_gate"], dtype=np.int64)

    agent, metadata = load_mlp_agent(checkpoint_path, int(student_obs.shape[1]))
    predicted_batches: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, student_obs.shape[0], batch_size):
            obs_batch = torch.as_tensor(student_obs[start : start + batch_size], dtype=torch.float32)
            predicted_batches.append(agent.actor_mean(obs_batch).cpu().numpy().astype(np.float32))
    student_mean = np.concatenate(predicted_batches, axis=0)
    student_logstd = agent.actor_logstd.detach().cpu().numpy().astype(np.float32)
    student_logstd = np.broadcast_to(student_logstd, student_mean.shape)

    teacher_var = np.exp(2.0 * teacher_logstd)
    student_var = np.exp(2.0 * student_logstd)
    kl_per_action = (
        student_logstd
        - teacher_logstd
        + (teacher_var + np.square(teacher_mean - student_mean)) / (2.0 * student_var)
        - 0.5
    )
    kl_per_sample = np.sum(kl_per_action, axis=1)
    action_mse_per_sample = np.mean(np.square(student_mean - teacher_mean), axis=1)
    agreement_per_sample = np.mean(np.abs(student_mean - teacher_mean) <= agreement_threshold, axis=1)

    episode_rows: list[dict[str, Any]] = []
    for seed in sorted(int(seed) for seed in np.unique(seeds)):
        mask = seeds == seed
        episode_rows.append(
            {
                "checkpoint": label,
                "checkpoint_file": repo_rel(checkpoint_path),
                "seed": seed,
                "samples": int(np.sum(mask)),
                "teacher_kl": round_float(float(np.mean(kl_per_sample[mask]))),
                "teacher_action_mse": round_float(float(np.mean(action_mse_per_sample[mask]))),
                "teacher_agreement": round_float(float(np.mean(agreement_per_sample[mask]))),
                "success_time_s": round_float(float(np.mean(success_time_s[mask]))),
                "target_gates": json.dumps(
                    {str(gate): int(count) for gate, count in sorted(Counter(target_gate[mask]).items())},
                    sort_keys=True,
                ),
            }
        )

    summary = {
        "checkpoint": label,
        **metadata,
        "samples": int(student_obs.shape[0]),
        "episodes": len(episode_rows),
        "teacher_kl": round_float(float(np.mean(kl_per_sample))),
        "teacher_action_mse": round_float(float(np.mean(action_mse_per_sample))),
        "teacher_agreement": round_float(float(np.mean(agreement_per_sample))),
        "episode_teacher_agreement_mean": round_float(
            float(np.mean([row["teacher_agreement"] for row in episode_rows]))
        ),
        "episode_teacher_agreement_min": round_float(
            float(np.min([row["teacher_agreement"] for row in episode_rows]))
        ),
        "episodes_ge_0_80_agreement": int(
            sum(float(row["teacher_agreement"]) >= 0.80 for row in episode_rows)
        ),
        "agreement_threshold": agreement_threshold,
    }
    return summary, episode_rows


def parse_checkpoint_arg(value: str) -> tuple[str, Path]:
    """Parse LABEL=PATH or PATH checkpoint argument."""
    if "=" in value:
        label, path_text = value.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError(f"empty checkpoint label in {value!r}")
        return label, repo_path(path_text)
    path = repo_path(value)
    return path.stem, path


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write dictionaries to CSV if rows are present."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def render_markdown(payload: dict[str, Any]) -> str:
    """Render a concise audit report."""
    dataset = payload["dataset"]
    summaries = payload["checkpoint_summaries"]
    lines = [
        "# V27 Retention Dataset Audit",
        "",
        f"- Created at: {payload['created_at']}",
        f"- Dataset: `{payload['dataset_path']}`",
        f"- Validation status: `{dataset['status']}`",
        f"- Samples: {dataset['num_samples']}",
        f"- Successful train-pool episodes: {dataset['num_success_episodes']}",
        f"- Excluded seed overlap: {dataset['excluded_seed_overlap']}",
        f"- Student obs dim: {dataset['student_obs_dim']}",
        f"- Samples by target gate: `{dataset['samples_by_target_gate']}`",
        "",
        "## Checkpoint Retention",
        "",
    ]
    if summaries:
        lines.extend(
            [
                "| Checkpoint | Agreement | Episode min | Episodes >=0.80 | KL | Action MSE |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in summaries:
            lines.append(
                "| "
                f"{row['checkpoint']} | {row['teacher_agreement']} | "
                f"{row['episode_teacher_agreement_min']} | "
                f"{row['episodes_ge_0_80_agreement']}/{row['episodes']} | "
                f"{row['teacher_kl']} | {row['teacher_action_mse']} |"
            )
    else:
        lines.append("- No checkpoints were audited.")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This is an offline teacher-success retention audit, not Level3 hard eval.",
            "- It does not inspect `final_locked` seeds.",
            "- Hard acceptance still requires unchanged `config/level3.toml` evaluator metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--exclude-seed-ranges", default=DEFAULT_EXCLUDED_SEEDS)
    parser.add_argument("--expected-student-obs-dim", type=int, default=82)
    parser.add_argument("--agreement-threshold", type=float, default=0.15)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument(
        "--checkpoint",
        action="append",
        default=[],
        help="Checkpoint to audit, as LABEL=PATH or PATH. May be repeated.",
    )
    parser.add_argument("--out-prefix", default=DEFAULT_OUT_PREFIX)
    return parser.parse_args()


def main() -> None:
    """Run the audit and write JSON/CSV/Markdown artifacts."""
    args = parse_args()
    dataset_path = repo_path(args.dataset)
    out_prefix = repo_path(args.out_prefix)
    arrays, metadata = load_dataset(dataset_path)
    dataset_summary = validate_dataset(
        arrays,
        metadata,
        expected_student_obs_dim=args.expected_student_obs_dim,
        exclude_seed_ranges=args.exclude_seed_ranges,
    )

    checkpoint_summaries: list[dict[str, Any]] = []
    episode_rows: list[dict[str, Any]] = []
    for checkpoint_arg in args.checkpoint:
        label, checkpoint_path = parse_checkpoint_arg(checkpoint_arg)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"checkpoint not found: {checkpoint_path}")
        summary, rows = retention_metrics_for_checkpoint(
            label,
            checkpoint_path,
            arrays,
            agreement_threshold=args.agreement_threshold,
            batch_size=max(1, int(args.batch_size)),
        )
        checkpoint_summaries.append(summary)
        episode_rows.extend(rows)

    payload = {
        "schema_version": 1,
        "created_at": utc_now(),
        "dataset_path": repo_rel(dataset_path),
        "dataset": dataset_summary,
        "checkpoint_summaries": checkpoint_summaries,
        "episode_csv": repo_rel(out_prefix.with_name(out_prefix.name + "_episodes.csv")),
        "summary_csv": repo_rel(out_prefix.with_name(out_prefix.name + "_summary.csv")),
    }

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_prefix.with_suffix(".json")
    md_path = out_prefix.with_suffix(".md")
    summary_csv = out_prefix.with_name(out_prefix.name + "_summary.csv")
    episode_csv = out_prefix.with_name(out_prefix.name + "_episodes.csv")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    write_csv(summary_csv, checkpoint_summaries)
    write_csv(episode_csv, episode_rows)

    print(f"wrote {repo_rel(json_path)}")
    print(f"wrote {repo_rel(md_path)}")
    if checkpoint_summaries:
        print(f"wrote {repo_rel(summary_csv)}")
        print(f"wrote {repo_rel(episode_csv)}")
    print(render_markdown(payload))


if __name__ == "__main__":
    main()
