"""Tests for the Level3 tracker qualification stage-gate checker."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.check_level3_tracker_stage_gate import evaluate_stage, load_json, main

ROOT = Path(__file__).parents[3]
GATES = ROOT / "experiments/level3_ppo_loop/tracker_qualification_gates.json"


def test_hover_stage_passes_and_unlocks_point_hold() -> None:
    """A complete hover report should unlock the next free-space stage."""
    gates = load_json(GATES)
    metrics = {
        "stage": "hover",
        "metrics": {
            "checkpoint_backed": True,
            "all_finite": True,
            "success_rate": 0.98,
            "crash_rate": 0.0,
            "mean_position_error_m": 0.08,
            "p90_position_error_m": 0.16,
            "mean_speed_mps": 0.1,
            "mean_action_delta_l2": 0.18,
        },
    }

    summary = evaluate_stage(gates, "hover", metrics)

    assert summary["passed"] is True
    assert summary["next_stage_unlocked"] == "point_hold"
    assert not summary["failures"]


def test_stage_gate_fails_when_metric_is_missing() -> None:
    """Missing required metrics should fail instead of silently passing."""
    gates = load_json(GATES)
    metrics = {
        "stage": "hover",
        "metrics": {
            "checkpoint_backed": True,
            "all_finite": True,
            "success_rate": 0.98,
            "crash_rate": 0.0,
            "mean_position_error_m": 0.08,
            "p90_position_error_m": 0.16,
            "mean_speed_mps": 0.1,
        },
    }

    summary = evaluate_stage(gates, "hover", metrics)

    assert summary["passed"] is False
    assert "missing metric 'mean_action_delta_l2'" in summary["failures"]


def test_prerequisites_are_enforced_from_history() -> None:
    """Later stages should require prior stages to be marked passed."""
    gates = load_json(GATES)
    metrics = {
        "stage": "line_tracking",
        "metrics": {
            "checkpoint_backed": True,
            "all_finite": True,
            "success_rate": 0.95,
            "crash_rate": 0.0,
            "mean_cross_track_error_m": 0.1,
            "p90_cross_track_error_m": 0.2,
            "mean_speed_error_mps": 0.12,
            "mean_action_delta_l2": 0.2,
        },
    }
    history = {
        "stage_results": {
            "hover": {"passed": True},
            "point_hold": {"passed": True},
            "point_reach": {"passed": True},
            "brake_to_point": {"passed": False},
        }
    }

    summary = evaluate_stage(
        gates,
        "line_tracking",
        metrics,
        history_doc=history,
        require_prerequisites=True,
    )

    assert summary["passed"] is False
    assert "prerequisite stage 'brake_to_point' is not marked passed" in summary["failures"]


def test_cli_exits_nonzero_on_failed_gate(tmp_path: Path) -> None:
    """The CLI contract should fail closed when metrics do not meet a gate."""
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "stage": "hover",
                "metrics": {
                    "checkpoint_backed": True,
                    "all_finite": True,
                    "success_rate": 0.1,
                    "crash_rate": 0.0,
                    "mean_position_error_m": 0.08,
                    "p90_position_error_m": 0.16,
                    "mean_speed_mps": 0.1,
                    "mean_action_delta_l2": 0.18,
                },
            }
        )
    )

    with pytest.raises(SystemExit) as exc_info:
        old_argv = sys.argv
        sys.argv = [
            "check_level3_tracker_stage_gate.py",
            "--stage",
            "hover",
            "--metrics-json",
            str(metrics_path),
        ]
        try:
            main()
        finally:
            sys.argv = old_argv

    assert exc_info.value.code == 2
