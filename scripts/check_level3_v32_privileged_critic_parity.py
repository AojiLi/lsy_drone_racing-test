"""Build and validate the Level3 v32 privileged-Critic zero-update checkpoint."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
    POLICY_ARCH_MLP,
    checkpoint_action_lowpass_alpha,
    checkpoint_action_rp_limit_deg,
    checkpoint_hidden_dim,
    checkpoint_obs_normalization,
    checkpoint_policy_arch,
    checkpoint_recurrent_hidden_dim,
    checkpoint_return_normalization,
    make_checkpoint,
    unpack_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Agent,
    expand_checkpoint_critic_input_dim,
)
from scripts.evaluate_level2_selected_ppo import (
    load_seed_file,
    run_checkpoint,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_CHECKPOINT = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/"
    "level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/"
    "level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt"
)
DEFAULT_TARGET_CHECKPOINT = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/level3_v32_parity/"
    "level3_loop_097_12m_v32_privileged_critic_zero_update.ckpt"
)
DEFAULT_SEED_FILE = ROOT / "experiments/level3_ppo_loop/seed_manifests/validation_unseen_101_200.txt"
DEFAULT_OUT_PREFIX = ROOT / "experiments/level3_ppo_loop/parity/v32_privileged_critic_loop097_12m"
COMPARE_ROW_FIELDS = (
    "success",
    "crashed",
    "timeout",
    "termination_reason",
    "steps",
    "target_gate",
    "target_gate_after",
    "gates",
)
SUMMARY_FIELDS = (
    "success_count",
    "success_rate",
    "crash_rate",
    "timeout_rate",
    "mean_gates",
    "mean_time_s_success",
    "success_seeds",
    "termination_reasons",
)


def repo_path(path: Path) -> str:
    """Return a stable repo-relative path when possible."""
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def infer_actor_action_dims(model_state_dict: dict[str, torch.Tensor]) -> tuple[int, int]:
    """Return deployed Actor observation and action widths."""
    actor_obs_dim = int(model_state_dict["actor_mean.0.weight"].shape[1])
    action_dim = int(model_state_dict["actor_mean.4.weight"].shape[0])
    return actor_obs_dim, action_dim


def build_privileged_critic_checkpoint(
    source_checkpoint: Path,
    target_checkpoint: Path,
    *,
    critic_observation_dim: int,
) -> dict[str, Any]:
    """Write a zero-update checkpoint whose Critic input is widened only by padding."""
    checkpoint = torch.load(source_checkpoint, map_location="cpu")
    model_state_dict, observation_layout = unpack_checkpoint(checkpoint)
    policy_arch = checkpoint_policy_arch(checkpoint, model_state_dict)
    if policy_arch != POLICY_ARCH_MLP:
        raise ValueError(f"v32 privileged Critic parity supports only MLP, got {policy_arch}.")

    actor_observation_dim, action_dim = infer_actor_action_dims(model_state_dict)
    hidden_dim = checkpoint_hidden_dim(checkpoint, model_state_dict)
    target_agent = Agent(
        (actor_observation_dim,),
        (action_dim,),
        hidden_dim=hidden_dim,
        critic_obs_shape=(critic_observation_dim,),
    )
    expanded_state = expand_checkpoint_critic_input_dim(model_state_dict, target_agent)

    target_agent.load_state_dict(expanded_state)
    obs = torch.randn((32, actor_observation_dim), generator=torch.Generator().manual_seed(32))
    critic_obs = torch.randn(
        (32, critic_observation_dim),
        generator=torch.Generator().manual_seed(33),
    )
    source_agent = Agent((actor_observation_dim,), (action_dim,), hidden_dim=hidden_dim)
    source_agent.load_state_dict(model_state_dict)
    with torch.no_grad():
        source_action, source_logprob, source_entropy, _ = source_agent.get_action_and_value(
            obs,
            deterministic=True,
        )
        target_action, target_logprob, target_entropy, _ = target_agent.get_action_and_value(
            obs,
            deterministic=True,
            critic_x=critic_obs,
        )
    torch.testing.assert_close(target_action, source_action)
    torch.testing.assert_close(target_logprob, source_logprob)
    torch.testing.assert_close(target_entropy, source_entropy)

    wrapped = make_checkpoint(
        expanded_state,
        hidden_dim=hidden_dim,
        observation_layout=observation_layout,
        action_rp_limit_deg=checkpoint_action_rp_limit_deg(checkpoint),
        action_lowpass_alpha=checkpoint_action_lowpass_alpha(checkpoint),
        policy_arch=policy_arch,
        recurrent_hidden_dim=checkpoint_recurrent_hidden_dim(checkpoint, model_state_dict),
        obs_normalization=checkpoint_obs_normalization(checkpoint),
        return_normalization=checkpoint_return_normalization(checkpoint),
        critic_observation_mode=CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
        actor_observation_dim=actor_observation_dim,
        critic_observation_dim=critic_observation_dim,
    )
    target_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(wrapped, target_checkpoint)
    return {
        "actor_observation_dim": actor_observation_dim,
        "critic_observation_dim": critic_observation_dim,
        "action_dim": action_dim,
        "hidden_dim": hidden_dim,
        "observation_layout": observation_layout,
        "target_checkpoint": repo_path(target_checkpoint),
    }


def rows_match(source_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    """Compare per-seed evaluator outcomes for deterministic parity."""
    errors: list[str] = []
    source_by_seed = {int(row["seed"]): row for row in source_rows}
    target_by_seed = {int(row["seed"]): row for row in target_rows}
    if set(source_by_seed) != set(target_by_seed):
        errors.append("source and v32 seed sets differ")
        return False, errors
    for seed in sorted(source_by_seed):
        source_row = source_by_seed[seed]
        target_row = target_by_seed[seed]
        for field in COMPARE_ROW_FIELDS:
            if source_row.get(field) != target_row.get(field):
                errors.append(
                    f"seed {seed} field {field}: "
                    f"{source_row.get(field)!r} != {target_row.get(field)!r}"
                )
    return not errors, errors


def write_summary_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    """Write evaluator summary rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(key for row in summaries for key in row))
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)


