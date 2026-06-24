"""Write a plain-language note for the latest Level3 PPO loop.

This script is intentionally small and source-backed: it reads the loop state and
packets already produced by the Codex workflow, then writes a Markdown note under
drone_notes/level3_loops. It does not train, evaluate, query W&B, or touch
checkpoints.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = ROOT / "experiments" / "level3_ppo_loop" / "state.json"
DEFAULT_OUT_DIR = ROOT / "drone_notes" / "level3_loops"


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Parse finite floats without raising on missing values."""
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def percent(value: Any) -> str:
    """Format a 0-1 ratio as a percentage."""
    parsed = safe_float(value)
    if parsed is None:
        return "n/a"
    return f"{parsed * 100:.1f}%"


def number(value: Any, suffix: str = "") -> str:
    """Format a finite number with a compact precision."""
    parsed = safe_float(value)
    if parsed is None:
        return "n/a"
    return f"{parsed:.3f}{suffix}".rstrip("0").rstrip(".")


def repo_path(value: Any) -> str:
    """Return a display-safe repository path string."""
    return str(value) if value not in (None, "") else "n/a"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"error: expected JSON object in {path}")
    return data


def trial_loop_number(trial: dict[str, Any]) -> str:
    """Return the loop number from a trial id."""
    match = re.search(r"level3_loop_(\d+)", str(trial.get("trial_id", "")))
    return match.group(1) if match else "unknown"


def sanitize_filename(value: str) -> str:
    """Return a conservative Markdown file stem."""
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or "level3-loop-note"


def latest_trial(state: dict[str, Any], trial_id: str | None) -> dict[str, Any]:
    """Return an explicitly requested or latest evaluated trial."""
    trials = [trial for trial in state.get("trials", []) if isinstance(trial, dict)]
    if trial_id:
        for trial in trials:
            if trial.get("trial_id") == trial_id:
                return trial
        raise SystemExit(f"error: trial_id not found in state: {trial_id}")
    for trial in reversed(trials):
        if trial.get("status") in {"evaluated", "target_met"}:
            return trial
    if trials:
        return trials[-1]
    raise SystemExit("error: no trials found in state")


def best_summary(trial: dict[str, Any]) -> dict[str, Any]:
    """Return the trial's best summary, if present."""
    best = trial.get("best_summary")
    if isinstance(best, dict):
        return best
    summaries = [item for item in trial.get("summaries", []) if isinstance(item, dict)]
    return summaries[-1] if summaries else {}


def packet_paths(trial: dict[str, Any], state: dict[str, Any]) -> dict[str, str]:
    """Collect the most useful packet paths for the note."""
    pending = state.get("pending_post_run_decision")
    if not isinstance(pending, dict):
        pending = {}
    paths = {
        "analysis": pending.get("analysis_report"),
        "subagent_reviews": pending.get("subagent_review_packet")
        or state.get("last_subagent_reviews"),
        "decision": pending.get("decision_packet") or state.get("last_main_agent_decision_packet"),
    }
    for packet_type, key in (
        ("analysis", "analysis_packets"),
        ("decision", "approved_hypothesis_packets"),
    ):
        if paths.get(packet_type):
            continue
        packets = trial.get(key)
        if isinstance(packets, list) and packets:
            last = packets[-1]
            if isinstance(last, dict):
                paths[packet_type] = last.get("path")
    return {key: repo_path(value) for key, value in paths.items() if value}


def note_path_for(trial: dict[str, Any], out_dir: Path) -> Path:
    """Return the default note path for a trial."""
    loop_num = trial_loop_number(trial)
    proposal = sanitize_filename(str(trial.get("proposal") or trial.get("trial_id") or "loop"))
    return out_dir / f"loop{loop_num}-{proposal}.md"


