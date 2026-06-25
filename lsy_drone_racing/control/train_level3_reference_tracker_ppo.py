"""Train the v54 Level3 reference-trajectory tracker PPO."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.optim as optim

import wandb
from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_OBS_DIM,
    REFERENCE_TRACKER_REWARD_DEFAULTS,
    REFERENCE_TRACKER_TASKS,
    TRACKER_ENV_MODES,
    ReferenceTrackerEnv,
    TrackerPPOAgent,
    load_tracker_checkpoint,
    normalize_tracker_task,
    save_tracker_checkpoint,
)

ROOT = Path(__file__).parents[2]
DEFAULT_MODEL = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/v54_reference_tracker_ppo/"
    / "v54_reference_tracker_ppo_final.ckpt"
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the v54 tracker PPO trainer."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3.toml")
    parser.add_argument(
        "--task",
        choices=REFERENCE_TRACKER_TASKS,
        default="hover",
    )
    parser.add_argument("--tracker-env-mode", choices=TRACKER_ENV_MODES, default="auto")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=4096)
    parser.add_argument("--num-steps", type=int, default=256)
    parser.add_argument("--num-minibatches", type=int, default=4)
    parser.add_argument("--update-epochs", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--clip-coef", type=float, default=0.2)
    parser.add_argument("--ent-coef", type=float, default=0.01)
    parser.add_argument("--vf-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    add_reward_arguments(parser)
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--initial-model-path", type=Path)
    parser.add_argument("--checkpoint-interval", type=int, default=0)
    parser.add_argument("--wandb-enabled", action="store_true")
    parser.add_argument("--wandb-project-name", default="ADR-PPO-Racing-Level3")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-run-name")
    parser.add_argument("--wandb-run-id")
    parser.add_argument("--wandb-mode", default="online")
    return parser.parse_args()


def add_reward_arguments(parser: argparse.ArgumentParser) -> None:
    """Expose v54 tracker reward coefficients as stable CLI knobs."""
    for name, default in REFERENCE_TRACKER_REWARD_DEFAULTS.items():
        parser.add_argument(
            f"--{name.replace('_', '-')}",
            f"--{name}",
            dest=name,
            type=float,
            default=default,
        )


def setup_wandb(args: argparse.Namespace) -> None:
    """Initialize W&B metrics for tracker training."""
    config = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in vars(args).items()
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
    wandb.init(**init_kwargs)
    wandb.define_metric("global_step")
    wandb.define_metric("train/*", step_metric="global_step")
    wandb.define_metric("tracker/*", step_metric="global_step")


def make_agent(args: argparse.Namespace, device: torch.device) -> TrackerPPOAgent:
    """Construct the tracker PPO agent on the selected device."""
    if args.initial_model_path is not None:
        agent, metadata = load_tracker_checkpoint(args.initial_model_path, device)
        if int(metadata.get("obs_dim", REFERENCE_TRACKER_OBS_DIM)) != REFERENCE_TRACKER_OBS_DIM:
            raise ValueError(f"Unexpected obs_dim in {args.initial_model_path}.")
        return agent.to(device)
    return TrackerPPOAgent(
        obs_dim=REFERENCE_TRACKER_OBS_DIM,
        action_dim=4,
        hidden_dim=args.hidden_dim,
    ).to(device)


def train(args: argparse.Namespace) -> Path:
    """Train one v54 tracker task and save the resulting checkpoint."""
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if args.cuda and torch.cuda.is_available() else "cpu")
    env = ReferenceTrackerEnv(
        config_name=args.config,
        task=args.task,
        max_episode_steps=args.max_episode_steps,
        seed=args.seed,
        render=False,
        rp_limit_deg=args.rp_limit_deg,
        tracker_env_mode=args.tracker_env_mode,
        reward_coefficients=reward_coefficients_from_args(args),
    )
    agent = make_agent(args, device)
    optimizer = optim.Adam(agent.parameters(), lr=args.learning_rate, eps=1e-5)
    if args.wandb_enabled:
        setup_wandb(args)

    obs_np, _info = env.reset(seed=args.seed)
    obs = torch.as_tensor(obs_np, dtype=torch.float32, device=device)
    next_done = torch.tensor(0.0, device=device)
    initial_global_step = initial_checkpoint_step(args.initial_model_path)
    global_step = initial_global_step
    start_time = time.time()
    next_checkpoint_step = (
        global_step + args.checkpoint_interval if args.checkpoint_interval > 0 else None
    )
    batch_size = args.num_steps
    minibatch_size = max(1, batch_size // max(1, args.num_minibatches))
    num_updates = max(1, args.total_timesteps // args.num_steps)
    episode_return = 0.0
    episode_length = 0

    for update in range(1, num_updates + 1):
        obs_buf = torch.zeros((args.num_steps, REFERENCE_TRACKER_OBS_DIM), device=device)
        actions_buf = torch.zeros((args.num_steps, 4), device=device)
        logprobs_buf = torch.zeros((args.num_steps,), device=device)
        rewards_buf = torch.zeros((args.num_steps,), device=device)
        dones_buf = torch.zeros((args.num_steps,), device=device)
        values_buf = torch.zeros((args.num_steps,), device=device)

        for step in range(args.num_steps):
            global_step += 1
            obs_buf[step] = obs
            dones_buf[step] = next_done
            with torch.no_grad():
                action, logprob, _entropy, value = agent.get_action_and_value(obs.unsqueeze(0))
            action_np = action.squeeze(0).detach().cpu().numpy().astype(np.float32)
            next_obs_np, reward, terminated, truncated, _info = env.step(action_np)
            done = bool(terminated or truncated)
            episode_return += float(reward)
            episode_length += 1

            actions_buf[step] = action.squeeze(0)
            logprobs_buf[step] = logprob.squeeze(0)
            rewards_buf[step] = float(reward)
            next_done = torch.tensor(float(done), device=device)
            values_buf[step] = value.squeeze(0)

            if done:
                if args.wandb_enabled:
                    wandb.log(
                        {
                            "global_step": global_step,
                            "train/episode_return": episode_return,
                            "train/episode_length": episode_length,
                        }
                        | env.last_diagnostics
                )
                next_obs_np, _info = env.reset()
                episode_return = 0.0
                episode_length = 0
            obs = torch.as_tensor(next_obs_np, dtype=torch.float32, device=device)

            if next_checkpoint_step is not None and global_step >= next_checkpoint_step:
                checkpoint_path = checkpoint_step_path(args.model_path, next_checkpoint_step)
                save_tracker_checkpoint(
                    checkpoint_path,
                    agent,
                    global_step=global_step,
                    extra_metadata=checkpoint_metadata(args),
                )
                next_checkpoint_step += args.checkpoint_interval

        with torch.no_grad():
            next_value = agent.critic(obs.unsqueeze(0)).reshape(())
            advantages = torch.zeros_like(rewards_buf)
            lastgaelam = torch.tensor(0.0, device=device)
            for t in reversed(range(args.num_steps)):
                if t == args.num_steps - 1:
                    next_nonterminal = 1.0 - next_done
                    next_values = next_value
                else:
                    next_nonterminal = 1.0 - dones_buf[t + 1]
                    next_values = values_buf[t + 1]
                delta = rewards_buf[t] + args.gamma * next_values * next_nonterminal - values_buf[t]
                lastgaelam = delta + args.gamma * args.gae_lambda * next_nonterminal * lastgaelam
                advantages[t] = lastgaelam
            returns = advantages + values_buf

        batch_indices = np.arange(batch_size)
        clipfracs: list[float] = []
        for _epoch in range(args.update_epochs):
            np.random.shuffle(batch_indices)
            for start in range(0, batch_size, minibatch_size):
                mb_idx = batch_indices[start : start + minibatch_size]
                _, newlogprob, entropy, newvalue = agent.get_action_and_value(
                    obs_buf[mb_idx], actions_buf[mb_idx]
                )
                logratio = newlogprob - logprobs_buf[mb_idx]
                ratio = logratio.exp()
                with torch.no_grad():
                    clipfracs.append(
                        float(((ratio - 1.0).abs() > args.clip_coef).float().mean().item())
                    )
                mb_advantages = advantages[mb_idx]
                mb_advantages = (mb_advantages - mb_advantages.mean()) / (
                    mb_advantages.std(unbiased=False) + 1e-8
                )
                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(
                    ratio,
                    1.0 - args.clip_coef,
                    1.0 + args.clip_coef,
                )
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()
                value_loss = 0.5 * ((newvalue.reshape(-1) - returns[mb_idx]) ** 2).mean()
                entropy_loss = entropy.mean()
                loss = pg_loss - args.ent_coef * entropy_loss + args.vf_coef * value_loss
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(agent.parameters(), args.max_grad_norm)
                optimizer.step()

        if args.wandb_enabled:
            sps = int(global_step / max(time.time() - start_time, 1e-6))
            wandb.log(
                {
                    "global_step": global_step,
                    "train/learning_rate": args.learning_rate,
                    "train/value_loss": float(value_loss.item()),
                    "train/policy_loss": float(pg_loss.item()),
                    "train/entropy": float(entropy_loss.item()),
                    "train/clipfrac": float(np.mean(clipfracs)) if clipfracs else 0.0,
                    "train/SPS": sps,
                }
            )

    save_tracker_checkpoint(
        args.model_path,
        agent,
        global_step=global_step,
        extra_metadata=checkpoint_metadata(args),
    )
    env.close()
    if args.wandb_enabled:
        wandb.finish()
    return args.model_path


def checkpoint_step_path(model_path: Path, step: int) -> Path:
    """Return the milestone checkpoint path for a global step."""
    stem = model_path.stem.removesuffix("_final")
    return model_path.with_name(f"{stem}_step_{step:09d}{model_path.suffix}")


def checkpoint_metadata(args: argparse.Namespace) -> dict[str, object]:
    """Build metadata stored in every v54 tracker checkpoint."""
    return {
        "config": args.config,
        "initial_model_path": str(args.initial_model_path) if args.initial_model_path else None,
        "task": normalize_tracker_task(args.task),
        "requested_task": args.task,
        "tracker_env_mode": args.tracker_env_mode,
        "rp_limit_deg": float(args.rp_limit_deg),
        "reward_coefficients": reward_coefficients_from_args(args),
        "max_episode_steps": int(args.max_episode_steps),
        "v54_lane": "v54_reference_trajectory_tracker_ppo",
    }


def reward_coefficients_from_args(args: argparse.Namespace) -> dict[str, float]:
    """Return ReferenceTrackerReward coefficients selected by CLI arguments."""
    return {
        name: float(getattr(args, name))
        for name in REFERENCE_TRACKER_REWARD_DEFAULTS
    }


def initial_checkpoint_step(path: Path | None) -> int:
    """Return the global-step offset from a prior checkpoint, if any."""
    if path is None:
        return 0
    _agent, metadata = load_tracker_checkpoint(path, "cpu")
    return int(metadata.get("global_step", 0))


def main() -> None:
    """Run tracker PPO training from CLI arguments."""
    args = parse_args()
    path = train(args)
    print(f"v54 reference tracker checkpoint saved to {path}")


if __name__ == "__main__":
    main()
