"""Train the v60 tracker with SBX's packaged JAX PPO backend."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import numpy as np
import optax
from flax import linen as nn
from sbx import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.vec_env.base_vec_env import VecEnv, VecEnvIndices, VecEnvObs

import wandb
from lsy_drone_racing.control.level3_reference_tracker import (
    COMMAND_REFERENCE_TRACKER_LAYOUT,
    REFERENCE_TRACKER_REWARD_DEFAULTS,
    ReferenceTrackerVectorEnv,
    default_tracker_observation_layout,
    normalize_tracker_task,
)

ROOT = Path(__file__).parents[2]
COMMAND_TASK = "reference_command_no_gate_reward"
DEFAULT_MODEL = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/v61_sbx_reference_command_tracker/"
    / "v61_sbx_reference_command_tracker_final"
)
NO_GATE_REWARD_COEFFICIENTS = frozenset(
    {
        "gate_center_coef",
        "obstacle_margin",
        "obstacle_coef",
        "gate_x_progress_coef",
        "gate_cross_bonus",
        "gate_recover_bonus",
        "gate_linger_penalty_coef",
    }
)


class ReferenceTrackerSBXVecEnv(VecEnv):
    """Adapt ReferenceTrackerVectorEnv to SB3/SBX's VecEnv API."""

    def __init__(self, env: ReferenceTrackerVectorEnv):
        """Initialize the VecEnv adapter around an already-vectorized tracker env."""
        self.env = env
        self._actions: np.ndarray | None = None
        super().__init__(env.num_envs, env.single_observation_space, env.single_action_space)

    def reset(self) -> VecEnvObs:
        """Reset the wrapped vector tracker env and return the initial observation batch."""
        seed = next((value for value in self._seeds if value is not None), None)
        options = next((value for value in self._options if value), None)
        obs, info = self.env.reset(seed=seed, options=options)
        self.reset_infos = _split_info(info, self.num_envs)
        self._reset_seeds()
        self._reset_options()
        return obs.astype(np.float32)

    def step_async(self, actions: np.ndarray) -> None:
        """Store actions until SBX calls step_wait."""
        self._actions = np.asarray(actions, dtype=np.float32)

    def step_wait(self) -> tuple[VecEnvObs, np.ndarray, np.ndarray, list[dict[str, Any]]]:
        """Step the wrapped tracker env and convert Gymnasium dones to VecEnv dones."""
        if self._actions is None:
            raise RuntimeError("step_wait called before step_async")
        obs, rewards, terminated, truncated, info = self.env.step(self._actions)
        dones = np.asarray(terminated, dtype=bool) | np.asarray(truncated, dtype=bool)
        infos = _split_info(info, self.num_envs)
        for env_idx, env_info in enumerate(infos):
            env_info["TimeLimit.truncated"] = bool(truncated[env_idx] and not terminated[env_idx])
            if dones[env_idx]:
                env_info["terminal_observation"] = np.asarray(obs[env_idx], dtype=np.float32)
        return (obs.astype(np.float32), np.asarray(rewards, dtype=np.float32), dones, infos)

    def close(self) -> None:
        """Close the wrapped environment if it exposes a close hook."""
        close = getattr(self.env, "close", None)
        if callable(close):
            close()

    def get_attr(self, attr_name: str, indices: VecEnvIndices = None) -> list[Any]:
        """Return an attribute value for selected logical envs."""
        del indices
        return [getattr(self.env, attr_name) for _ in range(self.num_envs)]

    def set_attr(self, attr_name: str, value: Any, indices: VecEnvIndices = None) -> None:
        """Set an attribute on the wrapped vector env."""
        del indices
        setattr(self.env, attr_name, value)

    def env_method(
        self,
        method_name: str,
        *method_args: Any,
        indices: VecEnvIndices = None,
        **method_kwargs: Any,
    ) -> list[Any]:
        """Call a method on the wrapped vector env."""
        del indices
        method = getattr(self.env, method_name)
        result = method(*method_args, **method_kwargs)
        return [result for _ in range(self.num_envs)]

    def env_is_wrapped(self, wrapper_class: type[Any], indices: VecEnvIndices = None) -> list[bool]:
        """Report whether selected logical envs are wrapped by wrapper_class."""
        del wrapper_class
        return [False for _ in self._get_indices(indices)]


class TrackerDiagnosticsCallback(BaseCallback):
    """Log tracker diagnostics exposed by the vector env."""

    def __init__(self, tracker_env: ReferenceTrackerVectorEnv, *, enabled: bool):
        """Store callback configuration."""
        super().__init__()
        self.tracker_env = tracker_env
        self.enabled = bool(enabled)

    def _on_step(self) -> bool:
        """Log mean tracker diagnostics once per SBX callback step."""
        if not self.enabled or not self.tracker_env.last_diagnostics:
            return True
        wandb.log({"global_step": int(self.num_timesteps), **self.tracker_env.last_diagnostics})
        return True


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--task", choices=[COMMAND_TASK], default=COMMAND_TASK)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--total-timesteps", type=int, default=65_536)
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--update-epochs", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--clip-coef", type=float, default=0.2)
    parser.add_argument("--ent-coef", type=float, default=0.01)
    parser.add_argument("--vf-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--target-kl", type=float)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument("--tracker-env-mode", default="auto")
    parser.add_argument("--observation-layout", default=COMMAND_REFERENCE_TRACKER_LAYOUT)
    parser.add_argument("--jax-device", default="gpu")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--checkpoint-interval", type=int, default=0)
    parser.add_argument("--wandb-enabled", action="store_true")
    parser.add_argument("--wandb-project-name", default="ADR-PPO-Racing-Level3")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-run-name")
    parser.add_argument("--wandb-run-id")
    parser.add_argument("--wandb-mode", default="online")
    add_reward_arguments(parser)
    return parser.parse_args()


