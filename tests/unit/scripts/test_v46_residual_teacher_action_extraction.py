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
def test_v47_residual_frontier_union_retention_lane_is_runnable() -> None:
    """v47 is the bounded production screen after the v46 preflight passes."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v47_v5_residual_frontier_union_retention_mlp_from_loop110_3m"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["architecture"]["track_geometry_change"] == "forbidden"
    assert hypothesis["requires_training_support"] == "teacher_retention_kl"
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V47_RESIDUAL_FRONTIER_UNION_RETENTION_DECISION_PACKET
    )
    assert hypothesis["params"]["v27_retention_dataset_path"] == (
        level3_ppo_loop.V46_RESIDUAL_FRONTIER_UNION_RETENTION_DATASET_PATH
    )
    assert hypothesis["params"]["policy_arch"] == "mlp_2x_tanh"
    assert level3_ppo_loop.structural_hypothesis_runnable(hypothesis)


@pytest.mark.unit
def test_v48_contact_conversion_reward_structure_lane_is_runnable() -> None:
    """v48 should be a named structural screen, not a track or retention change."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v48_v5_contact_conversion_reward_structure_from_loop110_3m"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["architecture"]["track_geometry_change"] == "forbidden"
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP110_V39_3M_CHECKPOINT
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V48_CONTACT_CONVERSION_REWARD_DECISION_PACKET
    )
    assert hypothesis["research_packet"] == level3_ppo_loop.V48_CONTACT_CONVERSION_REWARD_PACKET
    assert hypothesis["params"]["policy_arch"] == "mlp_2x_tanh"
    assert hypothesis["params"]["v27_teacher_kl_beta"] == 0.0
    assert hypothesis["params"]["reward_structure"] == "decoupled_frame_clearance"
    assert hypothesis["params"]["gate_frame_pressure_coef"] > 0.0
    assert hypothesis["params"]["missed_gate_penalty"] > 0.0
    assert "reward_structure" in hypothesis["architecture"]["changed_reward_numbers"]
    assert level3_ppo_loop.structural_hypothesis_runnable(hypothesis)


@pytest.mark.unit
def test_v49_hidden512_baseline_lane_is_runnable() -> None:
    """v49 should start a long-horizon hidden512 family without changing track/reward."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v49_v5_hidden512_mlp_warmstart_from_loop110_3m"
    ]

    assert hypothesis["proposal_name"].endswith("_60m")
    assert hypothesis["train_timesteps"] == 60_000_000
    assert hypothesis["checkpoint_interval"] == 5_000_000
    assert hypothesis["eval_milestones_m"] == "5,10,15,20,30,45,60"
    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["observation_layout"] == (
        level3_ppo_loop.LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    )
    assert hypothesis["architecture"]["track_geometry_change"] == "forbidden"
    assert hypothesis["architecture"]["capacity_family"] == "hidden512"
    assert hypothesis["architecture"]["changed_reward_numbers"] == []
    assert hypothesis["architecture"]["warmstart"]["source_hidden_dim"] == 256
    assert hypothesis["architecture"]["warmstart"]["target_hidden_dim"] == 512
    assert (
        hypothesis["architecture"]["followup_loop_policy"][
            "minimum_evaluated_family_trials_before_capacity_rejection"
        ]
        == 3
    )
    assert (
        "hidden512_reward_or_ppo_number_followup"
        in hypothesis["architecture"]["followup_loop_policy"][
            "allowed_hidden512_successors"
        ]
    )
    assert (
        "hidden512_same_hypothesis_90m_or_120m_maturation"
        in hypothesis["architecture"]["followup_loop_policy"][
            "allowed_hidden512_successors"
        ]
    )
    assert "long_horizon_rule" in hypothesis["architecture"]["followup_loop_policy"]
    assert "catastrophic_hold" in hypothesis["hypothesis"]["promotion_gate"]
    assert "parameter_survey_axes" in hypothesis["hypothesis"]
    assert "rollback" not in hypothesis["hypothesis"]["promotion_gate"]
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP110_V39_3M_CHECKPOINT
    assert hypothesis["allow_hidden_dim_warmstart"] is True
    assert hypothesis["allow_step_curve_maturation"] is True
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V49_HIDDEN512_BASELINE_DECISION_PACKET
    )
    assert hypothesis["research_packet"] == level3_ppo_loop.V49_HIDDEN512_BASELINE_PACKET

    params = hypothesis["params"]
    assert params["policy_arch"] == "mlp_2x_tanh"
    assert params["hidden_dim"] == 512
    assert params["v27_teacher_kl_beta"] == 0.0
    assert params["reward_structure"] == "legacy_staged"
    assert params["gate_stage_coef"] == 13.0
    assert params["gate_axis_coef"] == 24.0
    assert params["gate_front_bonus"] == 5.0
    assert params["gate_plane_bonus"] == 0.0
    assert params["gate_bonus"] == 200.0
    assert params["gate_back_bonus"] == 35.0
    assert params["finish_bonus"] == 175.0
    assert params["missed_gate_penalty"] == 0.0
    assert params["gate_frame_pressure_coef"] == 0.0
    assert params["time_penalty"] == 0.02
    assert level3_ppo_loop.structural_hypothesis_runnable(hypothesis)


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
