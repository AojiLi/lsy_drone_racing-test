"""Tests for the Level3 v37 GRU transfer preflight lane."""

from __future__ import annotations

import pytest

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    POLICY_ARCH_RECURRENT_ACTOR_GRU256,
)
from scripts import level3_ppo_loop


@pytest.mark.unit
def test_loop_registers_v37_gru_transfer_as_preflight_hold() -> None:
    """v37 must be explicit, track-safe, and held until transfer support exists."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v37_gru_transfer_memory_structure_from_loop101"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["observation_layout"] == LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V37_GRU_TRANSFER_DECISION_PACKET
    )
    assert hypothesis["requires_training_support"] == "mlp_to_gru_transfer_support"
    assert "mlp_to_gru_transfer_support" not in (
        level3_ppo_loop.SUPPORTED_TRAINING_STRUCTURES
    )

    architecture = hypothesis["architecture"]
    assert architecture["track_geometry_change"] == "forbidden"
    assert architecture["policy_arch"] == POLICY_ARCH_RECURRENT_ACTOR_GRU256
    assert architecture["transfer"]["source_checkpoint"] == (
        level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    )

    params = hypothesis["params"]
    assert params["policy_arch"] == POLICY_ARCH_RECURRENT_ACTOR_GRU256
    assert params["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert params["track_generator_profile"] == "default"
    assert params["recurrent_hidden_dim"] == 256
    assert params["recurrent_sequence_len"] == hypothesis["num_steps"]
