"""Tests for random track generation helpers."""

from __future__ import annotations

import jax
import jax.numpy as jp
import pytest

from lsy_drone_racing.envs.randomize import build_random_track_fn


@pytest.mark.unit
def test_replay_seed_track_generation_accepts_legacy_prng_key() -> None:
    """Replay-seed generation should not mix typed and legacy JAX key dtypes."""
    generate = build_random_track_fn(
        jp.array([0.8, 0.8, 0.8, 0.8], dtype=jp.float32),
        jp.array([0.5, 0.5, 0.5, 0.5], dtype=jp.float32),
        jp.array([-3.0, -3.0, 0.0], dtype=jp.float32),
        jp.array([3.0, 3.0, 2.5], dtype=jp.float32),
        replay_seed_probability=1.0,
        replay_seeds=(2114, 2120),
        hard_case_probability=0.0,
    )

    gates_pos, gates_quat, obstacles_pos = generate(jax.random.PRNGKey(0))

    assert gates_pos.shape == (4, 3)
    assert gates_quat.shape == (4, 4)
    assert obstacles_pos.shape == (4, 3)
