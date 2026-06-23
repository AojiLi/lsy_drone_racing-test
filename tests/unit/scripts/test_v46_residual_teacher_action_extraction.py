"""Tests for v46 residual-GRU teacher action extraction."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import MLPResidualRecurrentActorAgent
from scripts import level3_ppo_loop
from scripts.build_v27_retention_dataset import teacher_distribution_and_action


class _FakeResidualController:
    """Minimal controller surface used by the retention dataset builder."""

    def __init__(
        self,
        agent: MLPResidualRecurrentActorAgent,
        obs_vec: np.ndarray,
    ) -> None:
        self.agent = agent
        self.policy_arch = POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
        self.device = torch.device("cpu")
        self._obs_vec = obs_vec.astype(np.float32)
        self._last_action_norm = np.zeros(4, dtype=np.float32)
        self._recurrent_hidden_state = agent.get_initial_state(1, self.device)

    def _obs_rl(self, _obs: dict) -> np.ndarray:
        return self._obs_vec.copy()

    def _filter_action(self, action_norm: np.ndarray) -> np.ndarray:
        return np.clip(np.asarray(action_norm, dtype=np.float32), -1.0, 1.0)

    @staticmethod
    def _scale_action(action_norm: np.ndarray) -> np.ndarray:
        return np.asarray(action_norm, dtype=np.float32)

    def reset_episode_state(self, _obs: dict) -> None:
        self._last_action_norm = np.zeros(4, dtype=np.float32)
        self._recurrent_hidden_state = self.agent.get_initial_state(1, self.device)


@pytest.mark.unit
def test_v46_lane_is_held_until_residual_teacher_action_preflight() -> None:
    """v46 should be visible to the loop but blocked before parity support."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v46_v5_residual_frontier_teacher_action_retention_preflight"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["architecture"]["track_geometry_change"] == "forbidden"
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V46_RESIDUAL_FRONTIER_RETENTION_DECISION_PACKET
    )
    assert hypothesis["requires_training_support"] == (
        "residual_frontier_teacher_action_extraction_preflight_support"
    )
    assert not level3_ppo_loop.structural_hypothesis_runnable(hypothesis)


@pytest.mark.unit
def test_teacher_distribution_includes_residual_gru_branch() -> None:
    """Dataset extraction must not fall back to the MLP base actor for loop107."""
    torch.manual_seed(460)
    obs_vec = np.linspace(-0.4, 0.4, 68, dtype=np.float32)
    agent = MLPResidualRecurrentActorAgent(
        (68,),
        (4,),
        hidden_dim=8,
        recurrent_hidden_dim=8,
    )
    with torch.no_grad():
        agent.actor_residual_head.weight.zero_()
        agent.actor_residual_head.bias.copy_(torch.tensor([0.2, -0.15, 0.1, -0.05]))

    controller = _FakeResidualController(agent, obs_vec)
    obs_tensor = torch.as_tensor(obs_vec, dtype=torch.float32).unsqueeze(0)
    hidden = agent.get_initial_state(1, torch.device("cpu"))
    done = torch.zeros(1)

    with torch.no_grad():
        base_only = agent.actor_mean(obs_tensor)
        direct_action, _, _, _, _ = agent.get_action_and_value(
            obs_tensor,
            hidden,
            done,
            deterministic=True,
        )

    _student_obs, teacher_mean, teacher_logstd, scaled_action = (
        teacher_distribution_and_action(controller, {})
    )

    assert np.allclose(teacher_mean, direct_action.squeeze(0).numpy(), atol=1e-6)
    assert not np.allclose(teacher_mean, base_only.squeeze(0).numpy(), atol=1e-4)
    assert np.allclose(scaled_action, teacher_mean, atol=1e-6)
    assert teacher_logstd.shape == (4,)


@pytest.mark.unit
def test_residual_teacher_hidden_state_carries_and_resets() -> None:
    """Extraction should advance GRU hidden state and reset it per episode."""
    torch.manual_seed(461)
    obs_vec = np.linspace(-1.0, 1.0, 68, dtype=np.float32)
    agent = MLPResidualRecurrentActorAgent(
        (68,),
        (4,),
        hidden_dim=8,
        recurrent_hidden_dim=8,
    )
    controller = _FakeResidualController(agent, obs_vec)

    initial_hidden = controller._recurrent_hidden_state.detach().clone()
    teacher_distribution_and_action(controller, {})
    carried_hidden = controller._recurrent_hidden_state.detach().clone()

    assert not torch.allclose(carried_hidden, initial_hidden)

    controller.reset_episode_state({})

    assert torch.allclose(controller._recurrent_hidden_state, initial_hidden)