def add_reward_arguments(parser: argparse.ArgumentParser) -> None:
    """Expose v60 command reward coefficients as CLI knobs."""
    for name, default in REFERENCE_TRACKER_REWARD_DEFAULTS.items():
        parser.add_argument(
            f"--{name.replace('_', '-')}", f"--{name}", dest=name, type=float, default=default
        )


def reward_coefficients_from_args(args: argparse.Namespace) -> dict[str, float]:
    """Return reward coefficients, with gate-like terms disabled for v60."""
    coefficients = {name: float(getattr(args, name)) for name in REFERENCE_TRACKER_REWARD_DEFAULTS}
    if normalize_tracker_task(args.task) == COMMAND_TASK:
        for name in NO_GATE_REWARD_COEFFICIENTS:
            coefficients[name] = 0.0
    return coefficients


def make_training_env(args: argparse.Namespace) -> tuple[ReferenceTrackerSBXVecEnv, str]:
    """Create the SBX-compatible tracker env."""
    task = normalize_tracker_task(args.task)
    observation_layout = default_tracker_observation_layout(task, args.observation_layout)
    if task == COMMAND_TASK and observation_layout != COMMAND_REFERENCE_TRACKER_LAYOUT:
        raise ValueError(
            f"{COMMAND_TASK} must use {COMMAND_REFERENCE_TRACKER_LAYOUT}, got {observation_layout}."
        )
    tracker_env = ReferenceTrackerVectorEnv(
        config_name=args.config,
        task=task,
        num_envs=args.num_envs,
        max_episode_steps=args.max_episode_steps,
        seed=args.seed,
        render=False,
        rp_limit_deg=args.rp_limit_deg,
        tracker_env_mode=args.tracker_env_mode,
        observation_layout=observation_layout,
        reward_coefficients=reward_coefficients_from_args(args),
        jax_device=args.jax_device,
    )
    return ReferenceTrackerSBXVecEnv(tracker_env), observation_layout


def setup_wandb(args: argparse.Namespace, observation_layout: str) -> None:
    """Initialize W&B logging for SBX tracker training."""
    config = {
        key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()
    }
    config["observation_layout"] = observation_layout
    config["trainer_backend"] = "sbx_ppo"
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
    wandb.define_metric("tracker/*", step_metric="global_step")


def make_callbacks(
    args: argparse.Namespace, vec_env: ReferenceTrackerSBXVecEnv
) -> list[BaseCallback]:
    """Build SBX callbacks for diagnostics and optional checkpointing."""
    callbacks: list[BaseCallback] = [
        TrackerDiagnosticsCallback(vec_env.env, enabled=args.wandb_enabled)
    ]
    if args.checkpoint_interval > 0:
        checkpoint_dir = args.model_path.parent / "milestones"
        callbacks.append(
            CheckpointCallback(
                save_freq=max(1, args.checkpoint_interval // max(1, args.num_envs)),
                save_path=str(checkpoint_dir),
                name_prefix=args.model_path.stem,
                save_replay_buffer=False,
                save_vecnormalize=False,
            )
        )
    return callbacks


def train(args: argparse.Namespace) -> Path:
    """Run SBX PPO training and save the packaged model."""
    vec_env, observation_layout = make_training_env(args)
    if args.wandb_enabled:
        setup_wandb(args, observation_layout)

    policy_kwargs = {
        "net_arch": {
            "pi": [args.hidden_dim, args.hidden_dim],
            "vf": [args.hidden_dim, args.hidden_dim],
        },
        "activation_fn": nn.tanh,
        "optimizer_class": optax.adam,
        "optimizer_kwargs": {"eps": 1e-5},
        "log_std_init": -1.0,
        "ortho_init": False,
    }
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=args.learning_rate,
        n_steps=args.num_steps,
        batch_size=args.batch_size,
        n_epochs=args.update_epochs,
        gamma=args.gamma,
        gae_lambda=args.gae_lambda,
        clip_range=args.clip_coef,
        ent_coef=args.ent_coef,
        vf_coef=args.vf_coef,
        max_grad_norm=args.max_grad_norm,
        target_kl=args.target_kl,
        policy_kwargs=policy_kwargs,
        seed=args.seed,
        device=args.device,
        verbose=1,
    )
    model.learn(
        total_timesteps=int(args.total_timesteps),
        callback=make_callbacks(args, vec_env),
        progress_bar=False,
    )
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(args.model_path))
    vec_env.close()
    if args.wandb_enabled:
        wandb.finish()
    return args.model_path.with_suffix(".zip")


def _split_info(info: dict[str, Any], num_envs: int) -> list[dict[str, Any]]:
    """Split a Gymnasium vector info dict into SB3/SBX's per-env info list."""
    rows: list[dict[str, Any]] = [dict() for _ in range(num_envs)]
    if not isinstance(info, dict):
        return rows
    for key, value in info.items():
        if isinstance(value, dict):
            child_rows = _split_info(value, num_envs)
            for idx, child in enumerate(child_rows):
                rows[idx][key] = child
            continue
        array = np.asarray(value)
        if array.shape[:1] == (num_envs,):
            for idx in range(num_envs):
                rows[idx][key] = array[idx]
        else:
            for row in rows:
                row[key] = value
    return rows


def main() -> None:
    """Train from CLI arguments."""
    train(parse_args())


if __name__ == "__main__":
    main()
