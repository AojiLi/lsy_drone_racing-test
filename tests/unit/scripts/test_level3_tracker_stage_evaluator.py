"""Tests for tracker stage metric aggregation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import evaluate_level3_tracker_stage as evaluator
from scripts.check_level3_tracker_stage_gate import load_json, stage_by_id

ROOT = Path(__file__).parents[3]
GATES = ROOT / "experiments/level3_ppo_loop/tracker_qualification_gates.json"


def test_hover_aggregation_produces_gate_metrics() -> None:
    """Hover aggregation should produce every metric used by the hover gate."""
    gates = load_json(GATES)
    stage = stage_by_id(gates, "hover")
    rows = [
        {
            "success": True,
            "crashed": False,
            "all_finite": True,
            "mean_position_error_m": 0.08,
            "p90_position_error_m": 0.16,
            "mean_speed_mps": 0.1,
            "mean_action_delta_l2": 0.18,
            "mean_time_to_target_s": 0.4,
        },
        {
            "success": True,
            "crashed": False,
            "all_finite": True,
            "mean_position_error_m": 0.1,
            "p90_position_error_m": 0.18,
            "mean_speed_mps": 0.12,
            "mean_action_delta_l2": 0.2,
            "mean_time_to_target_s": 0.5,
        },
    ]

    metrics = evaluator.aggregate_stage_rows(stage, rows)

    assert metrics["success_rate"] == 1.0
    assert metrics["crash_rate"] == 0.0
    assert metrics["all_finite"] is True
    assert metrics["mean_position_error_m"] == pytest.approx(0.09)
    assert metrics["mean_action_delta_l2"] == pytest.approx(0.19)
    assert metrics["mean_time_to_target_s"] == pytest.approx(0.45)


def test_aggregator_covers_all_non_planner_gate_metrics() -> None:
    """Every non-planner stage gate metric should be emitted by the aggregator."""
    gates = load_json(GATES)
    fake_row = {
        "success": True,
        "crashed": False,
        "all_finite": True,
        "brake_success": True,
        "path_completed": True,
        "valid_aperture_cross": True,
        "post_gate_recovered": True,
        "mean_position_error_m": 0.1,
        "p90_position_error_m": 0.2,
        "mean_final_position_error_m": 0.1,
        "p90_final_position_error_m": 0.2,
        "mean_speed_mps": 0.1,
        "mean_terminal_speed_mps": 0.1,
        "p90_terminal_speed_mps": 0.2,
        "mean_overshoot_m": 0.1,
        "p90_overshoot_m": 0.2,
        "mean_time_to_target_s": 0.5,
        "mean_cross_track_error_m": 0.1,
        "p90_cross_track_error_m": 0.2,
        "mean_speed_error_mps": 0.1,
        "mean_heading_error_rad": 0.1,
        "p90_heading_error_rad": 0.2,
        "mean_yaw_rate_abs": 0.1,
        "mean_action_delta_l2": 0.1,
        "p90_action_delta_l2": 0.2,
        "hold_time_ratio": 0.8,
        "mean_switch_overshoot_m": 0.1,
        "mean_corner_overshoot_m": 0.1,
        "oscillation_score": 0.1,
        "mean_aperture_yz_error_m": 0.1,
        "p90_aperture_yz_error_m": 0.2,
        "mean_post_gate_speed_mps": 0.4,
    }

    for stage in gates["stages"]:
        if stage["id"] == "planner_integration_smoke":
            continue
        metrics = evaluator.aggregate_stage_rows(stage, [fake_row])
        metrics["checkpoint_backed"] = True
        for required in stage["required_metrics"]:
            assert required["name"] in metrics, (stage["id"], required["name"])


def test_gate_aperture_aggregation_uses_crossing_as_success() -> None:
    """Gate-aperture success should be valid crossing, not generic final error."""
    gates = load_json(GATES)
    stage = stage_by_id(gates, "gate_aperture_reference")
    rows = [
        {
            "success": False,
            "crashed": False,
            "all_finite": True,
            "valid_aperture_cross": True,
            "post_gate_recovered": True,
            "mean_aperture_yz_error_m": 0.1,
            "p90_aperture_yz_error_m": 0.2,
            "mean_post_gate_speed_mps": 0.4,
        },
        {
            "success": False,
            "crashed": True,
            "all_finite": True,
            "valid_aperture_cross": False,
            "post_gate_recovered": False,
            "mean_aperture_yz_error_m": 0.3,
            "p90_aperture_yz_error_m": 0.4,
            "mean_post_gate_speed_mps": 0.8,
        },
    ]

    metrics = evaluator.aggregate_stage_rows(stage, rows)

    assert metrics["valid_aperture_cross_rate"] == 0.5
    assert metrics["post_gate_recovery_rate"] == 0.5
    assert metrics["success_rate"] == 0.5
    assert metrics["crash_rate"] == 0.5


def test_planner_smoke_aggregates_level3_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    """Planner smoke should report the fields required by the final gate."""
    gates = load_json(GATES)
    stage = stage_by_id(gates, "planner_integration_smoke")

    def fake_run_level3_controller_seed(**kwargs: object) -> dict[str, object]:
        seed = int(kwargs["seed"])
        return {
            "seed": seed,
            "finite_action": True,
            "nonzero_first_gate_progress": seed != 102,
            "max_gate_index": 1 if seed == 101 else 0,
            "early_termination": seed == 102,
        }

    monkeypatch.setattr(
        evaluator,
        "run_level3_controller_seed",
        fake_run_level3_controller_seed,
    )

    metrics = evaluator.evaluate_planner_smoke(
        stage=stage,
        checkpoint=Path("/tmp/fake_tracker.ckpt"),
        seeds="101-103",
        max_steps=10,
        early_termination_step_threshold=5,
    )

    assert metrics["level3_toml_diff_clean"] is True
    assert metrics["nonzero_first_gate_progress_ratio"] == pytest.approx(2 / 3)
    assert metrics["gate0_pass_count"] == 1
    assert metrics["early_termination_ratio"] == pytest.approx(1 / 3)


def test_planner_smoke_writes_trace_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Planner smoke should write per-step trace rows outside the metrics payload."""
    gates = load_json(GATES)
    stage = stage_by_id(gates, "planner_integration_smoke")
    trace_flags: list[bool] = []

    def fake_run_level3_controller_seed(**kwargs: object) -> dict[str, object]:
        seed = int(kwargs["seed"])
        trace_flags.append(bool(kwargs["trace_steps"]))
        return {
            "seed": seed,
            "finite_action": True,
            "nonzero_first_gate_progress": True,
            "max_gate_index": 0,
            "early_termination": False,
            "trace": [
                {
                    "seed": seed,
                    "step": 1,
                    "gate_local_x": -0.5,
                    "gate_local_y": 0.1,
                    "gate_local_z": -0.2,
                    "aperture_y": 0.0,
                    "aperture_z": -0.1,
                    "aperture_yz_error": 0.14142135623730953,
                    "reference_x": 0.1,
                    "phase_id": 2,
                    "termination_reason": "running",
                }
            ],
        }

    monkeypatch.setattr(
        evaluator,
        "run_level3_controller_seed",
        fake_run_level3_controller_seed,
    )
    trace_output = tmp_path / "planner_trace.json"

    metrics = evaluator.evaluate_planner_smoke(
        stage=stage,
        checkpoint=Path("/tmp/fake_tracker.ckpt"),
        seeds="101-102",
        max_steps=10,
        early_termination_step_threshold=5,
        trace_output=trace_output,
    )
    payload = evaluator.json.loads(trace_output.read_text())

    assert trace_flags == [True, True]
    assert metrics["trace_output"] == str(trace_output)
    assert metrics["trace_step_rows"] == 2
    assert "trace" not in metrics["episode_rows"][0]
    assert payload["stage"] == "planner_integration_smoke"
    assert payload["trace_rows"][0]["seed"] == 101
    assert payload["trace_rows"][0]["aperture_y"] == pytest.approx(0.0)
    assert payload["trace_rows"][0]["aperture_z"] == pytest.approx(-0.1)
    assert payload["trace_rows"][0]["aperture_yz_error"] == pytest.approx(
        ((0.1 - 0.0) ** 2 + (-0.2 + 0.1) ** 2) ** 0.5
    )
