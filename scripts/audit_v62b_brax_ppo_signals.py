"""Audit v62b PPO signal health before changing tracker rewards."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import jax
import jax.numpy as jnp
import numpy as np

import scripts.benchmark_v60_brax_rollout as v60_rollout
import scripts.train_v60_brax_ppo_smoke as ppo_smoke
import scripts.train_v62_brax_reference_command_tracker as v62_lane

ROOT = Path(__file__).parents[1]
DEFAULT_CHECKPOINT = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/v62_brax_reference_command_tracker/"
    / "v62_brax_reference_command_tracker_final.pkl"
)
DEFAULT_OUTPUT = (
    ROOT
    / "experiments/level3_ppo_loop/analysis/tracker_stage_metrics"
    / ("v62b_brax_ppo_signal_audit.json")
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--seed", type=int, default=26221)
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument(
        "--initial-log-std-values",
        default="-0.5,-1.0,-1.5,-2.0",
        help="Comma-separated log std values to audit from identical initial weights.",
    )
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--skip-checkpoint", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--action-distribution",
        choices=ppo_smoke.ACTION_DISTRIBUTIONS,
        default="tanh_squashed_gaussian",
    )
    parser.add_argument("--jax-device", default="gpu")
    return parser.parse_args()


def parse_log_std_values(raw: str) -> list[float]:
    """Parse comma-separated log std values."""
    values = [float(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError("--initial-log-std-values must contain at least one value.")
    return values


def percentile(values: np.ndarray, q: float) -> float:
    """Return a float percentile."""
    return float(np.percentile(values, q))


def scalar_stats(values: np.ndarray) -> dict[str, float]:
    """Summarize an array."""
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    return {
        "mean": float(np.mean(flat)),
        "std": float(np.std(flat)),
        "min": float(np.min(flat)),
        "p05": percentile(flat, 5),
        "p50": percentile(flat, 50),
        "p95": percentile(flat, 95),
        "max": float(np.max(flat)),
        "abs_mean": float(np.mean(np.abs(flat))),
        "abs_p95": percentile(np.abs(flat), 95),
    }


def build_audit_rollout_fn(env_step: Any, *, num_steps: int, action_distribution: str) -> Any:
    """Build a rollout scan that preserves sampled and clipped action diagnostics."""

    def rollout_step(
        carry: tuple[Any, jax.Array], params: dict[str, Any]
    ) -> tuple[tuple[Any, jax.Array], dict[str, jax.Array]]:
        state, key = carry
        key, action_key, plan_key = jax.random.split(key, 3)
        mean, log_std, value = ppo_smoke.policy_apply_for_distribution(
            params, state.obs, action_distribution
        )
        action_sample, action_for_env, stored_logprob, clip_mask = ppo_smoke.sample_env_action(
            mean, log_std, action_key, action_distribution
        )
        raw_logprob = ppo_smoke.gaussian_logprob(action_sample, mean, log_std)
        env_action_logprob = ppo_smoke.action_logprob(
            action_for_env, mean, log_std, action_distribution
        )
        next_state, metrics = env_step(state, action_for_env, plan_key)
        transition = {
            "obs": state.obs,
            "mean": mean,
            "log_std": jnp.broadcast_to(log_std, action_sample.shape),
            "action_sample": action_sample,
            "action_for_env": action_for_env,
            "clip_mask": clip_mask,
            "raw_logprob": raw_logprob,
            "env_action_logprob": env_action_logprob,
            "stored_logprob": stored_logprob,
            "values": value,
            "rewards": next_state.reward,
            "dones": next_state.done,
            "reward_mean": metrics["reward_mean"],
            "done_mean": metrics["done_mean"],
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


def compute_advantage_summary(
    params: dict[str, Any],
    final_obs: jax.Array,
    transitions: dict[str, jax.Array],
    *,
    gamma: float,
    gae_lambda: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute raw advantages and returns."""
    _mean, _log_std, next_value = ppo_smoke.actor_critic_apply_raw(params, final_obs)
    advantages, returns = ppo_smoke.compute_gae(
        transitions["rewards"],
        transitions["dones"],
        transitions["values"],
        next_value,
        gamma=gamma,
        gae_lambda=gae_lambda,
    )
    return np.asarray(advantages), np.asarray(returns)


