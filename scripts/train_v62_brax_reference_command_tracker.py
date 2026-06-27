"""Train the formal v62 Brax/JAX reference-command tracker lane."""

from __future__ import annotations

import argparse
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import jax
import numpy as np
import optax

import scripts.benchmark_v60_brax_rollout as v60_rollout
import scripts.train_v60_brax_ppo_smoke as ppo_smoke

ROOT = Path(__file__).parents[1]
LANE_NAME = "v62_brax_reference_command_tracker"
DEFAULT_CHECKPOINT_DIR = ROOT / "lsy_drone_racing/control/checkpoints" / LANE_NAME
DEFAULT_CHECKPOINT = DEFAULT_CHECKPOINT_DIR / f"{LANE_NAME}_final.pkl"
DEFAULT_SUMMARY_JSON = (
    ROOT
    / "experiments/level3_ppo_loop/analysis"
    / ("tracker_stage_metrics/v62_brax_reference_command_tracker_1m_summary.json")
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the formal v62 lane."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--lane-name", default=LANE_NAME)
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--seed", type=int, default=26201)
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--total-timesteps", type=int, default=1_048_576)
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
        "--action-distribution",
        choices=ppo_smoke.ACTION_DISTRIBUTIONS,
        default="tanh_squashed_gaussian",
    )
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument("--eval-rollouts", type=int, default=4)
    parser.add_argument("--checkpoint-path", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--checkpoint-interval", type=int, default=262_144)
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--wandb-enabled", action="store_true")
    parser.add_argument("--wandb-project-name", default="ADR-PPO-Racing-Level3")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-run-name", default=LANE_NAME)
    parser.add_argument("--wandb-run-id")
    parser.add_argument("--wandb-mode", default="offline")
    parser.add_argument("--jax-device", default="gpu")
    return parser.parse_args()


def checkpoint_step_path(model_path: Path, step: int) -> Path:
    """Return a milestone checkpoint path."""
    stem = model_path.stem.removesuffix("_final")
    return model_path.with_name(f"{stem}_step_{int(step):09d}{model_path.suffix}")


def jsonable(value: Any) -> Any:
    """Convert arrays and paths into JSON-serializable values."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def save_lane_checkpoint(
    path: Path,
    *,
    args: argparse.Namespace,
    params: dict[str, Any],
    opt_state: optax.OptState,
    global_step: int,
    metrics: dict[str, Any],
    rng_keys: dict[str, jax.Array],
) -> None:
    """Save a v62 lane checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "format": "v62_brax_reference_command_tracker",
        "global_step": int(global_step),
        "params": jax.device_get(params),
        "optimizer_state": jax.device_get(opt_state),
        "rng_keys": jax.device_get(rng_keys),
        "metadata": {
            "lane_name": args.lane_name,
            "config": args.config,
            "task": "reference_command_no_gate_reward",
            "observation_layout": "level3_reference_tracker_command_v3",
            "obs_dim": v60_rollout.REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
            "action_dim": 4,
            "hidden_dim": int(args.hidden_dim),
            "num_envs": int(args.num_envs),
            "num_steps": int(args.num_steps),
            "backend": "jax_brax_state_optax_ppo",
            "reward_scope": "no gate/aperture/obstacle/race/finish/stage reward",
            "wandb_run_id": args.wandb_run_id,
            "initial_log_std": float(args.initial_log_std),
            "ent_coef": float(args.ent_coef),
            "value_target_scale": float(args.value_target_scale),
            "action_distribution": args.action_distribution,
            "action_logprob_mode": ppo_smoke.action_logprob_mode(args.action_distribution),
        },
        "metrics": jsonable(metrics),
    }
    with path.open("wb") as handle:
        pickle.dump(payload, handle)


def load_lane_checkpoint(
    path: Path, device: jax.Device
) -> tuple[dict[str, Any], optax.OptState, int, dict[str, jax.Array]]:
    """Load a v62 lane checkpoint."""
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    if payload.get("format") != "v62_brax_reference_command_tracker":
        raise ValueError(f"Unsupported checkpoint format in {path}.")
    params = jax.tree_util.tree_map(lambda value: jax.device_put(value, device), payload["params"])
    opt_state = jax.tree_util.tree_map(
        lambda value: jax.device_put(value, device), payload["optimizer_state"]
    )
    rng_keys = jax.tree_util.tree_map(
        lambda value: jax.device_put(value, device), payload.get("rng_keys", {})
    )
    return params, opt_state, int(payload["global_step"]), rng_keys


