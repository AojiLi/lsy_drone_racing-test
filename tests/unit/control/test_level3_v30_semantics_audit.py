"""Audit gates for the Level3 v30 semantics review."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import torch
from torch.distributions.normal import Normal

from lsy_drone_racing.control import train_CleanRL_ppo_level3 as level3_ppo
from lsy_drone_racing.envs import race_core
from scripts import evaluate_level2_selected_ppo, level3_ppo_loop

ROOT = Path(__file__).parents[3]
V30_PACKET = (
    ROOT
    / "experiments/level3_ppo_loop/decisions/2026-06-22_v30_semantics_audit_approved.md"
)


def _zero_actor(agent: level3_ppo.Agent) -> None:
    """Make the policy mean exactly zero so sampled clipping is easy to detect."""
    with torch.no_grad():
        for module in agent.actor_mean:
            if isinstance(module, torch.nn.Linear):
                module.weight.zero_()
                module.bias.zero_()
        agent.actor_logstd.fill_(0.0)


@pytest.mark.unit
def test_v30_packet_is_audit_only_and_requires_loop052_parity() -> None:
    """The approved v30 packet must not authorize a training launch."""
    packet = V30_PACKET.read_text()

    assert "approved for code audit and tests only" in packet
    assert "does not authorize\ntraining" in packet
    assert "final-target `level3.toml`" in packet
    assert "`validation_unseen` seeds" in packet
    assert "level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt" in packet
    assert "Launch loop091 or any other new training chunk" in packet


@pytest.mark.unit
def test_loop_state_guard_knows_v30_semantics_hold_key() -> None:
    """A future state.json v30 hold must be recognized before training."""
    source = inspect.getsource(level3_ppo_loop.active_state_training_hold)

    assert "level3_v30_semantics_audit_hold" in source


@pytest.mark.unit
def test_action_clipping_changes_ppo_logprob_for_out_of_bounds_samples() -> None:
    """PPO currently records log-probs for samples that wrappers may clip before simulation."""
    torch.manual_seed(30)
    agent = level3_ppo.Agent((68,), (4,), hidden_dim=8)
    _zero_actor(agent)

    obs = torch.zeros((4096, 68), dtype=torch.float32)
    action, logged_logprob, _entropy, _value = agent.get_action_and_value(obs)
    clipped = action.clamp(-1.0, 1.0)
    clipped_any = torch.any(action != clipped, dim=1)

    assert clipped_any.float().mean().item() > 0.50

    action_mean = agent.actor_mean(obs)
    action_std = torch.exp(agent.actor_logstd.expand_as(action_mean))
    clipped_logprob = Normal(action_mean, action_std).log_prob(clipped).sum(1)

    max_abs_logprob_delta = torch.max(
        torch.abs(logged_logprob[clipped_any] - clipped_logprob[clipped_any])
    ).item()
    assert max_abs_logprob_delta > 0.10


@pytest.mark.unit
def test_geometry_fallback_is_not_a_true_termination_reason() -> None:
    """The evaluator can infer bounds_or_ground from distance alone."""
    result = evaluate_level2_selected_ppo.classify_geometry(
        pos=torch.tensor([100.0, 100.0, 100.0]).numpy(),
        gates_pos=torch.zeros((1, 3)).numpy(),
        gates_quat=torch.tensor([[0.0, 0.0, 0.0, 1.0]]).numpy(),
        obstacles_pos=torch.zeros((1, 3)).numpy(),
        target_gate=0,
    )

    assert result["likely_object"] == "bounds_or_ground"
    assert result["nearest_object_distance_m"] > 0.25


@pytest.mark.unit
def test_finish_updates_target_gate_before_disabled_check() -> None:
    """Passing the final gate should be terminal in the same transition."""
    source = inspect.getsource(race_core.RaceCoreEnv.build_step_fn)

    assert source.index("_update_target_gates") < source.index("_update_disabled_drones")


@pytest.mark.unit
def test_finish_bonus_is_transition_event_not_persistent_state() -> None:
    """Finish reward should use the -1 transition, not every target_gate < 0 state."""
    source = inspect.getsource(level3_ppo.Level2RaceReward._reward_components)

    assert "finished = (target_gate < 0) & (self._prev_target_gate >= 0)" in source


@pytest.mark.unit
def test_autoreset_uses_current_done_flags_not_previous_marked_for_reset() -> None:
    """Rollout collection should not include a dummy step after terminal state."""
    source = inspect.getsource(race_core.RaceCoreEnv.build_step_fn)

    assert "marked_for_reset = data.marked_for_reset" not in source


@pytest.mark.unit
def test_race_observation_has_per_slot_done_reset_hook() -> None:
    """Flattened observation history and last_action need per-slot episode reset."""
    source = inspect.getsource(level3_ppo.RaceObservation)

    assert "def _reset_episode_state" in source
    assert "terminations" in source
    assert "truncations" in source


@pytest.mark.unit
def test_observation_delay_reset_uses_true_post_reset_observation() -> None:
    """Delay buffers for done slots should not be rebuilt from stale terminal observations."""
    source = inspect.getsource(level3_ppo.ObservationLatencyNoise.step)

    assert "reset_observations" in source or "final_observation" in source


@pytest.mark.unit
def test_evaluator_records_true_termination_reason() -> None:
    """Crash taxonomy should consume env-provided reasons, not only geometry guesses."""
    source = inspect.getsource(evaluate_level2_selected_ppo)

    assert "termination_reason" in source
