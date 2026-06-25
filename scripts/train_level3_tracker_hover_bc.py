"""Behavior-clone a hover PD teacher into the v55 tracker PPO actor."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.optim as optim
from drone_models.core import load_params

from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_OBS_DIM,
    ReferenceTrackerVectorEnv,
    TrackerPPOAgent,
    action_bounds_from_config,
    normalize_action,
    save_tracker_checkpoint,
)
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/"
    / "v55_tracker_hover_pd_bc_attempt004.ckpt"
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for hover behavior cloning."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--seed", type=int, default=550401)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--samples", type=int, default=262144)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument("--kp", type=float, default=2.0)
    parser.add_argument("--kd", type=float, default=1.4)
    parser.add_argument("--max-lateral-accel-g", type=float, default=0.6)
    parser.add_argument("--target", nargs=3, type=float, default=(0.0, 0.0, 0.65))
    parser.add_argument("--jax-device", default="gpu")
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def hover_pd_teacher_actions(
    raw_obs: dict[str, Any],
    *,
    target: np.ndarray,
    action_low: np.ndarray,
    action_high: np.ndarray,
    mass: float,
    kp: float,
    kd: float,
    max_lateral_accel_g: float,
) -> np.ndarray:
    """Return normalized roll/pitch/yaw/thrust actions for a hover PD teacher."""
    pos = np.asarray(raw_obs["pos"], dtype=np.float32)
    vel = np.asarray(raw_obs["vel"], dtype=np.float32)
    if pos.ndim == 1:
        pos = pos[None, :]
        vel = vel[None, :]
    target_batch = np.broadcast_to(target.astype(np.float32), pos.shape)
    acc = float(kp) * (target_batch - pos) - float(kd) * vel
    gravity = 9.81
    lateral_limit = abs(float(max_lateral_accel_g))
    roll = -np.clip(acc[:, 1] / gravity, -lateral_limit, lateral_limit)
    pitch = np.clip(acc[:, 0] / gravity, -lateral_limit, lateral_limit)
    yaw = np.zeros_like(roll)
    thrust = np.clip(float(mass) * (gravity + acc[:, 2]), action_low[3], action_high[3])
    physical = np.stack([roll, pitch, yaw, thrust], axis=1).astype(np.float32)
    return normalize_action(physical, action_low, action_high).astype(np.float32)


def collect_teacher_dataset(
    args: argparse.Namespace,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Roll out the hover PD teacher and collect tracker observations/actions."""
    config = load_config(ROOT / "config" / args.config)
    action_low, action_high = action_bounds_from_config(config, args.rp_limit_deg)
    params = load_params(config.sim.physics, config.sim.drone_model)
    mass = float(params["mass"])
    target = np.asarray(args.target, dtype=np.float32)
    env = ReferenceTrackerVectorEnv(
        config_name=args.config,
        task="hover",
        tracker_env_mode="free_space",
        num_envs=args.num_envs,
        max_episode_steps=args.max_episode_steps,
        seed=args.seed,
        rp_limit_deg=args.rp_limit_deg,
        jax_device=args.jax_device,
    )
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    obs, _info = env.reset(seed=args.seed)
    start = time.time()
    try:
        while sum(row.shape[0] for row in observations) < args.samples:
            if env._raw_obs is None:  # noqa: SLF001
                raise RuntimeError("ReferenceTrackerVectorEnv missing raw observations.")
            action = hover_pd_teacher_actions(
                env._raw_obs,  # noqa: SLF001
                target=target,
                action_low=action_low,
                action_high=action_high,
                mass=mass,
                kp=args.kp,
                kd=args.kd,
                max_lateral_accel_g=args.max_lateral_accel_g,
            )
            observations.append(np.asarray(obs, dtype=np.float32).copy())
            actions.append(action.copy())
            obs, _reward, _terminated, _truncated, _info = env.step(action)
    finally:
        env.close()
    obs_array = np.concatenate(observations, axis=0)[: args.samples].astype(np.float32)
    action_array = np.concatenate(actions, axis=0)[: args.samples].astype(np.float32)
    metadata = {
        "samples": int(obs_array.shape[0]),
        "collection_seconds": float(time.time() - start),
        "teacher": "hover_pd",
        "teacher_kp": float(args.kp),
        "teacher_kd": float(args.kd),
        "teacher_target": [float(x) for x in target],
        "teacher_action_mean": [float(x) for x in np.mean(action_array, axis=0)],
        "teacher_action_std": [float(x) for x in np.std(action_array, axis=0)],
    }
    return obs_array, action_array, metadata


def train_actor_bc(
    args: argparse.Namespace,
    observations: np.ndarray,
    actions: np.ndarray,
) -> tuple[TrackerPPOAgent, dict[str, float]]:
    """Fit the actor mean to teacher actions with supervised MSE."""
    device = torch.device("cuda" if args.cuda and torch.cuda.is_available() else "cpu")
    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    agent = TrackerPPOAgent(
        obs_dim=REFERENCE_TRACKER_OBS_DIM,
        action_dim=4,
        hidden_dim=args.hidden_dim,
    ).to(device)
    obs_tensor = torch.as_tensor(observations, dtype=torch.float32, device=device)
    action_tensor = torch.as_tensor(actions, dtype=torch.float32, device=device)
    optimizer = optim.AdamW(agent.actor_mean.parameters(), lr=args.learning_rate, eps=1e-5)
    with torch.no_grad():
        initial_pred = agent.actor_mean(obs_tensor[: args.batch_size])
        initial_mse = torch.mean((initial_pred - action_tensor[: args.batch_size]) ** 2)
    indices = np.arange(len(observations))
    last_loss = initial_mse
    for _epoch in range(args.epochs):
        rng.shuffle(indices)
        for start in range(0, len(indices), args.batch_size):
            batch = indices[start : start + args.batch_size]
            pred = agent.actor_mean(obs_tensor[batch])
            loss = torch.mean((pred - action_tensor[batch]) ** 2)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(agent.actor_mean.parameters(), 1.0)
            optimizer.step()
            last_loss = loss.detach()
    with torch.no_grad():
        final_mse = torch.mean((agent.actor_mean(obs_tensor) - action_tensor) ** 2)
    metrics = {
        "initial_actor_mse": float(initial_mse.cpu().item()),
        "final_actor_mse": float(final_mse.cpu().item()),
        "last_batch_mse": float(last_loss.cpu().item()),
    }
    return agent, metrics


def main() -> None:
    """Collect PD teacher data, train a BC actor, and save a tracker checkpoint."""
    args = parse_args()
    observations, actions, dataset_metadata = collect_teacher_dataset(args)
    agent, metrics = train_actor_bc(args, observations, actions)
    metadata = {
        "config": args.config,
        "task": "hover",
        "requested_task": "hover",
        "tracker_env_mode": "free_space",
        "num_envs": int(args.num_envs),
        "num_steps": 0,
        "total_timesteps": 0,
        "jax_device": str(args.jax_device),
        "rp_limit_deg": float(args.rp_limit_deg),
        "reward_coefficients": {},
        "max_episode_steps": int(args.max_episode_steps),
        "v54_lane": "v55_tracker_hover_pd_bc_warmstart",
        "bc": dataset_metadata | metrics,
    }
    save_tracker_checkpoint(args.output, agent, global_step=0, extra_metadata=metadata)
    print(
        {
            "checkpoint": str(args.output),
            "samples": int(observations.shape[0]),
            **metrics,
        }
    )


if __name__ == "__main__":
    main()
