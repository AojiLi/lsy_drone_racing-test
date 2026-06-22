"""Build a post-run analysis packet for a Level3 PPO loop trial."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOOP_DIR = ROOT / "experiments" / "level3_ppo_loop"
DEFAULT_STATE_PATH = LOOP_DIR / "state.json"
DEFAULT_ANALYSIS_DIR = LOOP_DIR / "analysis"
DEFAULT_WANDB_PROJECT = "ADR-PPO-Racing-Level3"
TARGET_SUCCESS_RATE = 0.60
TARGET_TIME_S = 7.0
DECISION_DIR = LOOP_DIR / "decisions"

POST_RUN_REVIEW_ROLES = [
    {
        "role": "evaluator_metrics",
        "suffix": "eval",
        "task": (
            "Audit checkpoint evidence from the hard evaluator. Focus on success "
            "rate, mean successful time, crashes, timeouts, gates, tilt, and "
            "whether any checkpoint is promising enough to mature."
        ),
    },
    {
        "role": "wandb_ppo_diagnostics",
        "suffix": "wandb_ppo",
        "task": (
        "Audit W&B curves. Focus on train reward, reward components, race "
            "metrics, teacher-retention KL/agreement when present, value scale, "
            "value loss, KL, clip fraction, entropy, explained variance, SPS, "
            "and whether training signals convert into evaluator progress."
        ),
    },
    {
        "role": "structure_research_synthesis",
        "suffix": "structure_research",
        "task": (
            "Audit whether the failure is likely reward numbers, observation, "
            "controller wiring, reward structure, or training structure. Any "
            "framework change must be a named structural lane, source-backed "
            "when nontrivial, and must keep the Level3 target track unchanged."
        ),
    },
]

POST_RUN_DECISION_OPTIONS = [
    "stop_target_met",
    "hold_for_more_analysis",
    "continue_same_hypothesis",
    "change_reward_or_training_numbers",
    "launch_named_structural_lane",
]

TUNABLE_REWARD_PARAM_KEYS = [
    "gate_stage_coef",
    "gate_axis_coef",
    "gate_bonus",
    "gate_front_bonus",
    "gate_back_bonus",
    "finish_bonus",
    "wrong_side_penalty",
    "crash_penalty",
    "obstacle_coef",
    "obstacle_margin",
    "timeout_penalty",
    "time_penalty",
    "act_coef",
    "d_act_th_coef",
    "d_act_xy_coef",
    "cmd_tilt_coef",
    "rpy_coef",
    "tilt_limit_deg",
    "tilt_excess_coef",
]

LOCKED_REWARD_CHANNELS = [
    "progress_coef",
    "near_gate_coef",
    "gate_plane_bonus",
    "missed_gate_penalty",
    "obstacle_clearance_coef",
]

CORE_WANDB_METRICS = [
    "train/total_reward",
    "train/reward",
    "losses/approx_kl",
    "losses/clipfrac",
    "losses/entropy",
    "losses/explained_variance",
    "losses/value_loss",
    "losses/policy_loss",
    "charts/SPS",
]

RETENTION_WANDB_METRICS = [
    "losses/teacher_kl",
    "losses/teacher_action_mse",
    "retention/teacher_agreement",
    "retention/sampled_batch_size",
]

RACE_WANDB_METRICS = [
    "race/passed_gate_rate",
    "race/finished_rate",
    "race/crashed_rate",
    "race/timeout_rate",
    "race/gate_stage",
    "race/gate_axis_x",
    "race/gate_centerline_dist",
    "race/gate_plane_dist",
    "race/gate_plane_cross_rate",
    "race/gate_plane_center_hit_rate",
    "race/missed_gate_rate",
    "race/gate_frame_pressure",
    "race/gate_front_hit_rate",
    "race/gate_pass_hit_rate",
    "race/gate_back_hit_rate",
    "race/wrong_side_gate_rate",
    "race/obstacle_distance",
    "race/obstacle_clearance_progress",
    "race/tilt_angle_deg",
    "race/cmd_tilt_deg",
]

REWARD_WANDB_METRICS = [
    "reward_components/gate_axis_progress",
    "reward_components/gate_stage_progress",
    "reward_components/gate_front",
    "reward_components/gate_plane",
    "reward_components/gate_back",
    "reward_components/gate_bonus",
    "reward_components/finish_bonus",
    "reward_components/missed_gate",
    "reward_components/gate_frame_pressure",
    "reward_components/wrong_side",
    "reward_components/crash",
    "reward_components/obstacle",
    "reward_components/obstacle_clearance",
    "reward_components/action",
    "reward_components/cmd_tilt",
    "reward_components/smooth",
    "reward_components/tilt",
    "reward_components/tilt_excess",
    "reward_components/timeout",
    "reward_components/time",
]

WANDB_METRICS = (
    CORE_WANDB_METRICS
    + RETENTION_WANDB_METRICS
    + RACE_WANDB_METRICS
    + REWARD_WANDB_METRICS
)


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Parse finite floats, returning default for empty or NaN values."""
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def clean_json_value(value: Any) -> Any:
    """Return a JSON-safe metric value."""
    parsed = safe_float(value)
    if parsed is not None:
        return parsed
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): clean_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json_value(item) for item in value]
    return str(value)