def read_optional_text(path: Path | None) -> str:
    """Read optional extra text."""
    if path is None:
        return ""
    if not path.exists():
        raise SystemExit(f"error: extra note file does not exist: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_note(
    state: dict[str, Any],
    trial: dict[str, Any],
    *,
    reader_summary: str = "",
) -> str:
    """Build a Chinese reader note for a loop."""
    summary = best_summary(trial)
    loop_num = trial_loop_number(trial)
    trial_id = str(trial.get("trial_id", "unknown"))
    proposal = str(trial.get("proposal", "unknown"))
    target_met = bool(summary.get("target_met"))
    next_lane = repo_path(state.get("next_structural_lane"))
    next_command = repo_path(state.get("next_recommended_command"))
    packets = packet_paths(trial, state)
    best = state.get("best") if isinstance(state.get("best"), dict) else {}
    frontier = (
        f"{repo_path(best.get('checkpoint'))}: success {percent(best.get('success_rate'))}, "
        f"mean gates {number(best.get('mean_gates'))}, "
        f"crash {percent(best.get('crash_rate'))}, "
        f"time {number(best.get('mean_time_s_success'), 's')}"
        if best
        else "n/a"
    )

    if target_met:
        one_line = "这轮已经达到 Level3 目标，可以进入最终确认。"
    else:
        one_line = (
            "这轮没有达到 60% 完赛率目标；它提供的是下一步该怎么改的证据。"
        )

    lines = [
        f"# Loop {loop_num}: {proposal}",
        "",
        f"- 生成时间: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Trial: `{trial_id}`",
        f"- 训练赛道: `{repo_path(trial.get('train_config'))}`",
        f"- 硬评估赛道: `{repo_path(trial.get('eval_config'))}`",
        f"- Observation: `{repo_path(trial.get('observation_layout'))}`",
        f"- 结构假设: `{repo_path(trial.get('structural_hypothesis'))}`",
        "",
        "## 一句话",
        "",
        one_line,
        "",
        "## 这轮到底做了什么",
        "",
        f"- 名字: `{proposal}`",
        f"- 训练步数: `{repo_path(trial.get('step_curve_policy', {}).get('train_timesteps'))}`",
        f"- 初始 checkpoint: `{repo_path(trial.get('initial_checkpoint'))}`",
        f"- 网络/训练结构: `{repo_path(trial.get('training_structure'))}`",
        f"- hidden_dim: `{repo_path(trial.get('params', {}).get('hidden_dim'))}`",
        f"- W&B run: `{repo_path(trial.get('wandb_url') or trial.get('wandb_run_id'))}`",
        "",
        "## 结果怎么读",
        "",
        f"- 最好 checkpoint: `{repo_path(summary.get('checkpoint'))}`",
        f"- checkpoint 文件: `{repo_path(summary.get('checkpoint_file'))}`",
        f"- 完赛率: **{percent(summary.get('success_rate'))}**",
        f"- 平均过门数: **{number(summary.get('mean_gates'))}**",
        f"- 撞毁率: **{percent(summary.get('crash_rate'))}**",
        f"- timeout: **{percent(summary.get('timeout_rate'))}**",
        f"- 成功时平均用时: **{number(summary.get('mean_time_s_success'), 's')}**",
        f"- 是否达到目标: **{'是' if target_met else '否'}**",
        "",
        "## 和当前最好结果相比",
        "",
        f"- 当前全局最好: {frontier}",
        "",
        "## 通俗理解",
        "",
        "- W&B 曲线和训练 reward 只是诊断，真正算数的是 hard eval。",
        "- 如果完赛率没有涨，但成功时速度够快，说明主要问题通常不是速度，而是稳定过门、避障和连续控制。",
        "- 如果 final checkpoint 比中间 checkpoint 差，后续要优先选中间最好点，不默认 final 最好。",
        "",
        "## 下一步",
        "",
        f"- 下一条 lane: `{next_lane}`",
        "",
        "```bash",
        next_command,
        "```",
        "",
        "## 重要文件",
        "",
    ]
    for label, path in packets.items():
        lines.append(f"- {label}: `{path}`")
    if not packets:
        lines.append("- n/a")
    if reader_summary:
        lines.extend(["", "## Reader-Note 子 Agent 补充", "", reader_summary])
    lines.append("")
    return "\n".join(lines)


def write_state_note_record(state_path: Path, state: dict[str, Any], trial: dict[str, Any], note: Path) -> None:
    """Record the generated reader note in state."""
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trial_id": trial.get("trial_id"),
        "note_path": str(note.relative_to(ROOT) if note.is_relative_to(ROOT) else note),
    }
    notes = state.setdefault("reader_notes", [])
    if isinstance(notes, list):
        notes.append(record)
    state["last_reader_note"] = record
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--trial-id", default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--reader-summary-file", type=Path, default=None)
    parser.add_argument("--update-state", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state_path = args.state if args.state.is_absolute() else ROOT / args.state
    state = load_json(state_path)
    trial = latest_trial(state, args.trial_id)
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_path = args.out if args.out is not None else note_path_for(trial, out_dir)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    reader_summary = read_optional_text(args.reader_summary_file)
    note = build_note(state, trial, reader_summary=reader_summary)
    if args.dry_run:
        print(note)
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(note, encoding="utf-8")
    if args.update_state:
        write_state_note_record(state_path, state, trial, out_path)
    print(out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path)


if __name__ == "__main__":
    main()
