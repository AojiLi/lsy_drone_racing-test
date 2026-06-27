"""Run a minimal pure-JAX PPO smoke test for the v60 command tracker."""

from __future__ import annotations

import argparse
import math
import os
import pickle
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import jax
import jax.numpy as jnp
import numpy as np
import optax

import scripts.benchmark_v60_brax_rollout as v60_rollout

ROOT = Path(__file__).parents[1]
DEFAULT_CHECKPOINT = (
    ROOT / "lsy_drone_racing/control/checkpoints/v62_brax_ppo_smoke/" / "v62_brax_ppo_smoke.pkl"
)
PYTORCH_FAST_PATH_STEPS_PER_S = 39_800.0
LOG_2PI = float(np.log(2.0 * np.pi))
LOG_2PI_E = float(np.log(2.0 * np.pi * np.e))
LOG_2 = float(np.log(2.0))
TANH_EPS = 1e-6
ACTION_DISTRIBUTIONS = ("clipped_gaussian", "tanh_squashed_gaussian")
COMMAND_REWARD_OVERRIDE_NAMES = frozenset(
    {
        "pos_error_coef",
        "vel_error_coef",
        "heading_coef",
        "action_coef",
        "action_delta_coef",
        "progress_bonus",
        "trajectory_cross_track_coef",
        "trajectory_along_speed_coef",
        "trajectory_reverse_speed_coef",
        "trajectory_overshoot_coef",
        "semantic_brake_speed_coef",
        "semantic_slow_speed_coef",
        "semantic_slow_stop_coef",
        "semantic_recover_speed_coef",
        "crash_penalty",
    }
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--seed", type=int, default=26101)
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--total-timesteps", type=int, default=131_072)
    parser.add_argument("--num-minibatches", type=int, default=4)
    parser.add_argument("--update-epochs", type=int, default=1)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--clip-coef", type=float, default=0.2)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--vf-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--initial-log-std", type=float, default=-2.0)
    parser.add_argument(
        "--value-target-scale",
        type=float,
        default=1.0,
        help=("Scale critic targets by this positive value while keeping GAE in raw reward units."),
    )
    parser.add_argument(
        "--command-vel-error-coef",
        type=float,
        help="Override the generic ReferenceCommandReward velocity-error coefficient.",
    )
    parser.add_argument(
        "--reward-coeff",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help=(
            "Override one clean generic command-tracker reward coefficient. May be "
            "repeated. Gate, obstacle, race, finish, and stage coefficients are not allowed."
        ),
    )
    parser.add_argument(
        "--action-distribution", choices=ACTION_DISTRIBUTIONS, default="tanh_squashed_gaussian"
    )
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument(
        "--command-generator-profile",
        choices=v60_rollout.COMMAND_GENERATOR_PROFILES,
        default="default",
        help="Command reference generator profile; default preserves the original v60 generator.",
    )
    parser.add_argument("--eval-rollouts", type=int, default=2)
    parser.add_argument("--checkpoint-path", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--wandb-enabled", action="store_true")
    parser.add_argument("--wandb-project-name", default="ADR-PPO-Racing-Level3")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-run-name")
    parser.add_argument("--wandb-run-id")
    parser.add_argument("--wandb-mode", default="offline")
    parser.add_argument("--jax-device", default="gpu")
    return parser.parse_args()


def command_reward_coefficients(args: argparse.Namespace) -> dict[str, float]:
    """Return explicit command-reward coefficient overrides for this run."""
    coefficients: dict[str, float] = {}
    for raw in getattr(args, "reward_coeff", []) or []:
        if "=" not in raw:
            raise ValueError(f"--reward-coeff must use NAME=VALUE, got {raw!r}.")
        name, value_text = raw.split("=", 1)
        name = name.strip()
        if name not in COMMAND_REWARD_OVERRIDE_NAMES:
            allowed = ", ".join(sorted(COMMAND_REWARD_OVERRIDE_NAMES))
            raise ValueError(f"Unsupported clean command reward coefficient {name!r}. Allowed: {allowed}")
        value = float(value_text.strip())
        if not math.isfinite(value):
            raise ValueError(f"Reward coefficient {name!r} must be finite, got {value_text!r}.")
        coefficients[name] = value
    if args.command_vel_error_coef is not None:
        vel_value = float(args.command_vel_error_coef)
        existing = coefficients.get("vel_error_coef")
        if existing is not None and not math.isclose(existing, vel_value):
            raise ValueError(
                "--command-vel-error-coef conflicts with --reward-coeff vel_error_coef=..."
            )
        coefficients["vel_error_coef"] = vel_value
    return coefficients


def init_actor_critic_params(
    key: jax.Array, *, obs_dim: int, hidden_dim: int, action_dim: int, initial_log_std: float
) -> dict[str, Any]:
    """Initialize a compact actor-critic MLP."""
    keys = jax.random.split(key, 6)
    return {
        "trunk": {
            "w1": jax.random.normal(keys[0], (obs_dim, hidden_dim), dtype=jnp.float32) * 0.05,
            "b1": jnp.zeros((hidden_dim,), dtype=jnp.float32),
            "w2": jax.random.normal(keys[1], (hidden_dim, hidden_dim), dtype=jnp.float32) * 0.05,
            "b2": jnp.zeros((hidden_dim,), dtype=jnp.float32),
        },
        "actor": {
            "w": jax.random.normal(keys[2], (hidden_dim, action_dim), dtype=jnp.float32) * 0.01,
            "b": jnp.zeros((action_dim,), dtype=jnp.float32),
            "log_std": jnp.full((action_dim,), float(initial_log_std), dtype=jnp.float32),
        },
        "critic": {
            "w": jax.random.normal(keys[3], (hidden_dim, 1), dtype=jnp.float32) * 0.01,
            "b": jnp.zeros((1,), dtype=jnp.float32),
        },
    }


def actor_critic_apply(
    params: dict[str, Any], obs: jax.Array
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Return bounded action mean, log std, and scalar value.

    This preserves the original clipped-Gaussian policy interface. Newer
    squashed-Gaussian code uses `actor_critic_apply_raw`.
    """
    raw_mean, log_std, value = actor_critic_apply_raw(params, obs)
    return jnp.tanh(raw_mean).astype(jnp.float32), log_std, value


def actor_critic_apply_raw(
    params: dict[str, Any], obs: jax.Array
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Return pre-squash action mean, log std, and scalar value."""
    hidden = jnp.tanh(obs @ params["trunk"]["w1"] + params["trunk"]["b1"])
    hidden = jnp.tanh(hidden @ params["trunk"]["w2"] + params["trunk"]["b2"])
    mean = hidden @ params["actor"]["w"] + params["actor"]["b"]
    value = jnp.squeeze(hidden @ params["critic"]["w"] + params["critic"]["b"], axis=-1)
    log_std = params["actor"]["log_std"]
    return mean.astype(jnp.float32), log_std.astype(jnp.float32), value.astype(jnp.float32)


def gaussian_logprob(action: jax.Array, mean: jax.Array, log_std: jax.Array) -> jax.Array:
    """Log probability under a diagonal Gaussian."""
    inv_std = jnp.exp(-log_std)
    normalized = (action - mean) * inv_std
    return -0.5 * jnp.sum(jnp.square(normalized) + 2.0 * log_std + LOG_2PI, axis=-1)


def gaussian_entropy(log_std: jax.Array) -> jax.Array:
    """Entropy for a diagonal Gaussian."""
    return 0.5 * jnp.sum(LOG_2PI_E + 2.0 * log_std)


def tanh_log_det_jacobian(pre_tanh_action: jax.Array) -> jax.Array:
    """Stable log |det d tanh(x) / dx| per action dimension."""
    return 2.0 * (LOG_2 - pre_tanh_action - jax.nn.softplus(-2.0 * pre_tanh_action))


def atanh_clipped(action: jax.Array) -> jax.Array:
    """Numerically safe inverse tanh for bounded env actions."""
    clipped = jnp.clip(action, -1.0 + TANH_EPS, 1.0 - TANH_EPS)
    return 0.5 * (jnp.log1p(clipped) - jnp.log1p(-clipped))


def tanh_squashed_gaussian_logprob_from_raw(
    pre_tanh_action: jax.Array, mean: jax.Array, log_std: jax.Array
) -> jax.Array:
    """Logprob of tanh(pre_tanh_action) under a squashed Gaussian."""
    raw_logprob = gaussian_logprob(pre_tanh_action, mean, log_std)
    correction = jnp.sum(tanh_log_det_jacobian(pre_tanh_action), axis=-1)
    return raw_logprob - correction


def tanh_squashed_gaussian_logprob(
    action: jax.Array, mean: jax.Array, log_std: jax.Array
) -> jax.Array:
    """Logprob of a bounded action under a tanh-squashed Gaussian."""
    return tanh_squashed_gaussian_logprob_from_raw(atanh_clipped(action), mean, log_std)


def action_logprob(
    action: jax.Array, mean: jax.Array, log_std: jax.Array, action_distribution: str
) -> jax.Array:
    """Return policy logprob for an env action under the selected distribution."""
    if action_distribution == "tanh_squashed_gaussian":
        return tanh_squashed_gaussian_logprob(action, mean, log_std)
    return gaussian_logprob(action, mean, log_std)


def policy_apply_for_distribution(
    params: dict[str, Any], obs: jax.Array, action_distribution: str
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Return the policy location matching the selected action distribution."""
    if action_distribution == "tanh_squashed_gaussian":
        return actor_critic_apply_raw(params, obs)
    return actor_critic_apply(params, obs)


def deterministic_env_action(mean: jax.Array, action_distribution: str) -> jax.Array:
    """Return the deterministic env action for a policy location."""
    if action_distribution == "tanh_squashed_gaussian":
        return jnp.tanh(mean)
    return jnp.clip(mean, -1.0, 1.0)


def action_logprob_mode(action_distribution: str) -> str:
    """Return a metadata label for the selected action/logprob path."""
    if action_distribution == "tanh_squashed_gaussian":
        return "tanh_squashed_gaussian_logprob_with_jacobian"
    return "env_clipped_action_gaussian_logprob"


def sample_env_action(
    mean: jax.Array, log_std: jax.Array, key: jax.Array, action_distribution: str
) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array]:
    """Sample an action and return the exact bounded action used by the env.

    PPO stores/logprobs the env action. For `tanh_squashed_gaussian`, `mean`
    and `action_sample` live in pre-tanh space and `action_for_env` is the
    squashed action. For `clipped_gaussian`, `action_sample` is clipped before
    execution and the clipped env action is used for the stored logprob.
    """
    action_sample = mean + jnp.exp(log_std) * jax.random.normal(key, mean.shape)
    if action_distribution == "tanh_squashed_gaussian":
        action_for_env = jnp.tanh(action_sample)
        logprob = tanh_squashed_gaussian_logprob_from_raw(action_sample, mean, log_std)
        clip_mask = jnp.zeros_like(action_for_env)
    else:
        action_for_env = jnp.clip(action_sample, -1.0, 1.0)
        logprob = gaussian_logprob(action_for_env, mean, log_std)
        clip_mask = (jnp.abs(action_sample) > 1.0).astype(jnp.float32)
    return action_sample, action_for_env, logprob, clip_mask


def select_done(done: jax.Array, old_value: jax.Array, new_value: jax.Array) -> jax.Array:
    """Select per-env reset values where an episode ended."""
    mask = done.reshape(done.shape + (1,) * (old_value.ndim - 1))
    return jnp.where(mask, new_value, old_value)


def build_command_env_step(
    step_fn: Any,
    action_low: jax.Array,
    action_high: jax.Array,
    *,
    dt: float,
    reward_coefficients: dict[str, float] | None = None,
    command_generator_profile: str = "default",
) -> Any:
    """Build one JAX command-tracker env step."""

    def env_step(
        state: Any, action_for_env: jax.Array, plan_key: jax.Array
    ) -> tuple[Any, dict[str, jax.Array]]:
        sim_action = v60_rollout.scale_action_jax(action_for_env, action_low, action_high)
        next_race_data, (raw_obs_full, _sparse_reward, terminated_full, truncated_full, _info) = (
            step_fn(state.pipeline_state, sim_action)
        )
        raw_obs = v60_rollout.drop_drone_dim(raw_obs_full)
        terminated = terminated_full[:, 0]
        truncated = truncated_full[:, 0]
        done = terminated | truncated
        reference = state.info["reference"]
        rewards, reward_metrics = v60_rollout.command_reward(
            state.info["raw_obs"],
            raw_obs,
            reference,
            action_for_env,
            state.info["last_action_norm"],
            terminated,
            truncated,
            reward_coefficients=reward_coefficients,
        )
        history_row = v60_rollout.history_rows(raw_obs)
        history = jnp.concatenate(
            [state.info["history"][:, 1:, :], history_row[:, None, :]], axis=1
        )
        reset_history = jnp.repeat(
            history_row[:, None, :], v60_rollout.REFERENCE_TRACKER_HISTORY, axis=1
        )
        history = jnp.where(done[:, None, None], reset_history, history)
        last_action_norm = jnp.where(done[:, None], jnp.zeros_like(action_for_env), action_for_env)
        old_steps = state.info["command_steps"]
        command_steps = jnp.where(done, 0, old_steps + 1)
        new_plans = v60_rollout.sample_command_plans(
            plan_key, raw_obs["pos"], dt, command_generator_profile
        )
        plans = jax.tree_util.tree_map(
            lambda old, new: select_done(done, old, new), state.info["plans"], new_plans
        )
        new_reference = v60_rollout.command_reference(plans, command_steps, dt)
        tracker_obs = v60_rollout.command_observation(
            raw_obs, new_reference, history, last_action_norm
        )
        next_state = state.replace(
            pipeline_state=next_race_data,
            obs=tracker_obs,
            reward=rewards,
            done=done.astype(jnp.float32),
            metrics=reward_metrics,
            info={
                "raw_obs": raw_obs,
                "plans": plans,
                "command_steps": command_steps,
                "history": history,
                "last_action_norm": last_action_norm,
                "reference": new_reference,
            },
        )
        metrics = {
            "reward_mean": reward_metrics["reward_mean"],
            "done_mean": jnp.mean(done.astype(jnp.float32)),
            "obs_abs_mean": jnp.mean(jnp.abs(tracker_obs)),
            "action_abs_mean": jnp.mean(jnp.abs(action_for_env)),
            "command_position_error": reward_metrics["command_position_error"],
            "command_velocity_error": reward_metrics["command_velocity_error"],
            "cross_track_error": reward_metrics["cross_track_error"],
            "action_delta_penalty": reward_metrics["action_delta_penalty"],
        }
        return next_state, metrics

    return env_step


def build_rollout_fn(
    env_step: Any, *, num_steps: int, action_distribution: str = "clipped_gaussian"
) -> Any:
    """Build a stochastic PPO rollout scan."""

    def rollout_step(
        carry: tuple[Any, jax.Array], params: dict[str, Any]
    ) -> tuple[tuple[Any, jax.Array], dict[str, jax.Array]]:
        state, key = carry
        key, action_key, plan_key = jax.random.split(key, 3)
        obs = state.obs
        mean, log_std, value = policy_apply_for_distribution(params, obs, action_distribution)
        action_sample, action_for_env, logprob, clip_mask = sample_env_action(
            mean, log_std, action_key, action_distribution
        )
        raw_logprob = gaussian_logprob(action_sample, mean, log_std)
        env_logprob_recomputed = action_logprob(action_for_env, mean, log_std, action_distribution)
        next_state, metrics = env_step(state, action_for_env, plan_key)
        transition = {
            "obs": obs,
            "actions": action_for_env,
            "logprobs": logprob,
            "values": value,
            "rewards": next_state.reward,
            "dones": next_state.done,
            "action_clip_fraction": jnp.mean(clip_mask),
            "action_any_dim_clipped_fraction": jnp.mean(jnp.max(clip_mask, axis=-1)),
            "action_sample_env_delta_abs_mean": jnp.mean(jnp.abs(action_sample - action_for_env)),
            "action_raw_vs_env_logprob_abs_mean": jnp.mean(jnp.abs(raw_logprob - logprob)),
            "action_logprob_env_consistency_error": jnp.mean(
                jnp.abs(logprob - env_logprob_recomputed)
            ),
            "reward_mean": metrics["reward_mean"],
            "done_mean": metrics["done_mean"],
            "obs_abs_mean": metrics["obs_abs_mean"],
            "action_abs_mean": metrics["action_abs_mean"],
            "command_position_error": metrics["command_position_error"],
            "command_velocity_error": metrics["command_velocity_error"],
            "cross_track_error": metrics["cross_track_error"],
            "action_delta_penalty": metrics["action_delta_penalty"],
        }
        return (next_state, key), transition

    @jax.jit
    def rollout(
        state: Any, params: dict[str, Any], key: jax.Array
    ) -> tuple[Any, jax.Array, dict[str, jax.Array]]:
        (next_state, next_key), transitions = jax.lax.scan(
            lambda carry, _: rollout_step(carry, params), (state, key), None, length=num_steps
        )
        return next_state, next_key, transitions

    return rollout


def build_eval_rollout_fn(
    env_step: Any, *, num_steps: int, action_distribution: str = "clipped_gaussian"
) -> Any:
    """Build a deterministic short evaluation rollout."""

    def rollout_step(
        carry: tuple[Any, jax.Array], params: dict[str, Any]
    ) -> tuple[tuple[Any, jax.Array], dict[str, jax.Array]]:
        state, key = carry
        key, plan_key = jax.random.split(key)
        mean, _log_std, _value = policy_apply_for_distribution(
            params, state.obs, action_distribution
        )
        action_for_env = deterministic_env_action(mean, action_distribution)
        next_state, metrics = env_step(state, action_for_env, plan_key)
        return (next_state, key), metrics

    @jax.jit
    def eval_rollout(
        state: Any, params: dict[str, Any], key: jax.Array
    ) -> tuple[Any, jax.Array, dict[str, jax.Array]]:
        (next_state, next_key), metrics = jax.lax.scan(
            lambda carry, _: rollout_step(carry, params), (state, key), None, length=num_steps
        )
        return next_state, next_key, metrics

    return eval_rollout


def compute_gae(
    rewards: jax.Array,
    dones: jax.Array,
    values: jax.Array,
    next_value: jax.Array,
    *,
    gamma: float,
    gae_lambda: float,
) -> tuple[jax.Array, jax.Array]:
    """Compute GAE advantages and returns."""

    def gae_step(
        carry: tuple[jax.Array, jax.Array], transition: tuple[jax.Array, jax.Array, jax.Array]
    ) -> tuple[tuple[jax.Array, jax.Array], jax.Array]:
        next_advantage, next_values = carry
        reward, done, value = transition
        next_non_terminal = 1.0 - done
        delta = reward + gamma * next_values * next_non_terminal - value
        advantage = delta + gamma * gae_lambda * next_non_terminal * next_advantage
        return (advantage, value), advantage

    (_carry, _next_value), advantages_reversed = jax.lax.scan(
        gae_step,
        (jnp.zeros_like(next_value), next_value),
        (rewards[::-1], dones[::-1], values[::-1]),
    )
    advantages = advantages_reversed[::-1]
    returns = advantages + values
    return advantages.astype(jnp.float32), returns.astype(jnp.float32)


def flatten_rollout(
    transitions: dict[str, jax.Array], advantages: jax.Array, returns: jax.Array
) -> dict[str, jax.Array]:
    """Flatten rollout tensors from time/env into batch."""

    def flatten(value: jax.Array) -> jax.Array:
        return value.reshape((value.shape[0] * value.shape[1],) + value.shape[2:])

    return {
        "obs": flatten(transitions["obs"]),
        "actions": flatten(transitions["actions"]),
        "logprobs": flatten(transitions["logprobs"]),
        "advantages": advantages.reshape(-1),
        "returns": returns.reshape(-1),
        "values": flatten(transitions["values"]),
    }


def build_update_fn(
    optimizer: optax.GradientTransformation,
    *,
    batch_size: int,
    num_minibatches: int,
    update_epochs: int,
    clip_coef: float,
    ent_coef: float,
    vf_coef: float,
    action_distribution: str = "clipped_gaussian",
) -> Any:
    """Build the clipped PPO update."""
    minibatch_size = batch_size // num_minibatches

    def loss_fn(
        params: dict[str, Any], batch: dict[str, jax.Array]
    ) -> tuple[jax.Array, dict[str, jax.Array]]:
        mean, log_std, new_values = policy_apply_for_distribution(
            params, batch["obs"], action_distribution
        )
        new_logprobs = action_logprob(batch["actions"], mean, log_std, action_distribution)
        entropy = gaussian_entropy(log_std)
        logratio = new_logprobs - batch["logprobs"]
        ratio = jnp.exp(logratio)
        advantages = batch["advantages"]
        advantages = (advantages - jnp.mean(advantages)) / (jnp.std(advantages) + 1e-8)
        pg_loss_unclipped = -advantages * ratio
        pg_loss_clipped = -advantages * jnp.clip(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
        policy_loss = jnp.mean(jnp.maximum(pg_loss_unclipped, pg_loss_clipped))
        value_loss = 0.5 * jnp.mean(jnp.square(new_values - batch["returns"]))
        entropy_loss = jnp.mean(entropy)
        loss = policy_loss + vf_coef * value_loss - ent_coef * entropy_loss
        approx_kl = jnp.mean((ratio - 1.0) - logratio)
        clip_fraction = jnp.mean((jnp.abs(ratio - 1.0) > clip_coef).astype(jnp.float32))
        return loss, {
            "loss": loss,
            "policy_loss": policy_loss,
            "value_loss": value_loss,
            "entropy": entropy_loss,
            "approx_kl": approx_kl,
            "clip_fraction": clip_fraction,
        }

    def minibatch_update(
        carry: tuple[dict[str, Any], optax.OptState], minibatch: dict[str, jax.Array]
    ) -> tuple[tuple[dict[str, Any], optax.OptState], dict[str, jax.Array]]:
        params, opt_state = carry
        (loss, metrics), grads = jax.value_and_grad(loss_fn, has_aux=True)(params, minibatch)
        grad_norm = optax.global_norm(grads)
        updates, opt_state = optimizer.update(grads, opt_state, params)
        params = optax.apply_updates(params, updates)
        metrics = metrics | {"grad_norm": grad_norm, "loss": loss}
        return (params, opt_state), metrics

    @jax.jit
    def ppo_update(
        params: dict[str, Any],
        opt_state: optax.OptState,
        batch: dict[str, jax.Array],
        key: jax.Array,
    ) -> tuple[dict[str, Any], optax.OptState, jax.Array, dict[str, jax.Array]]:
        def epoch_update(
            carry: tuple[dict[str, Any], optax.OptState, jax.Array], _unused: None
        ) -> tuple[tuple[dict[str, Any], optax.OptState, jax.Array], dict[str, jax.Array]]:
            epoch_params, epoch_opt_state, epoch_key = carry
            epoch_key, perm_key = jax.random.split(epoch_key)
            permutation = jax.random.permutation(perm_key, batch_size)
            shuffled = jax.tree_util.tree_map(lambda value: value[permutation], batch)
            minibatches = jax.tree_util.tree_map(
                lambda value: value.reshape((num_minibatches, minibatch_size) + value.shape[1:]),
                shuffled,
            )
            (epoch_params, epoch_opt_state), minibatch_metrics = jax.lax.scan(
                minibatch_update, (epoch_params, epoch_opt_state), minibatches
            )
            metrics = jax.tree_util.tree_map(jnp.mean, minibatch_metrics)
            return (epoch_params, epoch_opt_state, epoch_key), metrics

        (params, opt_state, key), epoch_metrics = jax.lax.scan(
            epoch_update, (params, opt_state, key), None, length=update_epochs
        )
        metrics = jax.tree_util.tree_map(jnp.mean, epoch_metrics)
        return params, opt_state, key, metrics

    return ppo_update


@jax.jit
def compute_advantage_batch(
    params: dict[str, Any],
    final_obs: jax.Array,
    transitions: dict[str, jax.Array],
    gamma: float,
    gae_lambda: float,
    value_target_scale: float = 1.0,
) -> tuple[dict[str, jax.Array], dict[str, jax.Array]]:
    """Compute flattened PPO batch plus rollout summary metrics."""
    _mean, _log_std, next_value = actor_critic_apply_raw(params, final_obs)
    scale = jnp.maximum(jnp.asarray(value_target_scale, dtype=jnp.float32), 1e-6)
    raw_values = transitions["values"] * scale
    raw_next_value = next_value * scale
    advantages, returns = compute_gae(
        transitions["rewards"],
        transitions["dones"],
        raw_values,
        raw_next_value,
        gamma=gamma,
        gae_lambda=gae_lambda,
    )
    value_targets = returns / scale
    batch = flatten_rollout(transitions, advantages, value_targets)
    returns_var = jnp.var(returns)
    explained_variance = jnp.where(
        returns_var > 1e-8, 1.0 - jnp.var(returns - raw_values) / returns_var, jnp.nan
    )
    summary = {
        "rollout_reward_mean": jnp.mean(transitions["reward_mean"]),
        "rollout_done_mean": jnp.mean(transitions["done_mean"]),
        "rollout_obs_abs_mean": jnp.mean(transitions["obs_abs_mean"]),
        "rollout_action_abs_mean": jnp.mean(transitions["action_abs_mean"]),
        "rollout_action_clip_fraction": jnp.mean(transitions["action_clip_fraction"]),
        "rollout_action_any_dim_clipped_fraction": jnp.mean(
            transitions["action_any_dim_clipped_fraction"]
        ),
        "rollout_action_sample_env_delta_abs_mean": jnp.mean(
            transitions["action_sample_env_delta_abs_mean"]
        ),
        "rollout_action_raw_vs_env_logprob_abs_mean": jnp.mean(
            transitions["action_raw_vs_env_logprob_abs_mean"]
        ),
        "rollout_action_logprob_env_consistency_error": jnp.mean(
            transitions["action_logprob_env_consistency_error"]
        ),
        "rollout_command_position_error": jnp.mean(transitions["command_position_error"]),
        "rollout_command_velocity_error": jnp.mean(transitions["command_velocity_error"]),
        "rollout_cross_track_error": jnp.mean(transitions["cross_track_error"]),
        "rollout_action_delta_penalty": jnp.mean(transitions["action_delta_penalty"]),
        "advantages_mean": jnp.mean(advantages),
        "advantages_std": jnp.std(advantages),
        "returns_mean": jnp.mean(returns),
        "returns_std": jnp.std(returns),
        "value_target_scale": scale,
        "value_targets_mean": jnp.mean(value_targets),
        "value_targets_std": jnp.std(value_targets),
        "value_target_abs_mean": jnp.mean(jnp.abs(value_targets)),
        "values_mean": jnp.mean(raw_values),
        "values_std": jnp.std(raw_values),
        "values_scaled_mean": jnp.mean(transitions["values"]),
        "explained_variance": explained_variance,
        "all_finite": (
            jnp.all(jnp.isfinite(transitions["obs"]))
            & jnp.all(jnp.isfinite(transitions["actions"]))
            & jnp.all(jnp.isfinite(transitions["rewards"]))
        ),
    }
    return batch, summary


def setup_wandb(args: argparse.Namespace) -> Any:
    """Initialize W&B lazily so dry environments can import this script."""
    import wandb

    config = {
        key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()
    }
    init_kwargs = {
        "project": args.wandb_project_name,
        "entity": args.wandb_entity,
        "name": args.wandb_run_name,
        "id": args.wandb_run_id,
        "mode": args.wandb_mode,
        "config": config,
    }
    if args.wandb_run_id:
        init_kwargs["resume"] = "allow"
    run = wandb.init(**init_kwargs)
    wandb.define_metric("global_step")
    wandb.define_metric("train/*", step_metric="global_step")
    wandb.define_metric("eval/*", step_metric="global_step")
    wandb.define_metric("speed/*", step_metric="global_step")
    return run


def save_checkpoint(
    path: Path,
    *,
    args: argparse.Namespace,
    params: dict[str, Any],
    opt_state: optax.OptState,
    global_step: int,
    metrics: dict[str, Any],
) -> None:
    """Save a smoke checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "v62_brax_ppo_smoke",
        "global_step": int(global_step),
        "params": jax.device_get(params),
        "optimizer_state": jax.device_get(opt_state),
        "metadata": {
            "config": args.config,
            "task": "reference_command_no_gate_reward",
            "observation_layout": "level3_reference_tracker_command_v3",
            "obs_dim": v60_rollout.REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
            "action_dim": 4,
            "hidden_dim": int(args.hidden_dim),
            "num_envs": int(args.num_envs),
            "num_steps": int(args.num_steps),
            "backend": "jax_brax_state_optax_ppo_smoke",
            "wandb_run_id": args.wandb_run_id,
            "initial_log_std": float(args.initial_log_std),
            "ent_coef": float(args.ent_coef),
            "value_target_scale": float(args.value_target_scale),
            "action_distribution": args.action_distribution,
            "action_logprob_mode": action_logprob_mode(args.action_distribution),
            "reward_coefficients": command_reward_coefficients(args),
            "command_generator_profile": args.command_generator_profile,
        },
        "metrics": metrics,
    }
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def eval_policy(
    eval_rollout: Any, state: Any, params: dict[str, Any], key: jax.Array, *, eval_rollouts: int
) -> tuple[Any, jax.Array, dict[str, float]]:
    """Run deterministic short evaluation rollouts."""
    metrics_rows = []
    for _ in range(max(1, eval_rollouts)):
        state, key, metrics = eval_rollout(state, params, key)
        jax.tree_util.tree_map(lambda value: value.block_until_ready(), metrics)
        metrics_rows.append(
            {name: float(np.asarray(value).mean()) for name, value in metrics.items()}
        )
    return (
        state,
        key,
        {name: float(np.mean([row[name] for row in metrics_rows])) for name in metrics_rows[0]},
    )


def main() -> None:
    """Run the v62 smoke trainer."""
    args = parse_args()
    if args.num_envs < 1 or args.num_steps < 1:
        raise ValueError("--num-envs and --num-steps must be positive.")
    if args.value_target_scale <= 0.0:
        raise ValueError("--value-target-scale must be positive.")
    batch_size = int(args.num_envs) * int(args.num_steps)
    if batch_size % int(args.num_minibatches) != 0:
        raise ValueError("--num-envs * --num-steps must be divisible by --num-minibatches.")
    num_updates = max(1, int(args.total_timesteps) // batch_size)
    actual_timesteps = num_updates * batch_size
    device = jax.devices(args.jax_device)[0]
    with jax.default_device(device):
        env, config, action_low, action_high = v60_rollout.make_base_env(args)
        raw_obs_np, _info = env.reset(seed=args.seed)
        raw_obs = {key: jax.device_put(value, device) for key, value in raw_obs_np.items()}
        keys = jax.random.split(jax.random.PRNGKey(args.seed), 6)
        state = v60_rollout.make_initial_state(
            env,
            raw_obs,
            keys[0],
            dt=1.0 / float(config.env.freq),
            command_generator_profile=args.command_generator_profile,
        )
        eval_state = v60_rollout.make_initial_state(
            env,
            raw_obs,
            keys[1],
            dt=1.0 / float(config.env.freq),
            command_generator_profile=args.command_generator_profile,
        )
        params = init_actor_critic_params(
            keys[2],
            obs_dim=v60_rollout.REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
            hidden_dim=int(args.hidden_dim),
            action_dim=4,
            initial_log_std=float(args.initial_log_std),
        )
        optimizer = optax.chain(
            optax.clip_by_global_norm(float(args.max_grad_norm)),
            optax.adam(float(args.learning_rate), eps=1e-5),
        )
        opt_state = optimizer.init(params)
        env_step = build_command_env_step(
            env._step,  # noqa: SLF001
            action_low,
            action_high,
            dt=1.0 / float(config.env.freq),
            reward_coefficients=command_reward_coefficients(args),
            command_generator_profile=args.command_generator_profile,
        )
        rollout = build_rollout_fn(
            env_step, num_steps=int(args.num_steps), action_distribution=args.action_distribution
        )
        eval_rollout = build_eval_rollout_fn(
            env_step, num_steps=int(args.num_steps), action_distribution=args.action_distribution
        )
        ppo_update = build_update_fn(
            optimizer,
            batch_size=batch_size,
            num_minibatches=int(args.num_minibatches),
            update_epochs=int(args.update_epochs),
            clip_coef=float(args.clip_coef),
            ent_coef=float(args.ent_coef),
            vf_coef=float(args.vf_coef),
            action_distribution=args.action_distribution,
        )

        wandb_run = setup_wandb(args) if args.wandb_enabled else None
        train_key, update_key, eval_key = keys[3], keys[4], keys[5]
        global_step = 0
        first_update_elapsed = None
        timed_updates: list[float] = []
        last_metrics: dict[str, float] = {}
        print(
            {
                "backend": "jax_brax_state_optax_ppo_smoke",
                "device": str(device),
                "num_updates": num_updates,
                "batch_size": batch_size,
                "actual_timesteps": actual_timesteps,
                "num_minibatches": int(args.num_minibatches),
                "update_epochs": int(args.update_epochs),
                "value_target_scale": float(args.value_target_scale),
                "action_distribution": args.action_distribution,
                "action_logprob_mode": action_logprob_mode(args.action_distribution),
                "command_generator_profile": args.command_generator_profile,
            }
        )

        for update_idx in range(1, num_updates + 1):
            update_start = time.perf_counter()
            state, train_key, transitions = rollout(state, params, train_key)
            batch, rollout_summary = compute_advantage_batch(
                params,
                state.obs,
                transitions,
                float(args.gamma),
                float(args.gae_lambda),
                float(args.value_target_scale),
            )
            params, opt_state, update_key, train_metrics = ppo_update(
                params, opt_state, batch, update_key
            )
            jax.tree_util.tree_map(lambda value: value.block_until_ready(), train_metrics)
            jax.tree_util.tree_map(lambda value: value.block_until_ready(), rollout_summary)
            elapsed = time.perf_counter() - update_start
            if first_update_elapsed is None:
                first_update_elapsed = elapsed
            else:
                timed_updates.append(elapsed)
            global_step += batch_size
            steps_per_s = batch_size / max(elapsed, 1e-9)
            metrics = {
                "global_step": global_step,
                "train/update": update_idx,
                "speed/update_elapsed_s": elapsed,
                "speed/update_steps_per_s": steps_per_s,
                "speed/pytorch_fast_path_ratio": steps_per_s / PYTORCH_FAST_PATH_STEPS_PER_S,
            }
            metrics |= {
                f"train/{name}": float(np.asarray(value)) for name, value in train_metrics.items()
            }
            metrics |= {
                f"train/{name}": float(np.asarray(value)) for name, value in rollout_summary.items()
            }
            last_metrics = metrics
            if wandb_run is not None:
                import wandb

                wandb.log(metrics, step=global_step)
            print(metrics)

        eval_state, eval_key, eval_metrics = eval_policy(
            eval_rollout, eval_state, params, eval_key, eval_rollouts=int(args.eval_rollouts)
        )
        post_warmup_mean = (
            float(np.mean(timed_updates)) if timed_updates else float(first_update_elapsed)
        )
        steady_updates = timed_updates[1:] if len(timed_updates) > 1 else timed_updates
        steady_state_mean = (
            float(np.mean(steady_updates)) if steady_updates else float(first_update_elapsed)
        )
        post_warmup_steps_per_s = batch_size / max(post_warmup_mean, 1e-9)
        steady_state_steps_per_s = batch_size / max(steady_state_mean, 1e-9)
        final_metrics = {
            "global_step": global_step,
            "actual_timesteps": actual_timesteps,
            "first_update_elapsed_s": float(first_update_elapsed),
            "post_warmup_mean_update_s": post_warmup_mean,
            "post_warmup_steps_per_s": post_warmup_steps_per_s,
            "steady_state_mean_update_s": steady_state_mean,
            "steady_state_steps_per_s": steady_state_steps_per_s,
            "pytorch_fast_path_steps_per_s": PYTORCH_FAST_PATH_STEPS_PER_S,
            "post_warmup_vs_pytorch_ratio": post_warmup_steps_per_s / PYTORCH_FAST_PATH_STEPS_PER_S,
            "steady_state_vs_pytorch_ratio": steady_state_steps_per_s
            / PYTORCH_FAST_PATH_STEPS_PER_S,
            "command_generator_profile": args.command_generator_profile,
        }
        final_metrics |= {f"eval/{name}": value for name, value in eval_metrics.items()}
        final_metrics |= last_metrics
        save_checkpoint(
            args.checkpoint_path,
            args=args,
            params=params,
            opt_state=opt_state,
            global_step=global_step,
            metrics=final_metrics,
        )
        with args.checkpoint_path.open("rb") as handle:
            payload = pickle.load(handle)
        if int(payload["global_step"]) != int(global_step):
            raise RuntimeError("Saved checkpoint failed global_step verification.")
        if wandb_run is not None:
            import wandb

            wandb.log(
                {f"eval/{name}": value for name, value in eval_metrics.items()}, step=global_step
            )
            wandb.finish()
        print(
            {
                "checkpoint": str(args.checkpoint_path),
                "global_step": int(global_step),
                "post_warmup_steps_per_s": post_warmup_steps_per_s,
                "steady_state_steps_per_s": steady_state_steps_per_s,
                "post_warmup_vs_pytorch_ratio": post_warmup_steps_per_s
                / PYTORCH_FAST_PATH_STEPS_PER_S,
                "steady_state_vs_pytorch_ratio": steady_state_steps_per_s
                / PYTORCH_FAST_PATH_STEPS_PER_S,
                "eval": eval_metrics,
            }
        )
        env.close()


if __name__ == "__main__":
    main()
