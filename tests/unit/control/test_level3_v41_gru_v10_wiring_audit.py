"""Tests for the Level3 v41 GRU/v10 wiring-audit lane."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import audit_level3_v41_gru_v10_wiring, level3_ppo_loop

ROOT = Path(__file__).parents[3]
V41_PACKET = (
    ROOT
    / "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop112_reject_v40_launch_v41_gru_v10_wiring_audit.md"
)


@pytest.mark.unit
def test_v41_packet_rejects_v40_before_more_gru_training() -> None:
    """The v41 packet must block v40 maturation and keep Level3 unchanged."""
    packet = V41_PACKET.read_text()

    assert "Decision: `launch_named_structural_lane`" in packet
    assert "v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity" in packet
    assert "Do not continue v40 as-is" in packet
    assert "Do not start future training from loop112 checkpoints" in packet
    assert "Final acceptance remains hard eval on unchanged `config/level3.toml`" in packet
    assert "No MPC, waypoint planner, rule controller" in packet


@pytest.mark.unit
def test_v41_audit_script_covers_required_checks() -> None:
    """The audit script must cover all required v41 wiring gates."""
    required = set(audit_level3_v41_gru_v10_wiring.REQUIRED_CHECKS)

    assert "checkpoint_metadata" in required
    assert "observation_parity_and_sanity" in required
    assert "train_eval_action_scale_parity" in required
    assert "train_inference_recurrent_actor_parity" in required
    assert "zero_update_save_reload_parity" in required
    assert "hidden_state_reset_and_carry_parity" in required
    assert "recurrent_ppo_gradient_update_sanity" in required


@pytest.mark.unit
def test_loop_registers_v42_gru_v10_gate_phase_curriculum_lane() -> None:
    """v42 must keep Level3 fixed and add only the training-only curriculum."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v42_gru_v10_gate_phase_reset_curriculum_from_scratch"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["from_scratch"] is True
    assert "loop112" not in str(hypothesis.get("initial_checkpoint", ""))
    assert hypothesis["train_timesteps"] == 10_000_000
    assert hypothesis["eval_milestones_m"] == "1,2,3,4,5,8,10"
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V42_GRU_V10_GATE_PHASE_CURRICULUM_DECISION_PACKET
    )

    architecture = hypothesis["architecture"]
    assert architecture["track_geometry_change"] == "forbidden"
    assert architecture["policy_arch"] == "recurrent_actor_gru256"
    assert architecture["diagnostic_precondition"] == (
        level3_ppo_loop.V41_GRU_V10_WIRING_AUDIT_PACKET
    )

    params = hypothesis["params"]
    assert params["policy_arch"] == "recurrent_actor_gru256"
    assert params["gate_phase_reset_prob"] == pytest.approx(0.45)
    assert params["track_generator_profile"] == "default"
