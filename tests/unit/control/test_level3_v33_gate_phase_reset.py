"""Tests for the Level3 v33 gate-phase reset curriculum lane."""

from __future__ import annotations

import inspect

import numpy as np
import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import Args, make_envs, wrapped_attr
from scripts import level3_ppo_loop


@pytest.mark.unit
def test_gate_phase_reset_args_validate_probability_and_ranges() -> None:
    """Curriculum reset parameters should reject invalid training distributions."""
    Args.create(gate_phase_reset_prob=0.45)

    with pytest.raises(ValueError, match="gate_phase_reset_prob"):
        Args.create(gate_phase_reset_prob=1.2)
    with pytest.raises(ValueError, match="x_min"):
        Args.create(gate_phase_reset_x_min=-0.1, gate_phase_reset_x_max=-0.5)
    with pytest.raises(ValueError, match="speed_min"):
        Args.create(gate_phase_reset_speed_min=1.0, gate_phase_reset_speed_max=0.5)


@pytest.mark.unit
def test_gate_phase_reset_wrapper_is_training_only_before_reward_observation_wrappers() -> None:
    """The curriculum should alter training reset states before reward and obs state initialize."""
    source = inspect.getsource(make_envs)

    assert "GatePhaseResetCurriculum(" in source
    assert source.index("GatePhaseResetCurriculum(") < source.index("NormalizeVectorActions(")
    assert source.index("GatePhaseResetCurriculum(") < source.index("Level2RaceReward(")


@pytest.mark.unit
def test_loop_registers_v33_gate_phase_reset_curriculum_lane() -> None:
    """The orchestrator must pass v33 curriculum parameters through Fire."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v33_gate_phase_reset_curriculum_from_loop097_12m"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["requires_training_support"] == "gate_phase_reset_curriculum_support"
    assert hypothesis["params"]["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert hypothesis["params"]["gate_phase_reset_prob"] == 0.45
    assert hypothesis["architecture"]["changed_reward_numbers"] == []
    for key in (
        "gate_phase_reset_prob",
        "gate_phase_reset_x_min",
        "gate_phase_reset_x_max",
        "gate_phase_reset_yz_max",
        "gate_phase_reset_speed_min",
        "gate_phase_reset_speed_max",
    ):
        assert key in level3_ppo_loop.FIRE_PARAM_KEYS


@pytest.mark.unit
def test_gate_phase_reset_curriculum_updates_raw_env_state_on_reset() -> None:
    """A probability-1 curriculum reset should place some slots at later target gates."""
    envs = make_envs(
        config="level3.toml",
        num_envs=32,
        jax_device="cpu",
        torch_device=torch.device("cpu"),
        coefs={
            "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "n_obs": 2,
            "gate_phase_reset_prob": 1.0,
        },
    )
    try:
        envs.reset(seed=123)
        data = wrapped_attr(envs, "data")
        assert data is not None

        target_gate = np.asarray(data.target_gate)[:, 0]
        gates_visited = np.asarray(data.gates_visited)[:, 0]
        steps = np.asarray(data.steps)

        assert target_gate.min() >= 0
        assert target_gate.max() > 0
        assert np.all(steps == 0)
        assert np.all(gates_visited[np.arange(target_gate.shape[0]), target_gate])
    finally:
        envs.close()
