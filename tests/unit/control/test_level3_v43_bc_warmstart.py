"""Tests for the Level3 v43 GRU/v10 behavior-cloning warmstart support."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import numpy as np
import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    POLICY_ARCH_RECURRENT_ACTOR_GRU256,
    checkpoint_policy_arch,
    unpack_checkpoint,
)
from scripts.train_level3_v43_bc_warmstart import load_sequence_dataset, train_bc

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_v43_bc_warmstart_trains_and_writes_recurrent_v10_checkpoint(
    tmp_path: Path,
) -> None:
    """The v43 BC preflight must create a tagged GRU/v10 checkpoint."""
    rng = np.random.default_rng(43)
    obs_dim = 91
    action_dim = 4
    samples_per_seed = 12
    seeds = np.repeat(np.arange(4, dtype=np.int32), samples_per_seed)
    steps = np.tile(np.arange(samples_per_seed, dtype=np.int32), 4)
    obs = rng.normal(0.0, 0.4, size=(seeds.size, obs_dim)).astype(np.float32)
    teacher_mean = np.tanh(obs[:, :action_dim] * 0.7).astype(np.float32)
    teacher_logstd = np.full_like(teacher_mean, -1.0, dtype=np.float32)
    dataset_path = tmp_path / "synthetic_v43_dataset.npz"
    np.savez_compressed(
        dataset_path,
        student_obs=obs,
        teacher_action_mean=teacher_mean,
        teacher_action_logstd=teacher_logstd,
        seed=seeds,
        episode_step=steps,
        metadata_json=np.asarray(
            json.dumps({"purpose": "unit test v43 bc"}),
            dtype=np.str_,
        ),
    )

    dataset = load_sequence_dataset(dataset_path)
    checkpoint_path = tmp_path / "v43_bc.ckpt"
    metrics_path = tmp_path / "metrics.json"
    metrics = train_bc(
        dataset,
        out_path=checkpoint_path,
        metrics_path=metrics_path,
        observation_layout=LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
        hidden_dim=256,
        recurrent_hidden_dim=256,
        sequence_len=6,
        batch_size=4,
        steps=80,
        lr=1e-3,
        seed=43,
        action_rp_limit_deg=90.0,
        action_lowpass_alpha=1.0,
        device=torch.device("cpu"),
    )

    assert checkpoint_path.exists()
    assert metrics_path.exists()
    assert metrics["final_teacher_action_mse"] < metrics["initial_teacher_action_mse"]
    assert metrics["final_teacher_kl"] < metrics["initial_teacher_kl"]

    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    state_dict, observation_layout = unpack_checkpoint(checkpoint)
    assert checkpoint_policy_arch(checkpoint, state_dict) == POLICY_ARCH_RECURRENT_ACTOR_GRU256
    assert observation_layout == LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT
    assert checkpoint["recurrent_hidden_dim"] == 256
    assert checkpoint["recurrent_sequence_len"] == 6
    assert checkpoint["v43_bc_warmstart"]["dataset"]["num_sequences"] == 4
