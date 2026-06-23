"""Tests for the Level3 v36 online competence-gated level replay lane."""

from __future__ import annotations

import inspect

import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    LEVEL_REPLAY_PROFILES,
    Args,
    OnlineLevelReplayCurriculum,
    make_envs,
    train_ppo,
    wrapped_instance,
)
from scripts import level3_ppo_loop


def _expand_range(start: int, stop: int) -> set[int]:
    return set(range(start, stop + 1))


@pytest.mark.unit
def test_v36_level_replay_profile_uses_train_pool_only() -> None:
    """The dynamic replay profile must not leak validation or final eval seeds."""
    profile = LEVEL_REPLAY_PROFILES["v36_train_pool_bounds_gate0_gate2"]
    replay_seeds = {int(seed) for seed in profile["replay_seeds"]}
    forbidden = (
        _expand_range(1, 20)
        | _expand_range(101, 200)
        | _expand_range(1001, 1200)
    )

    assert replay_seeds
    assert not (replay_seeds & forbidden)


@pytest.mark.unit
def test_online_level_replay_args_validate_schedule() -> None:
    """Competence-gated replay should require a bounded nonzero schedule."""
    Args.create(
        online_level_replay_profile="v36_train_pool_bounds_gate0_gate2",
        online_level_replay_prob=0.08,
        online_level_replay_competence_enabled=True,
        online_level_replay_competence_start_prob=0.03,
        online_level_replay_competence_step_prob=0.01,
    )

    with pytest.raises(ValueError, match="online_level_replay_prob"):
        Args.create(
            online_level_replay_profile="v36_train_pool_bounds_gate0_gate2",
            online_level_replay_prob=0.0,
        )
    with pytest.raises(ValueError, match="requires online_level_replay_profile"):
        Args.create(online_level_replay_competence_enabled=True)
    with pytest.raises(ValueError, match="start_prob"):
        Args.create(
            online_level_replay_profile="v36_train_pool_bounds_gate0_gate2",
            online_level_replay_prob=0.08,
            online_level_replay_competence_enabled=True,
            online_level_replay_competence_start_prob=0.2,
        )


@pytest.mark.unit
def test_online_level_replay_wrapper_uses_initial_probability() -> None:
    """The replay wrapper should start below max pressure and remain adjustable."""
    envs = make_envs(
        config="level3.toml",
        num_envs=4,
        jax_device="cpu",
        torch_device=torch.device("cpu"),
        coefs={
            "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "n_obs": 2,
            "online_level_replay_profile": "v36_train_pool_bounds_gate0_gate2",
            "online_level_replay_initial_prob": 0.03,
        },
    )
    try:
        replay = wrapped_instance(envs, OnlineLevelReplayCurriculum)
        assert replay is not None
        assert replay.level_replay_prob == pytest.approx(0.03)

        replay.set_probability(0.05)
        assert replay.level_replay_prob == pytest.approx(0.05)
    finally:
        envs.close()


@pytest.mark.unit
def test_train_loop_logs_and_updates_online_level_replay() -> None:
    """The PPO loop should update replay pressure from rollout race metrics."""
    source = inspect.getsource(train_ppo)

    assert "online_level_replay_competence_enabled" in source
    assert "curriculum/online_level_replay_prob" in source
    assert "online_level_replay_competence_gate_met" in source
    assert "set_probability(next_online_level_replay_prob)" in source


@pytest.mark.unit
def test_loop_registers_v36_online_level_replay_lane() -> None:
    """The orchestrator should launch v36 only as an explicit structural lane."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v36_online_competence_gated_level_replay_from_loop101"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    assert hypothesis["requires_training_support"] == (
        "online_competence_gated_level_replay_support"
    )
    assert hypothesis["params"]["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert hypothesis["params"]["track_generator_profile"] == "default"
    assert hypothesis["params"]["online_level_replay_profile"] == (
        "v36_train_pool_bounds_gate0_gate2"
    )
    assert hypothesis["params"]["online_level_replay_prob"] == pytest.approx(0.08)
    assert hypothesis["params"]["online_level_replay_competence_enabled"] is True
    assert hypothesis["architecture"]["changed_reward_numbers"] == []
    assert "online_competence_gated_level_replay_support" in (
        level3_ppo_loop.SUPPORTED_TRAINING_STRUCTURES
    )

    for key in (
        "online_level_replay_profile",
        "online_level_replay_prob",
        "online_level_replay_competence_enabled",
        "online_level_replay_competence_start_prob",
        "online_level_replay_competence_step_prob",
        "online_level_replay_competence_min_passed_gate_rate",
        "online_level_replay_competence_min_finished_rate",
        "online_level_replay_competence_max_crashed_rate",
    ):
        assert key in level3_ppo_loop.FIRE_PARAM_KEYS