def relative_to_root(path: Path) -> str:
    """Render a path relative to the repository root when possible."""
    resolved = path.resolve()
    return str(resolved.relative_to(ROOT)) if resolved.is_relative_to(ROOT) else str(resolved)


def load_state(path: Path) -> dict[str, Any]:
    """Load loop state."""
    try:
        with path.open() as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        if path.read_text().strip():
            raise SystemExit(f"error: state file is not valid JSON: {path}") from exc
        return {
            "schema_version": 2,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "target": {
                "success_rate": TARGET_SUCCESS_RATE,
                "mean_time_s_success": TARGET_TIME_S,
            },
            "best": None,
            "best_dev": None,
            "best_validation": None,
            "final_candidate": None,
            "final_certified": None,
            "pending_post_run_decision": None,
            "trials": [],
        }


def write_state(path: Path, state: dict[str, Any]) -> None:
    """Persist loop state."""
    state["updated_at"] = utc_now()
    with path.open("w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")


def select_trial(state: dict[str, Any], trial_id: str | None) -> dict[str, Any] | None:
    """Select a trial by id, or the latest trial with useful evidence."""
    trials = state.get("trials", [])
    if trial_id:
        for trial in trials:
            if trial.get("trial_id") == trial_id:
                return trial
        raise SystemExit(f"error: trial {trial_id!r} not found in state.")

    for trial in reversed(trials):
        if trial.get("best_summary") or trial.get("summary_csv") or trial.get("wandb_run_id"):
            return trial
    return trials[-1] if trials else None


def read_csv_rows(path: Path | None) -> list[dict[str, Any]]:
    """Read a CSV as dictionaries with numeric values where possible."""
    if path is None or not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append({key: clean_json_value(value) for key, value in row.items()})
    return rows


def resolve_optional_path(raw_path: str | None) -> Path | None:
    """Resolve a path stored in state."""
    if not raw_path:
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else ROOT / path


