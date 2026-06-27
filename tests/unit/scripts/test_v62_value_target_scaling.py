import jax
import jax.numpy as jnp
import numpy as np

import scripts.train_v60_brax_ppo_smoke as ppo_smoke


def _zero_params() -> dict[str, dict[str, jax.Array]]:
    return {
        "trunk": {
            "w1": jnp.zeros((2, 3), dtype=jnp.float32),
            "b1": jnp.zeros((3,), dtype=jnp.float32),
            "w2": jnp.zeros((3, 3), dtype=jnp.float32),
            "b2": jnp.zeros((3,), dtype=jnp.float32),
        },
        "actor": {
            "w": jnp.zeros((3, 1), dtype=jnp.float32),
            "b": jnp.zeros((1,), dtype=jnp.float32),
            "log_std": jnp.zeros((1,), dtype=jnp.float32),
        },
        "critic": {
            "w": jnp.zeros((3, 1), dtype=jnp.float32),
            "b": jnp.zeros((1,), dtype=jnp.float32),
        },
    }


def test_value_target_scale_keeps_raw_gae_and_scales_critic_targets() -> None:
    transitions = {
        "obs": jnp.zeros((2, 1, 2), dtype=jnp.float32),
        "actions": jnp.zeros((2, 1, 1), dtype=jnp.float32),
        "logprobs": jnp.zeros((2, 1), dtype=jnp.float32),
        "values": jnp.zeros((2, 1), dtype=jnp.float32),
        "rewards": jnp.ones((2, 1), dtype=jnp.float32),
        "dones": jnp.zeros((2, 1), dtype=jnp.float32),
        "reward_mean": jnp.ones((2,), dtype=jnp.float32),
        "done_mean": jnp.zeros((2,), dtype=jnp.float32),
        "obs_abs_mean": jnp.zeros((2,), dtype=jnp.float32),
        "action_abs_mean": jnp.zeros((2,), dtype=jnp.float32),
        "action_clip_fraction": jnp.zeros((2,), dtype=jnp.float32),
        "action_any_dim_clipped_fraction": jnp.zeros((2,), dtype=jnp.float32),
        "action_sample_env_delta_abs_mean": jnp.zeros((2,), dtype=jnp.float32),
        "action_raw_vs_env_logprob_abs_mean": jnp.zeros((2,), dtype=jnp.float32),
        "action_logprob_env_consistency_error": jnp.zeros((2,), dtype=jnp.float32),
        "command_position_error": jnp.zeros((2,), dtype=jnp.float32),
        "command_velocity_error": jnp.zeros((2,), dtype=jnp.float32),
        "cross_track_error": jnp.zeros((2,), dtype=jnp.float32),
        "action_delta_penalty": jnp.zeros((2,), dtype=jnp.float32),
    }

    batch, summary = ppo_smoke.compute_advantage_batch(
        _zero_params(), jnp.zeros((1, 2), dtype=jnp.float32), transitions, 1.0, 1.0, 10.0
    )

    np.testing.assert_allclose(np.asarray(batch["advantages"]), [2.0, 1.0])
    np.testing.assert_allclose(np.asarray(batch["returns"]), [0.2, 0.1])
    np.testing.assert_allclose(np.asarray(summary["returns_mean"]), 1.5)
    np.testing.assert_allclose(np.asarray(summary["value_targets_mean"]), 0.15)
    np.testing.assert_allclose(np.asarray(summary["value_target_scale"]), 10.0)
