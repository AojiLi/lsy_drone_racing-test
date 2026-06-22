"""Tests for Level3 v31b observation and return normalization support."""

from __future__ import annotations

import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    checkpoint_obs_normalization,
    checkpoint_return_normalization,
    make_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import Agent, RunningMeanStd


def test_running_mean_std_round_trips_vector_values() -> None:
    """Observation normalization metadata should restore the same transform."""
    device = torch.device("cpu")
    batch = torch.tensor([[1.0, 3.0], [3.0, 7.0], [5.0, 11.0]], device=device)

    rms = RunningMeanStd((2,), device=device)
    rms.update(batch)

    normalized = rms.normalize(batch, clip=10.0)
    restored = rms.denormalize(normalized)
    torch.testing.assert_close(restored, batch, atol=1e-4, rtol=1e-4)

    restored_rms = RunningMeanStd((2,), device=device, state=rms.metadata(enabled=True, clip=10.0))
    torch.testing.assert_close(restored_rms.mean, rms.mean)
    torch.testing.assert_close(restored_rms.var, rms.var)
    assert float(restored_rms.count.item()) == float(rms.count.item())


def test_running_mean_std_handles_scalar_returns() -> None:
    """Return normalization uses scalar running statistics."""
    device = torch.device("cpu")
    returns = torch.tensor([10.0, 20.0, 30.0], device=device)

    rms = RunningMeanStd((), device=device)
    rms.update(returns)

    normalized = rms.normalize(returns, clip=10.0)
    restored = rms.denormalize(normalized)
    torch.testing.assert_close(restored, returns, atol=1e-4, rtol=1e-4)
    assert rms.mean.shape == torch.Size([])
    assert rms.var.shape == torch.Size([])


def test_level3_checkpoint_preserves_normalization_metadata() -> None:
    """Saved checkpoints must carry frozen eval-time normalization stats."""
    state_dict = Agent((68,), (4,), hidden_dim=8).state_dict()
    obs_norm = {
        "enabled": True,
        "mean": [0.0] * 68,
        "var": [1.0] * 68,
        "count": 123.0,
        "clip": 10.0,
        "epsilon": 1e-4,
    }
    return_norm = {
        "enabled": True,
        "mean": 12.0,
        "var": 9.0,
        "count": 123.0,
        "clip": 10.0,
        "epsilon": 1e-4,
    }

    checkpoint = make_checkpoint(
        state_dict,
        hidden_dim=8,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        obs_normalization=obs_norm,
        return_normalization=return_norm,
    )

    assert checkpoint_obs_normalization(checkpoint) == obs_norm
    assert checkpoint_return_normalization(checkpoint) == return_norm
