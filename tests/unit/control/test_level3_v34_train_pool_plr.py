"""Tests for the Level3 v34 offline train-pool PLR lane."""

from __future__ import annotations

from lsy_drone_racing.control.train_CleanRL_ppo_level3 import TRACK_GENERATOR_PROFILES
from scripts import level3_ppo_loop


def _expand_range(start: int, stop: int) -> set[int]:
    return set(range(start, stop + 1))


def test_v34_track_profile_uses_train_pool_only_low_probability_replay() -> None:
    """The offline PLR profile must not leak dev, validation, or final seeds."""
    profile = TRACK_GENERATOR_PROFILES["v34_lowprob_train_pool_bounds_plr"]
    replay_seeds = {int(seed) for seed in profile["replay_seeds"]}
    forbidden = (
        _expand_range(1, 20)
        | _expand_range(101, 200)
        | _expand_range(1001, 1200)
    )

    assert profile["replay_seed_probability"] == 0.08
    assert profile["hard_case_probability"] == 0.0
    assert replay_seeds
    assert not (replay_seeds & forbidden)


def test_loop_registers_v34_as_named_offline_plr_lane() -> None:
    """The orchestrator should launch v34 only as an explicit structural lane."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v34_lowprob_train_pool_plr_from_loop101"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    assert hypothesis["requires_training_support"] == "offline_train_pool_plr_support"
    assert hypothesis["params"]["track_generator_profile"] == (
        "v34_lowprob_train_pool_bounds_plr"
    )
    assert hypothesis["params"]["gate_phase_reset_prob"] == 0.45
    assert hypothesis["architecture"]["changed_reward_numbers"] == []
    assert "v34_lowprob_train_pool_bounds_plr" in (
        level3_ppo_loop.STRING_PARAM_CHOICES["track_generator_profile"]
    )
