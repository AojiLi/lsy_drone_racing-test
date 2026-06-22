"""Check Level3 training/inference action scaling parity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gymnasium
import jax.numpy as jp
import numpy as np
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.control import ppo_level3_inference
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import NormalizeVectorActions
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]


def inject_checkpoint(checkpoint: Path) -> None:
    """Point ppo_level3_inference at an explicit checkpoint."""
    control_dir = Path(ppo_level3_inference.__file__).parent
    ppo_level3_inference.MODEL_NAME = str(checkpoint.resolve().relative_to(control_dir))


def make_env(config_name: str) -> tuple[Any, Any]:
    """Create a single hard-eval environment."""
    config = load_config(ROOT / "config" / config_name)
    config.sim.render = False
    env = gymnasium.make(
        config.env.id,
        freq=config.env.freq,
        sim_config=config.sim,
        sensor_range=config.env.sensor_range,
        control_mode=config.env.control_mode,
        track=config.env.track,
        disturbances=config.env.get("disturbances"),
        randomizations=config.env.get("randomizations"),
        seed=config.env.seed,
    )
    return JaxToNumpy(env), config


def max_abs_diff(a: Any, b: Any) -> float:
    """Return max absolute difference between arrays."""
    return float(np.max(np.abs(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64))))


def run_check(
    *,
    config_name: str,
    checkpoint: Path,
    seed: int,
    samples: int,
    tolerance: float,
) -> dict[str, Any]:
    """Run action-scaling parity checks."""
    inject_checkpoint(checkpoint)
    env, config = make_env(config_name)
    try:
        obs, info = env.reset(seed=seed)
        controller = ppo_level3_inference.PPOLevel2Inference(obs, info, config)
        action_low = np.asarray(env.action_space.low, dtype=np.float32)
        action_high = np.asarray(env.action_space.high, dtype=np.float32)
        train_scale = (action_high - action_low) / 2.0
        train_mean = (action_high + action_low) / 2.0
        controller_low = np.asarray(controller.action_low, dtype=np.float32)
        controller_high = np.asarray(controller.action_high, dtype=np.float32)
        rng = np.random.default_rng(seed)
        actions_norm = rng.uniform(-1.5, 1.5, size=(samples, controller.action_dim)).astype(
            np.float32
        )
        train_scaled = np.asarray(
            NormalizeVectorActions._scale_actions(
                jp.asarray(actions_norm), jp.asarray(train_scale), jp.asarray(train_mean)
            ),
            dtype=np.float32,
        )
        infer_scaled = np.stack(
            [controller._scale_action(action_norm) for action_norm in actions_norm], axis=0
        ).astype(np.float32)
        diffs = {
            "action_low_max_abs_diff": max_abs_diff(action_low, controller_low),
            "action_high_max_abs_diff": max_abs_diff(action_high, controller_high),
            "action_scale_max_abs_diff": max_abs_diff(train_scale, controller.action_scale),
            "action_mean_max_abs_diff": max_abs_diff(train_mean, controller.action_mean),
            "sample_scaled_max_abs_diff": max_abs_diff(train_scaled, infer_scaled),
            "sample_scaled_mean_abs_diff": float(
                np.mean(np.abs(train_scaled.astype(np.float64) - infer_scaled.astype(np.float64)))
            ),
        }
        return {
            "config": config_name,
            "checkpoint": str(checkpoint),
            "seed": seed,
            "samples": samples,
            "tolerance": tolerance,
            "env_action_low": action_low.tolist(),
            "env_action_high": action_high.tolist(),
            "controller_action_low": controller_low.tolist(),
            "controller_action_high": controller_high.tolist(),
            "diffs": diffs,
            "clean": all(value <= tolerance for value in diffs.values()),
        }
    finally:
        env.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line args."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_dr.toml")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--samples", type=int, default=1000)
    parser.add_argument("--tolerance", type=float, default=1e-6)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    """Run the diagnostic and write JSON."""
    args = parse_args()
    summary = run_check(
        config_name=args.config,
        checkpoint=args.checkpoint,
        seed=args.seed,
        samples=args.samples,
        tolerance=args.tolerance,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
