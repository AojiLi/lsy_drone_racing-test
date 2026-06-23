"""Tests for the Level3 v35 competence-gated gate-phase curriculum lane."""

from __future__ import annotations

import inspect

import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Args,
    GatePhaseResetCurriculum,
    make_envs,
    train_ppo,
    wrapped_instance,
)
from scripts import level3_ppo_loop


@pytest.mark.unit
def test_competence_gated_curriculum_args_validate_schedule() -> None:
    """Competence gating should require a bounded, nonzero curriculum schedule."""
    Args.create(
        gate_phase_reset_prob=0.45,
        gate_phase_reset_competence_enabled=True,
        gate_phase_reset_competence_start_prob=0.12,
        gate_phase_reset_competence_step_prob=0.02,
    )

    with pytest.raises(ValueError, match="requires gate_phase_reset_prob"):
        Args.create(gate_phase_reset_competence_enabled=True, gate_phase_reset_prob=0.0)
    with pytest.raises(ValueError, match="start_prob"):
        Args.create(
            gate_phase_reset_prob=0.45,
            gate_phase_reset_competence_enabled=True,
            gate_phase_reset_competence_start_prob=0.5,
        )
    with pytest.raises(ValueError, match="step_prob"):
        Args.create(
            gate_phase_reset_prob=0.45,
            gate_phase_reset_competence_enabled=True,
            gate_phase_reset_competence_step_prob=0.0,
        )


@pytest.mark.unit
def test_competence_gated_curriculum_uses_initial_probability() -> None:
    """The wrapper should start below the maximum pressure and remain adjustable."""
    envs = make_envs(
        config="level3.toml",
        num_envs=4,
        jax_device="cpu",
        torch_device=torch.device("cpu"),
        coefs={
            "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "n_obs": 2,
            "gate_phase_reset_prob": 0.45,
            "gate_phase_reset_initial_prob": 0.12,
        },
    )
    try:
        curriculum = wrapped_instance(envs, GatePhaseResetCurriculum)
        assert curriculum is not None
        assert curriculum.gate_phase_reset_prob == pytest.approx(0.12)

        curriculum.set_probability(0.2)
        assert curriculum.gate_phase_reset_prob == pytest.approx(0.2)
    finally:
        envs.close()


@pytest.mark.unit
def test_train_loop_logs_and_updates_competence_curriculum() -> None:
    """The PPO loop should update curriculum pressure from rollout race metrics."""
    source = inspect.getsource(train_ppo)

    assert "gate_phase_reset_competence_enabled" in source
    assert "curriculum/gate_phase_reset_prob" in source
    assert "curriculum/competence_gate_met" in source
    assert "set_probability(next_gate_phase_reset_prob)" in source


@pytest.mark.unit
def test_loop_registers_v35_competence_gated_curriculum_lane() -> None:
    """The orchestrator should launch v35 only as an explicit structural lane."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v35_competence_gated_gate_phase_curriculum_from_loop101"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    assert hypothesis["requires_training_support"] == (
        "competence_gated_gate_phase_curriculum_support"
    )
    assert hypothesis["params"]["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert hypothesis["params"]["track_generator_profile"] == "default"
    assert hypothesis["params"]["gate_phase_reset_prob"] == 0.45
    assert hypothesis["params"]["gate_phase_reset_competence_enabled"] is True
    assert hypothesis["params"]["gate_phase_reset_competence_start_prob"] == pytest.approx(0.12)
    assert hypothesis["architecture"]["changed_reward_numbers"] == []
    assert "track_generator_profile" not in hypothesis["architecture"]["changed_training_numbers"]
    assert "competence_gated_gate_phase_curriculum_support" in (
        level3_ppo_loop.SUPPORTED_TRAINING_STRUCTURES
    )

    for key in (
        "gate_phase_reset_competence_enabled",
        "gate_phase_reset_competence_start_prob",
        "gate_phase_reset_competence_step_prob",
        "gate_phase_reset_competence_min_passed_gate_rate",
        "gate_phase_reset_competence_min_finished_rate",
        "gate_phase_reset_competence_max_crashed_rate",
    ):
        assert key in level3_ppo_loop.FIRE_PARAM_KEYS