def metric_stats(rows: list[dict[str, Any]], metric: str) -> dict[str, Any] | None:
    """Summarize one metric series."""
    points: list[tuple[float, float]] = []
    for index, row in enumerate(rows):
        value = safe_float(row.get(metric))
        if value is None:
            continue
        step = safe_float(row.get("global_step"), float(index)) or float(index)
        points.append((step, value))
    if not points:
        return None

    values = [value for _, value in points]
    tail_count = max(1, len(values) // 5)
    tail_values = values[-tail_count:]
    first_step, first_value = points[0]
    last_step, last_value = points[-1]
    step_delta = max(last_step - first_step, 1.0)
    delta = last_value - first_value
    slope_per_million_steps = delta / step_delta * 1_000_000.0
    abs_ref = max(abs(first_value), abs(last_value), 1.0)
    if abs(delta) < 0.03 * abs_ref:
        trend = "flat"
    else:
        trend = "up" if delta > 0 else "down"

    return {
        "count": len(values),
        "first": round(first_value, 6),
        "last": round(last_value, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "mean": round(sum(values) / len(values), 6),
        "tail_mean": round(sum(tail_values) / len(tail_values), 6),
        "delta": round(delta, 6),
        "slope_per_million_steps": round(slope_per_million_steps, 6),
        "trend": trend,
    }


def summarize_wandb_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Summarize selected W&B metric curves."""
    summaries: dict[str, dict[str, Any]] = {}
    for metric in WANDB_METRICS:
        summary = metric_stats(rows, metric)
        if summary is not None:
            summaries[metric] = summary
    return summaries


def fetch_wandb_rows(
    entity: str | None,
    project: str | None,
    run_id: str | None,
    samples: int,
    offline: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], str | None]:
    """Fetch sampled W&B history rows for a run."""
    if offline or not run_id:
        return {"available": False, "reason": "wandb disabled or run id missing"}, [], None
    if not entity:
        return {"available": False, "reason": "wandb entity missing"}, [], None
    project = project or DEFAULT_WANDB_PROJECT
    try:
        import wandb
    except ImportError:
        return {"available": False, "reason": "wandb package not importable"}, [], None

    try:
        api = wandb.Api()
        run = api.run(f"{entity}/{project}/{run_id}")
        history = run.history(samples=samples)
    except Exception as exc:  # noqa: BLE001 - analysis should degrade gracefully.
        return {"available": False, "reason": str(exc)}, [], None

    rows = [
        {str(key): clean_json_value(value) for key, value in row.items()}
        for row in history.to_dict(orient="records")
    ]
    summary = {
        "available": True,
        "entity": entity,
        "project": project,
        "run_id": run_id,
        "url": run.url,
        "state": run.state,
        "history_rows": len(rows),
        "sampled": True,
    }
    return summary, rows, run.url


def best_checkpoint_summary(
    trial: dict[str, Any], summary_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    """Return the best checkpoint summary for the trial."""
    best = trial.get("best_summary")
    if isinstance(best, dict):
        return best
    if not summary_rows:
        return {}
    return max(summary_rows, key=lambda row: safe_float(row.get("score"), -1e9) or -1e9)


def previous_best_summary(state: dict[str, Any], trial_id: str | None) -> dict[str, Any] | None:
    """Return the newest best summary before the selected trial."""
    for trial in reversed(state.get("trials", [])):
        if trial.get("trial_id") == trial_id:
            continue
        best = trial.get("best_summary")
        if isinstance(best, dict):
            return best
    best = state.get("best")
    return best if isinstance(best, dict) else None


def eval_delta(current: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    """Compare selected evaluator metrics against the previous evaluated trial."""
    if previous is None:
        return {}
    fields = ["success_rate", "mean_time_s_success", "crash_rate", "timeout_rate", "mean_gates"]
    deltas: dict[str, Any] = {}
    for field in fields:
        current_value = safe_float(current.get(field))
        previous_value = safe_float(previous.get(field))
        if current_value is not None and previous_value is not None:
            deltas[field] = round(current_value - previous_value, 6)
    return deltas


def recommend_next_move(
    best: dict[str, Any],
    wandb_metrics: dict[str, dict[str, Any]],
    previous_delta: dict[str, Any],
    target_success: float,
    target_time: float,
    *,
    wandb_available: bool,
    require_wandb: bool,
) -> dict[str, Any]:
    """Recommend a conservative next move from evaluator and W&B evidence."""
    success = safe_float(best.get("success_rate"), 0.0) or 0.0
    crash = safe_float(best.get("crash_rate"), 0.0) or 0.0
    timeout = safe_float(best.get("timeout_rate"), 0.0) or 0.0
    mean_gates = safe_float(best.get("mean_gates"), 0.0) or 0.0
    time_s = safe_float(best.get("mean_time_s_success"))
    worst_tilt = safe_float(best.get("worst_tilt_deg"), 0.0) or 0.0
    cmd_tilt_frac = safe_float(best.get("cmd_tilt_over_limit_frac"), 0.0) or 0.0

    approx_kl_tail = safe_float(wandb_metrics.get("losses/approx_kl", {}).get("tail_mean"))
    clipfrac_tail = safe_float(wandb_metrics.get("losses/clipfrac", {}).get("tail_mean"))
    unstable_diagnostic = (
        (approx_kl_tail is not None and approx_kl_tail > 0.045)
        or (clipfrac_tail is not None and clipfrac_tail > 0.35)
    )
    passed_delta = safe_float(wandb_metrics.get("race/passed_gate_rate", {}).get("delta"))
    finished_tail = safe_float(wandb_metrics.get("race/finished_rate", {}).get("tail_mean"))
    no_evaluator_improvement = (
        safe_float(previous_delta.get("success_rate"), 0.0) <= 0.0
        and safe_float(previous_delta.get("mean_gates"), 0.0) <= 0.0
    )
    no_wandb_conversion = (
        wandb_available
        and bool(wandb_metrics)
        and finished_tail is not None
        and finished_tail <= 0.001
        and passed_delta is not None
        and passed_delta <= 0.002
    )

    if require_wandb and not wandb_available:
        return {
            "branch": "wandb_unavailable_hold",
            "params": {},
            "rationale": (
                "W&B history is required for unattended analysis, but it could not "
                "be fetched. Hold instead of treating missing curves as no conversion."
            ),
        }

    if time_s is not None and success >= target_success and time_s <= target_time:
        return {
            "branch": "stop_target_met",
            "params": {},
            "rationale": "Evaluator target is met. Do not launch another tuning run.",
        }

    if unstable_diagnostic:
        return {
            "branch": "reward_hold_for_instability_diagnostic",
            "params": {},
            "rationale": (
                "W&B PPO diagnostics look unstable. Keep reward parameters fixed, "
                "inspect whether the last reward move caused evaluator regression, "
                "and do not tune PPO hyperparameters in this loop."
            ),
        }

    if success < target_success and no_evaluator_improvement and no_wandb_conversion:
        return {
            "branch": "hold_plateau_no_conversion",
            "params": {},
            "rationale": (
                "Evaluator success/mean_gates did not improve and W&B gate/finish "
                "signals did not convert. Do not launch another automatic reward "
                "move without a new approved reward-only hypothesis or "
                "explicit reward-parameter decision packet."
            ),
        }

    if success < target_success and mean_gates < 2.5:
        return {
            "branch": "gate_acquisition",
            "params": {
                "gate_stage_coef": 13.0,
                "gate_axis_coef": 24.0,
                "gate_front_bonus": 5.0,
                "gate_bonus": 200.0,
                "gate_back_bonus": 35.0,
                "finish_bonus": 175.0,
                "time_penalty": 0.02,
            },
            "rationale": "Low success with low mean gates points to gate acquisition.",
        }

    if crash > 0.25 or worst_tilt > 45.0 or cmd_tilt_frac > 0.10:
        return {
            "branch": "safety_smoothness",
            "params": {
                "crash_penalty": 70.0,
                "obstacle_coef": 6.5,
                "act_coef": 0.02,
                "d_act_xy_coef": 0.10,
                "d_act_th_coef": 0.10,
                "cmd_tilt_coef": 0.9,
                "rpy_coef": 0.9,
                "tilt_limit_deg": 38.0,
                "tilt_excess_coef": 16.0,
            },
            "rationale": "Crash or tilt evidence points to safety and smoothness.",
        }

    if success >= target_success and time_s is not None and time_s > target_time:
        return {
            "branch": "speed",
            "params": {
                "time_penalty": 0.07,
                "gate_axis_coef": 24.0,
                "act_coef": 0.01,
                "d_act_xy_coef": 0.05,
                "d_act_th_coef": 0.05,
                "cmd_tilt_coef": 0.55,
                "rpy_coef": 0.55,
                "tilt_limit_deg": 42.0,
            },
            "rationale": "Success is sufficient but successful runs are too slow.",
        }

    if timeout > 0.30 and success < target_success:
        return {
            "branch": "completion_timeout_pressure",
            "params": {
                "finish_bonus": 180.0,
                "gate_back_bonus": 35.0,
                "timeout_penalty": 95.0,
                "gate_axis_coef": 22.0,
            },
            "rationale": "Timeouts dominate before meeting the success target.",
        }

    return {
        "branch": "hold_or_small_reward_move",
        "params": {},
        "rationale": (
            "No clear reward-only move dominates. Prefer analysis by subagents "
            "before tuning."
        ),
    }


def command_for_recommendation(recommendation: dict[str, Any], analysis_path: Path) -> str | None:
    """Render the next loop command for a parameter-only recommendation."""
    params = recommendation.get("params", {})
    if not params:
        return None
    parts = [
        "pixi run -e gpu python scripts/level3_ppo_loop.py",
        "  --max-iterations 1",
        "  --wandb-enabled",
        "  --wandb-entity aojili77-technical-university-of-munich",
        f"  --analysis-packet {relative_to_root(analysis_path)}",
    ]
    for key, value in params.items():
        parts.append(f"  --param {key}={value:g}")
    return " \\\n".join(parts)


def render_metric_table(metrics: dict[str, dict[str, Any]], limit: int = 18) -> str:
    """Render a compact metric table."""
    if not metrics:
        return "- W&B history unavailable.\n"
    lines = ["| Metric | Last | Tail mean | Trend |", "| --- | ---: | ---: | --- |"]
    for metric, summary in list(metrics.items())[:limit]:
        lines.append(
            "| "
            f"{metric} | {summary.get('last')} | {summary.get('tail_mean')} | "
            f"{summary.get('trend')} |"
        )
    return "\n".join(lines) + "\n"


def render_param_block(params: dict[str, Any]) -> str:
    """Render params as command flags."""
    if not params:
        return "- None.\n"
    return "\n".join(f"- `--param {key}={value:g}`" for key, value in params.items()) + "\n"


def retention_metric_summaries(
    metrics: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return v27 teacher-retention metric summaries when present."""
    return {metric: metrics[metric] for metric in RETENTION_WANDB_METRICS if metric in metrics}


def render_retention_section(metrics: dict[str, dict[str, Any]]) -> str:
    """Render v27 retention diagnostics from W&B summaries."""
    retention = retention_metric_summaries(metrics)
    if not retention:
        return "- No v27 teacher-retention metrics found in W&B history.\n"
    lines = ["| Metric | First | Last | Tail mean | Trend |", "| --- | ---: | ---: | ---: | --- |"]
    for metric in RETENTION_WANDB_METRICS:
        summary = retention.get(metric)
        if summary is None:
            continue
        lines.append(
            "| "
            f"{metric} | {summary.get('first')} | {summary.get('last')} | "
            f"{summary.get('tail_mean')} | {summary.get('trend')} |"
        )
    return "\n".join(lines) + "\n"


def write_subagent_briefs(
    analysis_dir: Path,
    trial_id: str,
    report_path: Path,
    analysis_json_path: Path,
) -> list[str]:
    """Write role-specific briefs that Codex can hand to subagents."""
    paths: list[str] = []
    for role_spec in POST_RUN_REVIEW_ROLES:
        role = role_spec["role"]
        suffix = role_spec["suffix"]
        task = role_spec["task"]
        path = analysis_dir / f"{trial_id}_{suffix}_subagent_brief.md"
        path.write_text(
            "\n".join(
                [
                    f"# Level3 Trial {trial_id}: {role.replace('_', ' ').title()} Brief",
                    "",
                    "## Task",
                    "",
                    task,
                    "",
                    "## Evidence",
                    "",
                    f"- Report: `{relative_to_root(report_path)}`",
                    f"- JSON: `{relative_to_root(analysis_json_path)}`",
                    "",
                    "## Scope",
                    "",
                    "- Structural search is allowed only as an explicit named lane.",
                    "- Do not modify Level3 track geometry or randomization.",
                    "- Final acceptance must be hard eval on `config/level3_dr.toml`.",
                    "- Reward, observation, controller, PPO/training, or reward-structure "
                    "changes must be named and justified by evidence.",
                    "",
                    "## Output",
                    "",
                    "- Key finding:",
                    "- Evidence:",
                    "- Recommended next action:",
                    "- Required packet or command:",
                    "- Risk/rollback condition:",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        paths.append(relative_to_root(path))
    return paths


def render_report(
    trial: dict[str, Any],
    best: dict[str, Any],
    previous_delta: dict[str, Any],
    wandb_summary: dict[str, Any],
    wandb_metrics: dict[str, dict[str, Any]],
    recommendation: dict[str, Any],
    command: str | None,
    analysis_json_path: Path,
) -> str:
    """Render the markdown analysis report."""
    trial_id = str(trial.get("trial_id", "unknown_trial"))
    params = recommendation.get("params", {})
    command_block = (
        f"```bash\n{command}\n```\n"
        if command
        else "- No next training command recommended yet.\n"
    )
    return "\n".join(
        [
            f"# Level3 PPO Post-Run Analysis: {trial_id}",
            "",
            "## Level3 Hard-Eval Scope",
            "",
            "- Structural search is allowed only as an explicit named lane.",
            "- Do not modify Level3 track geometry or randomization.",
            "- Final acceptance must be hard eval on `config/level3_dr.toml`.",
            "- The main agent must write a decision packet before the next training chunk.",
            "- Allowed next decisions: "
            + ", ".join(f"`{option}`" for option in POST_RUN_DECISION_OPTIONS)
            + ".",
            "",
            "## Required Subagent Reviews",
            "",
            "\n".join(
                f"- `{role['role']}`: {role['task']}" for role in POST_RUN_REVIEW_ROLES
            ),
            "",
            "## Evaluator Evidence",
            "",
            f"- Best checkpoint: `{best.get('checkpoint_file')}`",
            f"- Success rate: {safe_float(best.get('success_rate'), 0.0):.2%}",
            f"- Mean successful time: {safe_float(best.get('mean_time_s_success'))}",
            f"- Crash rate: {safe_float(best.get('crash_rate'), 0.0):.2%}",
            f"- Timeout rate: {safe_float(best.get('timeout_rate'), 0.0):.2%}",
            f"- Mean gates: {safe_float(best.get('mean_gates'), 0.0)}",
            f"- Target met: {bool(best.get('target_met'))}",
            f"- Delta vs previous evaluated trial: `{previous_delta}`",
            "",
            "## W&B Evidence",
            "",
            f"- Available: {wandb_summary.get('available')}",
            f"- Run URL: {wandb_summary.get('url')}",
            f"- Reason if unavailable: {wandb_summary.get('reason')}",
            "",
            render_metric_table(wandb_metrics),
            "## V27 Retention Evidence",
            "",
            render_retention_section(wandb_metrics),
            "## Diagnosis",
            "",
            f"- Branch: `{recommendation.get('branch')}`",
            f"- Rationale: {recommendation.get('rationale')}",
            "- PPO instability metrics are diagnostics only; this loop must not tune "
            "`learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, "
            "`num_minibatches`, `hidden_dim`, or `n_obs`.",
            "",
            "## Parameter Recommendation",
            "",
            render_param_block(params),
            command_block,
            "## Decision Gate",
            "",
            "- Next training is blocked until the main agent synthesizes the analysis "
            "and subagent findings into a decision packet under "
            "`experiments/level3_ppo_loop/decisions/`.",
            "- If the next move changes observation/controller/reward structure/PPO "
            "training structure, the packet must name the structural lane and cite "
            "the local or external evidence.",
            "",
            "## Artifacts",
            "",
            f"- JSON snapshot: `{relative_to_root(analysis_json_path)}`",
            "",
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--trial-id")
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--wandb-entity", default=os.environ.get("WANDB_ENTITY"))
    parser.add_argument("--wandb-project")
    parser.add_argument("--wandb-samples", type=int, default=500)
    parser.add_argument("--offline", action="store_true", help="Skip W&B API fetch.")
    parser.add_argument(
        "--require-wandb-online",
        action="store_true",
        help="Hold recommendations if W&B history cannot be fetched.",
    )
    parser.add_argument(
        "--no-state-update",
        action="store_true",
        help="Do not write analysis paths back to state.json.",
    )
    return parser.parse_args()


def main() -> None:
    """Build a post-run analysis packet."""
    args = parse_args()
    args.state_path = args.state_path.resolve()
    args.analysis_dir = args.analysis_dir.resolve()
    if not args.state_path.exists():
        raise SystemExit(f"error: state file not found: {args.state_path}")

    state = load_state(args.state_path)
    target = state.get("target", {})
    target_success = float(target.get("success_rate", TARGET_SUCCESS_RATE))
    target_time = float(target.get("mean_time_s_success", TARGET_TIME_S))
    trial = select_trial(state, args.trial_id)
    if trial is None:
        print("No loop trials found yet; run training/evaluation before analysis.")
        return

    trial_id = str(trial.get("trial_id", "unknown_trial"))
    args.analysis_dir.mkdir(parents=True, exist_ok=True)
    DECISION_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows = read_csv_rows(resolve_optional_path(trial.get("summary_csv")))
    best = best_checkpoint_summary(trial, summary_rows)
    previous = previous_best_summary(state, trial_id)
    previous_delta = eval_delta(best, previous)

    entity = trial.get("wandb_entity") or args.wandb_entity
    project = trial.get("wandb_project_name") or args.wandb_project or DEFAULT_WANDB_PROJECT
    wandb_summary, wandb_rows, wandb_url = fetch_wandb_rows(
        str(entity) if entity else None,
        str(project) if project else None,
        str(trial.get("wandb_run_id")) if trial.get("wandb_run_id") else None,
        max(args.wandb_samples, 1),
        args.offline,
    )
    wandb_metrics = summarize_wandb_rows(wandb_rows)
    wandb_available = bool(wandb_summary.get("available"))
    recommendation = recommend_next_move(
        best,
        wandb_metrics,
        previous_delta,
        target_success,
        target_time,
        wandb_available=wandb_available,
        require_wandb=args.require_wandb_online,
    )

    report_path = args.analysis_dir / f"{trial_id}_analysis.md"
    analysis_json_path = args.analysis_dir / f"{trial_id}_analysis.json"
    command = command_for_recommendation(recommendation, report_path)

    payload = {
        "schema_version": 1,
        "created_at": utc_now(),
        "trial_id": trial_id,
        "target": {
            "success_rate": target_success,
            "mean_time_s_success": target_time,
        },
        "locked_scope": {
            "mode": "structural_search_with_level3_hard_eval",
            "tunable_reward_params": TUNABLE_REWARD_PARAM_KEYS,
            "disabled_reward_channels": LOCKED_REWARD_CHANNELS,
            "immutable_target_eval_config": "config/level3_dr.toml",
            "do_not_modify_level3_track": True,
        },
        "post_run_decision_gate": {
            "status": "awaiting_main_agent_decision",
            "required_review_roles": [
                str(role["role"]) for role in POST_RUN_REVIEW_ROLES
            ],
            "allowed_decisions": POST_RUN_DECISION_OPTIONS,
            "decision_dir": relative_to_root(DECISION_DIR),
            "requires_packet_before_next_training": True,
        },
        "best_summary": best,
        "previous_delta": previous_delta,
        "wandb": wandb_summary,
        "wandb_metric_summaries": wandb_metrics,
        "retention_metric_summaries": retention_metric_summaries(wandb_metrics),
        "recommendation": recommendation,
        "next_command": command,
    }
    analysis_json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    report = render_report(
        trial,
        best,
        previous_delta,
        wandb_summary,
        wandb_metrics,
        recommendation,
        command,
        analysis_json_path,
    )
    report_path.write_text(report, encoding="utf-8")
    subagent_briefs = write_subagent_briefs(
        args.analysis_dir,
        trial_id,
        report_path,
        analysis_json_path,
    )

    if not args.no_state_update:
        trial["analysis_report"] = relative_to_root(report_path)
        trial["analysis_json"] = relative_to_root(analysis_json_path)
        trial["analysis_subagent_briefs"] = subagent_briefs
        trial["analysis_created_at"] = utc_now()
        trial["post_run_decision_required"] = True
        trial["post_run_required_review_roles"] = [
            str(role["role"]) for role in POST_RUN_REVIEW_ROLES
        ]
        trial["main_agent_decision_packet"] = None
        state["pending_post_run_decision"] = {
            "created_at": utc_now(),
            "status": "awaiting_main_agent_decision",
            "trial_id": trial_id,
            "analysis_report": relative_to_root(report_path),
            "analysis_json": relative_to_root(analysis_json_path),
            "subagent_briefs": subagent_briefs,
            "required_review_roles": [
                str(role["role"]) for role in POST_RUN_REVIEW_ROLES
            ],
            "allowed_decisions": POST_RUN_DECISION_OPTIONS,
            "decision_dir": relative_to_root(DECISION_DIR),
            "requires_packet_before_next_training": True,
            "hard_eval_config": "config/level3_dr.toml",
            "do_not_modify_level3_track": True,
        }
        if wandb_url:
            trial["wandb_url"] = wandb_url
        write_state(args.state_path, state)

    print(f"wrote {relative_to_root(report_path)}")
    print(f"wrote {relative_to_root(analysis_json_path)}")
    for path in subagent_briefs:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