def write_report(
    path: Path,
    *,
    metadata: dict[str, Any],
    source_summary: dict[str, Any] | None,
    v32_summary: dict[str, Any] | None,
    parity_passed: bool,
    parity_errors: list[str],
) -> None:
    """Write the tracked parity report."""
    lines = [
        "# v32 Privileged Critic Zero-Update Parity",
        "",
        f"Status: `{'passed' if parity_passed else 'failed'}`",
        "",
        "## Scope",
        "",
        "- Source checkpoint: "
        f"`{repo_path(Path(metadata['source_checkpoint']))}`.",
        "- v32 checkpoint: "
        f"`{metadata['target_checkpoint']}`.",
        "- Actor observation is unchanged; only the Critic input layer is widened.",
        "- Final evaluator config remains `config/level3.toml`.",
        "",
        "## Metadata",
        "",
        "```json",
        json.dumps(metadata, indent=2, sort_keys=True),
        "```",
    ]
    if source_summary and v32_summary:
        lines.extend(
            [
                "",
                "## Validation Summary",
                "",
                "| Metric | source | v32 zero-update |",
                "| --- | ---: | ---: |",
            ]
        )
        for field in SUMMARY_FIELDS:
            lines.append(
                f"| `{field}` | `{source_summary.get(field)}` | `{v32_summary.get(field)}` |"
            )
    if parity_errors:
        lines.extend(["", "## Parity Errors", ""])
        lines.extend(f"- {error}" for error in parity_errors[:50])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-checkpoint", type=Path, default=DEFAULT_SOURCE_CHECKPOINT)
    parser.add_argument("--target-checkpoint", type=Path, default=DEFAULT_TARGET_CHECKPOINT)
    parser.add_argument("--critic-observation-dim", type=int, default=135)
    parser.add_argument("--config", default="level3.toml")
    parser.add_argument("--seed-file", type=Path, default=DEFAULT_SEED_FILE)
    parser.add_argument("--seed-split-name", default="validation_unseen")
    parser.add_argument("--out-prefix", type=Path, default=DEFAULT_OUT_PREFIX)
    parser.add_argument("--skip-eval", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Build the v32 zero-update checkpoint and optionally run hard-eval parity."""
    args = parse_args()
    source_checkpoint = args.source_checkpoint
    if not source_checkpoint.is_absolute():
        source_checkpoint = ROOT / source_checkpoint
    target_checkpoint = args.target_checkpoint
    if not target_checkpoint.is_absolute():
        target_checkpoint = ROOT / target_checkpoint
    out_prefix = args.out_prefix
    if not out_prefix.is_absolute():
        out_prefix = ROOT / out_prefix

    metadata = build_privileged_critic_checkpoint(
        source_checkpoint,
        target_checkpoint,
        critic_observation_dim=args.critic_observation_dim,
    )
    metadata["source_checkpoint"] = str(source_checkpoint.resolve())

    source_summary = None
    v32_summary = None
    parity_passed = True
    parity_errors: list[str] = []
    if not args.skip_eval:
        seeds = load_seed_file(args.seed_file)
        source_rows, source_summary = run_checkpoint(
            source_checkpoint,
            config_name=args.config,
            seeds=seeds,
            seed_split_name=args.seed_split_name,
            smooth_coef_rpy=0.15,
            smooth_coef_thrust=0.15,
            tilt_limit_deg=40.0,
            inference_module_name="ppo_level3_inference",
            confidence_interval="wilson",
            failure_taxonomy=True,
        )
        v32_rows, v32_summary = run_checkpoint(
            target_checkpoint,
            config_name=args.config,
            seeds=seeds,
            seed_split_name=args.seed_split_name,
            smooth_coef_rpy=0.15,
            smooth_coef_thrust=0.15,
            tilt_limit_deg=40.0,
            inference_module_name="ppo_level3_inference",
            confidence_interval="wilson",
            failure_taxonomy=True,
        )
        parity_passed, parity_errors = rows_match(source_rows, v32_rows)
        write_csv(out_prefix.with_name(out_prefix.name + "_source_episodes.csv"), source_rows)
        write_csv(out_prefix.with_name(out_prefix.name + "_v32_episodes.csv"), v32_rows)
        write_summary_csv(
            out_prefix.with_name(out_prefix.name + "_summary.csv"),
            [source_summary, v32_summary],
        )

    report_path = out_prefix.with_suffix(".md")
    write_report(
        report_path,
        metadata=metadata,
        source_summary=source_summary,
        v32_summary=v32_summary,
        parity_passed=parity_passed,
        parity_errors=parity_errors,
    )
    print(f"wrote parity report: {repo_path(report_path)}")
    if not parity_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
