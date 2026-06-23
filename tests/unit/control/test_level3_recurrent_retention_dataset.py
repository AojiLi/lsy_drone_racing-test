"""Tests for sequence-aware Level3 recurrent teacher-retention datasets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import POLICY_ARCH_RECURRENT_ACTOR_GRU256
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Args,
    RecurrentActorAgent,
    load_v27_retention_dataset,
    v27_recurrent_dataset_retention_loss,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_recurrent_retention_dataset_loads_sequences_and_backprops(
    tmp_path: Path,
) -> None:
    """True-GRU PPO retention should sample episode sequences, not flat states."""
    rng = np.random.default_rng(44)
    obs_dim = 91
    action_dim = 4
    samples_per_seed = 10
    seeds = np.repeat(np.arange(3, dtype=np.int32), samples_per_seed)
    episode_steps = np.tile(np.arange(samples_per_seed, dtype=np.int32), 3)
    student_obs = rng.normal(0.0, 0.5, size=(seeds.size, obs_dim)).astype(np.float32)
    teacher_mean = np.tanh(student_obs[:, :action_dim]).astype(np.float32)
    teacher_logstd = np.full_like(teacher_mean, -1.0, dtype=np.float32)
    dataset_path = tmp_path / "retention_sequences.npz"
    np.savez_compressed(
        dataset_path,
        student_obs=student_obs,
        teacher_action_mean=teacher_mean,
        teacher_action_logstd=teacher_logstd,
        seed=seeds,
        episode_step=episode_steps,
    )

    args = Args.create(
        policy_arch=POLICY_ARCH_RECURRENT_ACTOR_GRU256,
        v27_teacher_kl_beta=0.1,
        v27_retention_dataset_path=str(dataset_path),
        v27_retention_batch_size=12,
        recurrent_sequence_len=6,
        num_steps=6,
    )
    dataset = load_v27_retention_dataset(
        args,
        obs_shape=(obs_dim,),
        action_shape=(action_dim,),
        device=torch.device("cpu"),
    )
    assert dataset is not None
    assert dataset.num_samples == seeds.size
    assert dataset.num_sequences == 3

    agent = RecurrentActorAgent((obs_dim,), (action_dim,))
    teacher_kl, teacher_action_mse, teacher_agreement, sample_size = (
        v27_recurrent_dataset_retention_loss(
            agent,
            dataset,
            sequence_len=args.recurrent_sequence_len,
            batch_size=args.v27_retention_batch_size,
        )
    )
    assert sample_size == 12
    assert torch.isfinite(teacher_kl)
    assert torch.isfinite(teacher_action_mse)
    assert 0.0 <= float(teacher_agreement.item()) <= 1.0

    teacher_kl.backward()
    grad_norm = sum(
        float(param.grad.detach().abs().sum().item())
        for param in agent.parameters()
        if param.grad is not None
    )
    assert grad_norm > 0.0