def next_checkpoint_step(global_step: int, interval: int) -> int | None:
    """Return the next milestone step after the current global step."""
    if interval <= 0:
        return None
    return ((int(global_step) // interval) + 1) * interval


def eval_delta(initial: dict[str, float], final: dict[str, float]) -> dict[str, float | bool]:
    """Compare initial and final deterministic eval metrics."""
    delta = {
        name: float(final[name] - initial[name])
        for name in sorted(initial.keys() & final.keys())
        if isinstance(initial[name], int | float)
    }
    lower_is_better = (
        "command_position_error",
        "command_velocity_error",
        "cross_track_error",
        "action_delta_penalty",
        "done_mean",
    )
    improved_errors = {
        f"{name}_improved": bool(delta.get(name, 0.0) < 0.0)
        for name in lower_is_better
        if name in delta
    }
    reward_improved = bool(delta.get("reward_mean", 0.0) > 0.0)
    any_tracking_improved = any(improved_errors.values())
    return (
        delta
        | improved_errors
        | {
            "reward_improved": reward_improved,
            "any_tracking_metric_improved": bool(any_tracking_improved),
            "has_eval_learning_signal": bool(reward_improved or any_tracking_improved),
        }
    )


def main() -> None:
    """Run a bounded v62 Brax/JAX reference-command tracker training chunk."""
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
        keys = jax.random.split(jax.random.PRNGKey(args.seed), 8)
        optimizer = optax.chain(
            optax.clip_by_global_norm(float(args.max_grad_norm)),
            optax.adam(float(args.learning_rate), eps=1e-5),
        )
        if args.resume_from is not None:
            params, opt_state, global_step, restored_keys = load_lane_checkpoint(
                args.resume_from, device
            )
            train_key = restored_keys.get("train_key", keys[3])
            update_key = restored_keys.get("update_key", keys[4])
        else:
            params = ppo_smoke.init_actor_critic_params(
                keys[2],
                obs_dim=v60_rollout.REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
                hidden_dim=int(args.hidden_dim),
                action_dim=4,
                initial_log_std=float(args.initial_log_std),
            )
            opt_state = optimizer.init(params)
            global_step = 0
            train_key = keys[3]
            update_key = keys[4]

        def make_tracker_state(plan_key: jax.Array) -> Any:
            return v60_rollout.make_initial_state(
                env, raw_obs, plan_key, dt=1.0 / float(config.env.freq)
            )

        state = make_tracker_state(keys[0])
        env_step = ppo_smoke.build_command_env_step(
            env._step,  # noqa: SLF001
            action_low,
            action_high,
            dt=1.0 / float(config.env.freq),
        )
        rollout = ppo_smoke.build_rollout_fn(
            env_step, num_steps=int(args.num_steps), action_distribution=args.action_distribution
        )
        eval_rollout = ppo_smoke.build_eval_rollout_fn(
            env_step, num_steps=int(args.num_steps), action_distribution=args.action_distribution
        )
        ppo_update = ppo_smoke.build_update_fn(
            optimizer,
            batch_size=batch_size,
            num_minibatches=int(args.num_minibatches),
            update_epochs=int(args.update_epochs),
            clip_coef=float(args.clip_coef),
            ent_coef=float(args.ent_coef),
            vf_coef=float(args.vf_coef),
            action_distribution=args.action_distribution,
        )
        wandb_run = ppo_smoke.setup_wandb(args) if args.wandb_enabled else None
        eval_key = keys[5]
        eval_plan_key = keys[6]
        initial_eval_state = make_tracker_state(eval_plan_key)
        _eval_state, _eval_key, initial_eval = ppo_smoke.eval_policy(
            eval_rollout,
            initial_eval_state,
            params,
            eval_key,
            eval_rollouts=int(args.eval_rollouts),
        )
        if wandb_run is not None:
            import wandb

            wandb.log(
                {f"eval_initial/{name}": value for name, value in initial_eval.items()},
                step=global_step,
            )

        next_milestone = next_checkpoint_step(global_step, int(args.checkpoint_interval))
        first_update_elapsed: float | None = None
        timed_updates: list[float] = []
        milestone_checkpoints: list[str] = []
        last_metrics: dict[str, float] = {}
        print(
            {
                "lane_name": args.lane_name,
                "backend": "jax_brax_state_optax_ppo",
                "device": str(device),
                "num_updates": num_updates,
                "batch_size": batch_size,
                "actual_timesteps": actual_timesteps,
                "initial_global_step": int(global_step),
                "initial_log_std": float(args.initial_log_std),
                "ent_coef": float(args.ent_coef),
                "value_target_scale": float(args.value_target_scale),
                "action_distribution": args.action_distribution,
                "action_logprob_mode": ppo_smoke.action_logprob_mode(args.action_distribution),
                "initial_eval": initial_eval,
            }
        )

        for update_idx in range(1, num_updates + 1):
            update_start = time.perf_counter()
            state, train_key, transitions = rollout(state, params, train_key)
            batch, rollout_summary = ppo_smoke.compute_advantage_batch(
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
                "global_step": int(global_step),
                "train/update": update_idx,
                "speed/update_elapsed_s": elapsed,
                "speed/update_steps_per_s": steps_per_s,
                "speed/pytorch_fast_path_ratio": steps_per_s
                / ppo_smoke.PYTORCH_FAST_PATH_STEPS_PER_S,
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
            while next_milestone is not None and global_step >= next_milestone:
                milestone_path = checkpoint_step_path(args.checkpoint_path, next_milestone)
                save_lane_checkpoint(
                    milestone_path,
                    args=args,
                    params=params,
                    opt_state=opt_state,
                    global_step=global_step,
                    metrics=metrics,
                    rng_keys={"train_key": train_key, "update_key": update_key},
                )
                milestone_checkpoints.append(str(milestone_path))
                next_milestone = next_checkpoint_step(next_milestone, int(args.checkpoint_interval))

        final_eval_state = make_tracker_state(eval_plan_key)
        _eval_state, _eval_key, final_eval = ppo_smoke.eval_policy(
            eval_rollout, final_eval_state, params, eval_key, eval_rollouts=int(args.eval_rollouts)
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
        comparison = eval_delta(initial_eval, final_eval)
        final_metrics: dict[str, Any] = {
            "lane_name": args.lane_name,
            "global_step": int(global_step),
            "actual_timesteps": int(actual_timesteps),
            "first_update_elapsed_s": float(first_update_elapsed),
            "post_warmup_mean_update_s": post_warmup_mean,
            "post_warmup_steps_per_s": post_warmup_steps_per_s,
            "steady_state_mean_update_s": steady_state_mean,
            "steady_state_steps_per_s": steady_state_steps_per_s,
            "pytorch_fast_path_steps_per_s": ppo_smoke.PYTORCH_FAST_PATH_STEPS_PER_S,
            "post_warmup_vs_pytorch_ratio": post_warmup_steps_per_s
            / ppo_smoke.PYTORCH_FAST_PATH_STEPS_PER_S,
            "steady_state_vs_pytorch_ratio": steady_state_steps_per_s
            / ppo_smoke.PYTORCH_FAST_PATH_STEPS_PER_S,
            "initial_eval": initial_eval,
            "final_eval": final_eval,
            "eval_delta": comparison,
            "last_train_metrics": last_metrics,
            "milestone_checkpoints": milestone_checkpoints,
            "checkpoint": str(args.checkpoint_path),
            "initial_log_std": float(args.initial_log_std),
            "ent_coef": float(args.ent_coef),
            "value_target_scale": float(args.value_target_scale),
            "action_distribution": args.action_distribution,
            "action_logprob_mode": ppo_smoke.action_logprob_mode(args.action_distribution),
        }
        save_lane_checkpoint(
            args.checkpoint_path,
            args=args,
            params=params,
            opt_state=opt_state,
            global_step=global_step,
            metrics=final_metrics,
            rng_keys={"train_key": train_key, "update_key": update_key},
        )
        with args.checkpoint_path.open("rb") as handle:
            payload = pickle.load(handle)
        if int(payload["global_step"]) != int(global_step):
            raise RuntimeError("Saved checkpoint failed global_step verification.")
        if args.summary_json is not None:
            args.summary_json.parent.mkdir(parents=True, exist_ok=True)
            args.summary_json.write_text(
                json.dumps(jsonable(final_metrics), indent=2, sort_keys=True) + "\n"
            )
        if wandb_run is not None:
            import wandb

            wandb.log(
                {f"eval_final/{name}": value for name, value in final_eval.items()},
                step=global_step,
            )
            wandb.log(
                {f"eval_delta/{name}": value for name, value in comparison.items()},
                step=global_step,
            )
            wandb.finish()
        print(json.dumps(jsonable(final_metrics), indent=2, sort_keys=True))
        env.close()


if __name__ == "__main__":
    main()