def verdicts_for_metrics(metrics: dict[str, Any]) -> dict[str, str]:
    """Turn raw audit metrics into concise verdicts."""
    action = metrics["action_sampling"]
    adv = metrics["advantage"]
    reward = metrics["reward"]
    log_std = metrics["initial_or_policy_log_std"]
    return {
        "action_sampling_logprob": (
            "bad" if action["stored_vs_env_logprob_abs_mean"] > 1e-6 else "ok"
        ),
        "action_clipping": "high" if action["sample_clip_fraction"] > 0.05 else "ok",
        "advantage_scale": "large" if adv["std"] > 25.0 or abs(adv["mean"]) > 25.0 else "ok",
        "reward_scale": "large" if reward["abs_mean"] > 3.0 or reward["abs_p95"] > 10.0 else "ok",
        "initial_std": "too_large" if np.exp(log_std["mean"]) > 0.35 else "ok",
    }


def summarize_rollout(
    *,
    label: str,
    params: dict[str, Any],
    state: Any,
    rollout: Any,
    key: jax.Array,
    gamma: float,
    gae_lambda: float,
) -> dict[str, Any]:
    """Run and summarize one audit rollout."""
    final_state, _next_key, transitions = rollout(state, params, key)
    jax.tree_util.tree_map(lambda value: value.block_until_ready(), transitions)
    advantages, returns = compute_advantage_summary(
        params, final_state.obs, transitions, gamma=gamma, gae_lambda=gae_lambda
    )
    action_sample = np.asarray(transitions["action_sample"])
    action_for_env = np.asarray(transitions["action_for_env"])
    clip_mask = np.asarray(transitions["clip_mask"], dtype=bool)
    raw_logprob = np.asarray(transitions["raw_logprob"])
    env_action_logprob = np.asarray(transitions["env_action_logprob"])
    stored_logprob = np.asarray(transitions["stored_logprob"])
    raw_vs_env_action = raw_logprob - env_action_logprob
    stored_vs_env = stored_logprob - env_action_logprob
    sample_delta = action_sample - action_for_env
    log_std = np.asarray(transitions["log_std"])
    rewards = np.asarray(transitions["rewards"])
    values = np.asarray(transitions["values"])
    dones = np.asarray(transitions["dones"])
    metrics = {
        "label": label,
        "initial_or_policy_log_std": scalar_stats(log_std),
        "initial_or_policy_std": scalar_stats(np.exp(log_std)),
        "action_sampling": {
            "sample_clip_fraction": float(np.mean(clip_mask)),
            "any_dim_clipped_fraction": float(np.mean(np.any(clip_mask, axis=-1))),
            "mean_abs_sample": float(np.mean(np.abs(action_sample))),
            "mean_abs_env_action": float(np.mean(np.abs(action_for_env))),
            "mean_abs_sample_minus_env_action": float(np.mean(np.abs(sample_delta))),
            "p95_abs_sample_minus_env_action": percentile(np.abs(sample_delta), 95),
            "raw_vs_env_action_logprob_mean": float(np.mean(raw_vs_env_action)),
            "raw_vs_env_action_logprob_abs_mean": float(np.mean(np.abs(raw_vs_env_action))),
            "raw_vs_env_action_logprob_abs_p95": percentile(np.abs(raw_vs_env_action), 95),
            "stored_vs_env_logprob_abs_mean": float(np.mean(np.abs(stored_vs_env))),
            "stored_vs_env_logprob_abs_p95": percentile(np.abs(stored_vs_env), 95),
            "raw_logprob": scalar_stats(raw_logprob),
            "env_action_logprob": scalar_stats(env_action_logprob),
            "stored_logprob": scalar_stats(stored_logprob),
        },
        "advantage": scalar_stats(advantages),
        "normalized_advantage": scalar_stats(
            (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        ),
        "return": scalar_stats(returns),
        "value": scalar_stats(values),
        "reward": scalar_stats(rewards),
        "done_fraction": float(np.mean(dones)),
        "tracker_metrics": {
            "reward_mean": float(np.mean(np.asarray(transitions["reward_mean"]))),
            "command_position_error": float(
                np.mean(np.asarray(transitions["command_position_error"]))
            ),
            "command_velocity_error": float(
                np.mean(np.asarray(transitions["command_velocity_error"]))
            ),
            "cross_track_error": float(np.mean(np.asarray(transitions["cross_track_error"]))),
            "action_delta_penalty": float(np.mean(np.asarray(transitions["action_delta_penalty"]))),
        },
    }
    metrics["verdicts"] = verdicts_for_metrics(metrics)
    return metrics


def make_initial_params(
    key: jax.Array, *, hidden_dim: int, initial_log_std: float
) -> dict[str, Any]:
    """Create initial params for one log-std scenario."""
    return ppo_smoke.init_actor_critic_params(
        key,
        obs_dim=v60_rollout.REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
        hidden_dim=hidden_dim,
        action_dim=4,
        initial_log_std=initial_log_std,
    )


def main() -> None:
    """Run the v62b PPO-signal audit."""
    args = parse_args()
    log_std_values = parse_log_std_values(args.initial_log_std_values)
    device = jax.devices(args.jax_device)[0]
    with jax.default_device(device):
        env, config, action_low, action_high = v60_rollout.make_base_env(args)
        raw_obs_np, _info = env.reset(seed=args.seed)
        raw_obs = {key: jax.device_put(value, device) for key, value in raw_obs_np.items()}
        env_step = ppo_smoke.build_command_env_step(
            env._step,  # noqa: SLF001
            action_low,
            action_high,
            dt=1.0 / float(config.env.freq),
        )
        rollout = build_audit_rollout_fn(
            env_step, num_steps=int(args.num_steps), action_distribution=args.action_distribution
        )
        keys = jax.random.split(jax.random.PRNGKey(args.seed), 6)
        base_param_key = keys[0]
        plan_key = keys[1]
        rollout_key = keys[2]

        def make_state() -> Any:
            return v60_rollout.make_initial_state(
                env, raw_obs, plan_key, dt=1.0 / float(config.env.freq)
            )

        scenarios = []
        for log_std in log_std_values:
            params = make_initial_params(
                base_param_key, hidden_dim=int(args.hidden_dim), initial_log_std=log_std
            )
            scenarios.append(
                summarize_rollout(
                    label=f"initial_log_std_{log_std:g}",
                    params=params,
                    state=make_state(),
                    rollout=rollout,
                    key=rollout_key,
                    gamma=float(args.gamma),
                    gae_lambda=float(args.gae_lambda),
                )
            )
        if not args.skip_checkpoint and args.checkpoint.exists():
            params, _opt_state, global_step, _rng_keys = v62_lane.load_lane_checkpoint(
                args.checkpoint, device
            )
            checkpoint_metrics = summarize_rollout(
                label=f"checkpoint_step_{global_step}",
                params=params,
                state=make_state(),
                rollout=rollout,
                key=rollout_key,
                gamma=float(args.gamma),
                gae_lambda=float(args.gae_lambda),
            )
            checkpoint_metrics["checkpoint"] = str(args.checkpoint)
            checkpoint_metrics["checkpoint_global_step"] = int(global_step)
            scenarios.append(checkpoint_metrics)

        default_scenario = scenarios[0] if scenarios else None
        summary = {
            "audit": "v62b_brax_ppo_signal_audit",
            "config": args.config,
            "num_envs": int(args.num_envs),
            "num_steps": int(args.num_steps),
            "seed": int(args.seed),
            "action_distribution": args.action_distribution,
            "action_logprob_mode": ppo_smoke.action_logprob_mode(args.action_distribution),
            "scenarios": scenarios,
            "overall_findings": {
                "default_or_first_scenario": (
                    {"label": default_scenario["label"], "verdicts": default_scenario["verdicts"]}
                    if default_scenario is not None
                    else None
                ),
                "reward_tuning_should_wait": any(
                    item["verdicts"]["action_sampling_logprob"] == "bad"
                    or item["verdicts"]["action_clipping"] == "high"
                    or item["verdicts"]["advantage_scale"] == "large"
                    or item["verdicts"]["reward_scale"] == "large"
                    or item["verdicts"]["initial_std"] == "too_large"
                    for item in scenarios
                ),
            },
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(v62_lane.jsonable(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps(v62_lane.jsonable(summary), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
