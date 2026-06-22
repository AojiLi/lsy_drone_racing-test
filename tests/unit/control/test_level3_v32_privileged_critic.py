"""Tests for Level3 v32 asymmetric privileged-Critic support."""

from __future__ import annotations

import torch

from lsy_drone_racing.control.ppo_level3_inference import PPOAgent
from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    checkpoint_critic_observation_mode,
    make_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Agent,
    expand_checkpoint_critic_input_dim,
)
from scripts import level3_ppo_loop


def test_privileged_critic_checkpoint_records_training_only_mode() -> None:
    """Asymmetric checkpoints must say that only the Critic uses privileged state."""
    agent = Agent((68,), (4,), hidden_dim=8, critic_obs_shape=(135,))

    checkpoint = make_checkpoint(
        agent.state_dict(),
        hidden_dim=8,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        critic_observation_mode=CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
        actor_observation_dim=68,
        critic_observation_dim=135,
    )

    assert checkpoint_critic_observation_mode(checkpoint) == (
        CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1
    )
    assert checkpoint["actor_observation_dim"] == 68
    assert checkpoint["critic_observation_dim"] == 135


def test_privileged_critic_warmstart_preserves_actor_outputs() -> None:
    """Zero-padding only the Critic input must leave Actor behavior unchanged."""
    torch.manual_seed(32)
    source = Agent((68,), (4,), hidden_dim=8)
    target = Agent((68,), (4,), hidden_dim=8, critic_obs_shape=(135,))

    expanded_state = expand_checkpoint_critic_input_dim(source.state_dict(), target)
    target.load_state_dict(expanded_state)

    obs = torch.randn((16, 68), dtype=torch.float32)
    critic_obs = torch.randn((16, 135), dtype=torch.float32)
    with torch.no_grad():
        source_action, source_logprob, source_entropy, _ = source.get_action_and_value(
            obs,
            deterministic=True,
        )
        target_action, target_logprob, target_entropy, _ = target.get_action_and_value(
            obs,
            deterministic=True,
            critic_x=critic_obs,
        )

    torch.testing.assert_close(target_action, source_action)
    torch.testing.assert_close(target_logprob, source_logprob)
    torch.testing.assert_close(target_entropy, source_entropy)
    assert target.critic[0].weight.shape[1] == 135
    torch.testing.assert_close(target.critic[0].weight[:, 68:], torch.zeros((8, 67)))


def test_inference_can_load_privileged_checkpoint_actor_only() -> None:
    """Deployment should ignore Critic-only privileged weights."""
    training_agent = Agent((68,), (4,), hidden_dim=8, critic_obs_shape=(135,))
    checkpoint = make_checkpoint(
        training_agent.state_dict(),
        hidden_dim=8,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        critic_observation_mode=CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
        actor_observation_dim=68,
        critic_observation_dim=135,
    )

    inference_agent = PPOAgent((68,), (4,), hidden_dim=8)
    deploy_state = {
        key: value
        for key, value in checkpoint["model_state_dict"].items()
        if not key.startswith("critic.")
    }
    missing, unexpected = inference_agent.load_state_dict(deploy_state, strict=False)

    assert not unexpected
    assert set(missing) == {
        "critic.0.weight",
        "critic.0.bias",
        "critic.2.weight",
        "critic.2.bias",
        "critic.4.weight",
        "critic.4.bias",
    }


def test_loop_registers_and_passes_v32_critic_observation_mode() -> None:
    """The orchestrator must pass critic_observation_mode through Fire."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v32_asymmetric_privileged_critic_clean_ppo_5m"
    ]

    assert hypothesis["params"]["critic_observation_mode"] == (
        CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1
    )
    assert "critic_observation_mode" in level3_ppo_loop.FIRE_PARAM_KEYS
    assert (
        CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1
        in level3_ppo_loop.STRING_PARAM_CHOICES["critic_observation_mode"]
    )
