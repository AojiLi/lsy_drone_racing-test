"""Benchmark a pure-JAX/Brax-style v60 command-tracker rollout."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import gymnasium as gym
import jax
import jax.numpy as jnp
import numpy as np
from brax.envs import base as brax_base

from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
    REFERENCE_TRACKER_HISTORY,
    REFERENCE_TRACKER_REWARD_DEFAULTS,
    REFERENCE_TRACKER_WAYPOINT_TYPES,
    action_bounds_from_config,
)
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[1]
COMMAND_GENERATOR_PROFILES = (
    "default",
    "speed_bin_balanced",
    "velocity_contrast_constant_speed",
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3_tracker_free_space.toml")
    parser.add_argument("--seed", type=int, default=26081)
    parser.add_argument("--num-envs", "--num_envs", dest="num_envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--max-episode-steps", type=int, default=500)
    parser.add_argument("--rp-limit-deg", type=float, default=50.0)
    parser.add_argument(
        "--command-generator-profile",
        choices=COMMAND_GENERATOR_PROFILES,
        default="default",
        help="Command reference generator profile; default preserves the original v60 generator.",
    )
    parser.add_argument("--jax-device", default="gpu")
    return parser.parse_args()


def make_base_env(args: argparse.Namespace) -> tuple[Any, Any, jax.Array, jax.Array]:
    """Create the JAX vector race env used by the rollout probe."""
    config = load_config(ROOT / "config" / args.config)
    config.sim.render = False
    config.env.seed = int(args.seed)
    env = gym.make_vec(
        config.env.id,
        num_envs=int(args.num_envs),
        freq=config.env.freq,
        sim_config=config.sim,
        sensor_range=config.env.sensor_range,
        control_mode=config.env.control_mode,
        track=config.env.track,
        disturbances=config.env.get("disturbances"),
        randomizations=config.env.get("randomizations"),
        seed=config.env.seed,
        max_episode_steps=int(args.max_episode_steps),
        device=args.jax_device,
    )
    action_low, action_high = action_bounds_from_config(config, args.rp_limit_deg)
    return (
        env,
        config,
        jnp.asarray(action_low, dtype=jnp.float32),
        jnp.asarray(action_high, dtype=jnp.float32),
    )


def init_policy_params(
    key: jax.Array, obs_dim: int, hidden_dim: int, action_dim: int
) -> dict[str, jax.Array]:
    """Initialize a small random MLP policy for rollout benchmarking."""
    keys = jax.random.split(key, 6)
    return {
        "w1": jax.random.normal(keys[0], (obs_dim, hidden_dim), dtype=jnp.float32) * 0.05,
        "b1": jnp.zeros((hidden_dim,), dtype=jnp.float32),
        "w2": jax.random.normal(keys[1], (hidden_dim, hidden_dim), dtype=jnp.float32) * 0.05,
        "b2": jnp.zeros((hidden_dim,), dtype=jnp.float32),
        "w3": jax.random.normal(keys[2], (hidden_dim, action_dim), dtype=jnp.float32) * 0.01,
        "b3": jnp.zeros((action_dim,), dtype=jnp.float32),
    }


def policy_apply(params: dict[str, jax.Array], obs: jax.Array) -> jax.Array:
    """Run a two-layer tanh policy."""
    hidden = jnp.tanh(obs @ params["w1"] + params["b1"])
    hidden = jnp.tanh(hidden @ params["w2"] + params["b2"])
    return jnp.tanh(hidden @ params["w3"] + params["b3"])


def scale_action_jax(
    action_norm: jax.Array, action_low: jax.Array, action_high: jax.Array
) -> jax.Array:
    """Scale normalized actions into physical attitude commands."""
    clipped = jnp.clip(action_norm, -1.0, 1.0)
    return clipped * ((action_high - action_low) / 2.0) + ((action_high + action_low) / 2.0)


def drop_drone_dim(tree: dict[str, Any]) -> dict[str, jax.Array]:
    """Drop the single-drone dimension from RaceCore observations."""
    return {key: value[:, 0] for key, value in tree.items()}


def safe_normalize(vectors: jax.Array, fallback: jax.Array | None = None) -> jax.Array:
    """Normalize a batch of vectors with per-row fallback."""
    if fallback is None:
        fallback = jnp.tile(jnp.array([[1.0, 0.0, 0.0]], dtype=jnp.float32), (vectors.shape[0], 1))
    norms = jnp.linalg.norm(vectors, axis=1, keepdims=True)
    fallback_norms = jnp.maximum(jnp.linalg.norm(fallback, axis=1, keepdims=True), 1e-6)
    return jnp.where(norms > 1e-6, vectors / jnp.maximum(norms, 1e-6), fallback / fallback_norms)


def quat_to_rotmat(quat: jax.Array) -> jax.Array:
    """Convert xyzw quaternions into body-to-world rotation matrices."""
    x, y, z, w = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    row0 = jnp.stack([1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)], axis=1)
    row1 = jnp.stack([2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)], axis=1)
    row2 = jnp.stack([2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)], axis=1)
    return jnp.stack([row0, row1, row2], axis=1).astype(jnp.float32)


def history_rows(obs: dict[str, jax.Array]) -> jax.Array:
    """Build compact tracker history rows."""
    rot_t = jnp.swapaxes(quat_to_rotmat(obs["quat"]), 1, 2)
    vel_body = jnp.einsum("nij,nj->ni", rot_t, obs["vel"])
    return jnp.concatenate([obs["pos"][:, 2:3], vel_body, obs["ang_vel"]], axis=1).astype(
        jnp.float32
    )


def point_on_polyline(points: jax.Array, distance: jax.Array) -> tuple[jax.Array, jax.Array]:
    """Return batched points and directions on three-point polylines."""
    seg0 = points[:, 1] - points[:, 0]
    seg1 = points[:, 2] - points[:, 1]
    len0 = jnp.linalg.norm(seg0, axis=1)
    len1 = jnp.linalg.norm(seg1, axis=1)
    total = jnp.maximum(len0 + len1, 1e-6)
    d = jnp.clip(distance, 0.0, total)
    use0 = d <= len0
    dir0 = safe_normalize(
        seg0,
        fallback=jnp.tile(jnp.array([[1.0, 0.0, 0.0]], dtype=jnp.float32), (points.shape[0], 1)),
    )
    dir1 = safe_normalize(seg1, fallback=dir0)
    point0 = points[:, 0] + dir0 * d[:, None]
    point1 = points[:, 1] + dir1 * (d - len0)[:, None]
    point = jnp.where(use0[:, None], point0, point1)
    direction = jnp.where(use0[:, None], dir0, dir1)
    return point.astype(jnp.float32), direction.astype(jnp.float32)


def polyline_lengths(points: jax.Array) -> jax.Array:
    """Return total lengths for three-point polylines."""
    return jnp.sum(jnp.linalg.norm(points[:, 1:] - points[:, :-1], axis=2), axis=1)


def uniform_from_bins(
    bin_key: jax.Array, value_key: jax.Array, bins: jax.Array, shape: tuple[int, ...]
) -> jax.Array:
    """Sample uniformly from uniformly selected [low, high] bins."""
    bin_index = jax.random.randint(bin_key, shape, minval=0, maxval=bins.shape[0])
    low = bins[bin_index, 0]
    high = bins[bin_index, 1]
    unit = jax.random.uniform(value_key, shape, minval=0.0, maxval=1.0)
    return low + unit * (high - low)


def sample_command_plans(
    key: jax.Array, origin: jax.Array, dt: float, command_generator_profile: str = "default"
) -> dict[str, jax.Array]:
    """Sample dense v60-style command plans using JAX only."""
    num_envs = origin.shape[0]
    if command_generator_profile not in COMMAND_GENERATOR_PROFILES:
        raise ValueError(f"Unknown command generator profile: {command_generator_profile}")
    key_count = 27 if command_generator_profile == "velocity_contrast_constant_speed" else 24
    if command_generator_profile == "default":
        key_count = 18
    keys = jax.random.split(key, key_count)
    yaw = jax.random.uniform(keys[0], (num_envs,), minval=-jnp.pi, maxval=jnp.pi)
    forward = jnp.stack([jnp.cos(yaw), jnp.sin(yaw), jnp.zeros_like(yaw)], axis=1)
    side = jnp.stack([-forward[:, 1], forward[:, 0], jnp.zeros_like(yaw)], axis=1)
    up = jnp.tile(jnp.array([[0.0, 0.0, 1.0]], dtype=jnp.float32), (num_envs, 1))

    if command_generator_profile == "velocity_contrast_constant_speed":
        contrast_bin = jax.random.randint(keys[1], (num_envs,), minval=0, maxval=3)

        def contrast_uniform(
            value_key: jax.Array, bins: jax.Array, *, scale: float = 1.0
        ) -> jax.Array:
            low = bins[contrast_bin, 0] * scale
            high = bins[contrast_bin, 1] * scale
            unit = jax.random.uniform(value_key, (num_envs,), minval=0.0, maxval=1.0)
            return low + unit * (high - low)

        pass_speed = contrast_uniform(
            keys[2],
            jnp.array([[0.32, 0.44], [0.52, 0.64], [0.72, 0.88]], dtype=jnp.float32),
        )
        brake_entry_speed = jnp.clip(
            pass_speed * jax.random.uniform(keys[3], (num_envs,), minval=0.26, maxval=0.38),
            0.10,
            0.24,
        )
        hold_speed = jax.random.uniform(keys[4], (num_envs,), minval=0.00, maxval=0.05)
        slow_speed = contrast_uniform(
            keys[5],
            jnp.array([[0.16, 0.22], [0.24, 0.31], [0.32, 0.40]], dtype=jnp.float32),
        )
        recover_speed = contrast_uniform(
            keys[6],
            jnp.array([[0.34, 0.46], [0.50, 0.64], [0.68, 0.86]], dtype=jnp.float32),
        )
        pass_dist = jax.random.uniform(keys[7], (num_envs,), minval=0.62, maxval=1.02)
        slow_dist = jax.random.uniform(keys[8], (num_envs,), minval=0.40, maxval=0.74)
        recover_dist = jax.random.uniform(keys[9], (num_envs,), minval=0.55, maxval=0.95)
        pass_curve = jax.random.uniform(keys[10], (num_envs,), minval=-0.16, maxval=0.16)
        slow_curve = jax.random.uniform(keys[11], (num_envs,), minval=-0.07, maxval=0.07)
        recover_turn = jax.random.uniform(keys[12], (num_envs,), minval=-0.48, maxval=0.48)
        altitude_keys = (keys[13], keys[14], keys[15], keys[16], keys[17], keys[18])
        hold_steps = jax.random.randint(keys[19], (num_envs,), minval=46, maxval=81)
        decel_fraction = 0.70
        pass_decel_min_steps = 42
        slow_min_steps = 62
        recover_min_steps = 56
    elif command_generator_profile == "speed_bin_balanced":
        pass_speed = uniform_from_bins(
            keys[1],
            keys[2],
            jnp.array([[0.45, 0.55], [0.55, 0.68], [0.68, 0.82]], dtype=jnp.float32),
            (num_envs,),
        )
        brake_entry_speed = uniform_from_bins(
            keys[3],
            keys[4],
            jnp.array([[0.10, 0.15], [0.15, 0.20], [0.20, 0.24]], dtype=jnp.float32),
            (num_envs,),
        )
        hold_speed = jax.random.uniform(keys[5], (num_envs,), minval=0.00, maxval=0.06)
        slow_speed = uniform_from_bins(
            keys[6],
            keys[7],
            jnp.array([[0.20, 0.26], [0.26, 0.34], [0.34, 0.42]], dtype=jnp.float32),
            (num_envs,),
        )
        recover_speed = uniform_from_bins(
            keys[8],
            keys[9],
            jnp.array([[0.40, 0.52], [0.52, 0.66], [0.66, 0.82]], dtype=jnp.float32),
            (num_envs,),
        )
        pass_dist = jax.random.uniform(keys[10], (num_envs,), minval=0.42, maxval=0.72)
        slow_dist = jax.random.uniform(keys[11], (num_envs,), minval=0.34, maxval=0.66)
        recover_dist = jax.random.uniform(keys[12], (num_envs,), minval=0.40, maxval=0.76)
        pass_curve = jax.random.uniform(keys[13], (num_envs,), minval=-0.18, maxval=0.18)
        slow_curve = jax.random.uniform(keys[14], (num_envs,), minval=-0.08, maxval=0.08)
        recover_turn = jax.random.uniform(keys[15], (num_envs,), minval=-0.55, maxval=0.55)
        altitude_keys = (keys[16], keys[17], keys[18], keys[19], keys[20], keys[21])
        hold_steps = jax.random.randint(keys[22], (num_envs,), minval=44, maxval=73)
        decel_fraction = 0.42
        pass_decel_min_steps = 34
        slow_min_steps = 54
        recover_min_steps = 48
    else:
        pass_speed = jax.random.uniform(keys[1], (num_envs,), minval=0.55, maxval=0.78)
        brake_entry_speed = jax.random.uniform(keys[2], (num_envs,), minval=0.15, maxval=0.24)
        hold_speed = jax.random.uniform(keys[3], (num_envs,), minval=0.02, maxval=0.07)
        slow_speed = jax.random.uniform(keys[4], (num_envs,), minval=0.25, maxval=0.35)
        recover_speed = jax.random.uniform(keys[5], (num_envs,), minval=0.42, maxval=0.62)
        pass_dist = jax.random.uniform(keys[6], (num_envs,), minval=0.30, maxval=0.46)
        slow_dist = jax.random.uniform(keys[7], (num_envs,), minval=0.20, maxval=0.34)
        recover_dist = jax.random.uniform(keys[8], (num_envs,), minval=0.28, maxval=0.48)
        pass_curve = jax.random.uniform(keys[9], (num_envs,), minval=-0.14, maxval=0.14)
        slow_curve = jax.random.uniform(keys[10], (num_envs,), minval=-0.05, maxval=0.05)
        recover_turn = jax.random.uniform(keys[11], (num_envs,), minval=-0.45, maxval=0.45)
        altitude_keys = (keys[12], keys[13], keys[14], keys[15], keys[16], keys[17])
        hold_steps = jnp.full((num_envs,), 36, dtype=jnp.int32)
        decel_fraction = 0.60
        pass_decel_min_steps = 18
        slow_min_steps = 30
        recover_min_steps = 32
    recover_dir = safe_normalize(
        forward * jnp.cos(recover_turn)[:, None] + side * jnp.sin(recover_turn)[:, None]
    )

    def clamp_workspace(point: jax.Array) -> jax.Array:
        low = jnp.array([-2.0, -1.15, 0.55], dtype=jnp.float32)
        high = jnp.array([2.0, 1.15, 1.20], dtype=jnp.float32)
        return jnp.clip(point, low, high).astype(jnp.float32)

    brake_point = clamp_workspace(
        origin
        + forward * pass_dist[:, None]
        + side * pass_curve[:, None]
        + up * jax.random.uniform(altitude_keys[0], (num_envs, 1), minval=-0.03, maxval=0.08)
    )
    pass_mid = clamp_workspace(
        origin
        + forward * (0.5 * pass_dist)[:, None]
        + side
        * (
            0.5 * pass_curve
            + jax.random.uniform(altitude_keys[1], (num_envs,), minval=-0.04, maxval=0.04)
        )[:, None]
        + up * jax.random.uniform(altitude_keys[2], (num_envs, 1), minval=-0.02, maxval=0.05)
    )
    slow_end = clamp_workspace(
        brake_point
        + forward * slow_dist[:, None]
        + side * slow_curve[:, None]
        + up * jax.random.uniform(altitude_keys[3], (num_envs, 1), minval=-0.02, maxval=0.04)
    )
    slow_mid = clamp_workspace(
        brake_point
        + forward * (0.5 * slow_dist)[:, None]
        + side * (0.5 * slow_curve)[:, None]
        + up * jax.random.uniform(altitude_keys[4], (num_envs, 1), minval=-0.01, maxval=0.03)
    )
    recover_end = clamp_workspace(
        slow_end
        + recover_dir * recover_dist[:, None]
        + up * jax.random.uniform(altitude_keys[5], (num_envs, 1), minval=-0.02, maxval=0.06)
    )
    recover_mid = clamp_workspace(slow_end + recover_dir * (0.5 * recover_dist)[:, None])

    pass_points = jnp.stack([origin, pass_mid, brake_point], axis=1)
    slow_points = jnp.stack([brake_point, slow_mid, slow_end], axis=1)
    recover_points = jnp.stack([slow_end, recover_mid, recover_end], axis=1)
    pass_length = polyline_lengths(pass_points)
    pass_decel_start_m = pass_length * decel_fraction
    pass_cruise_steps = jnp.maximum(
        8, jnp.ceil(pass_decel_start_m / jnp.maximum(pass_speed * dt, 1e-4)).astype(jnp.int32)
    )
    pass_decel_length = jnp.maximum(0.0, pass_length - pass_decel_start_m)
    pass_decel_avg_speed = 0.5 * (pass_speed + brake_entry_speed)
    pass_decel_steps = jnp.maximum(
        pass_decel_min_steps,
        jnp.ceil(pass_decel_length / jnp.maximum(pass_decel_avg_speed * dt, 1e-4)).astype(
            jnp.int32
        ),
    )
    pass_steps = pass_cruise_steps + pass_decel_steps
    slow_steps = jnp.maximum(
        slow_min_steps,
        jnp.ceil(polyline_lengths(slow_points) / jnp.maximum(slow_speed * dt, 1e-4)).astype(
            jnp.int32
        ),
    )
    avg_recover_speed = 0.5 * (slow_speed + recover_speed)
    recover_steps = jnp.maximum(
        recover_min_steps,
        jnp.ceil(
            polyline_lengths(recover_points) / jnp.maximum(avg_recover_speed * dt, 1e-4)
        ).astype(jnp.int32),
    )
    return {
        "pass_points": pass_points,
        "brake_point": brake_point,
        "slow_points": slow_points,
        "recover_points": recover_points,
        "pass_speed": pass_speed.astype(jnp.float32),
        "brake_entry_speed": brake_entry_speed.astype(jnp.float32),
        "hold_speed": hold_speed.astype(jnp.float32),
        "slow_speed": slow_speed.astype(jnp.float32),
        "recover_speed": recover_speed.astype(jnp.float32),
        "pass_steps": pass_steps,
        "pass_cruise_steps": pass_cruise_steps,
        "pass_decel_steps": pass_decel_steps,
        "pass_decel_start_m": pass_decel_start_m.astype(jnp.float32),
        "hold_steps": hold_steps,
        "slow_steps": slow_steps,
        "recover_steps": recover_steps,
        "total_steps": pass_steps + hold_steps + slow_steps + recover_steps,
        "approach_heading": safe_normalize(brake_point - origin, fallback=forward),
    }


def pass_distance_and_speed(
    plans: dict[str, jax.Array], step: jax.Array, dt: float
) -> tuple[jax.Array, jax.Array]:
    """Compute v60 pass-through distance and speed with a deceleration ramp."""
    cruise = step < plans["pass_cruise_steps"]
    cruise_distance = step.astype(jnp.float32) * dt * plans["pass_speed"]
    decel_step = jnp.minimum(
        jnp.maximum(step - plans["pass_cruise_steps"], 0), plans["pass_decel_steps"]
    ).astype(jnp.float32)
    decel_steps = jnp.maximum(plans["pass_decel_steps"].astype(jnp.float32), 1.0)
    u = jnp.clip(decel_step / decel_steps, 0.0, 1.0)
    smooth = u * u * (3.0 - 2.0 * u)
    speed = plans["pass_speed"] + (plans["brake_entry_speed"] - plans["pass_speed"]) * smooth
    smooth_integral = u**3 - 0.5 * u**4
    decel_distance = (
        decel_steps
        * dt
        * (
            plans["pass_speed"] * u
            + (plans["brake_entry_speed"] - plans["pass_speed"]) * smooth_integral
        )
    )
    length = polyline_lengths(plans["pass_points"])
    distance = jnp.where(
        cruise, cruise_distance, jnp.minimum(length, plans["pass_decel_start_m"] + decel_distance)
    )
    speed = jnp.where(cruise, plans["pass_speed"], speed)
    return distance.astype(jnp.float32), speed.astype(jnp.float32)


def command_reference(
    plans: dict[str, jax.Array], step: jax.Array, dt: float
) -> dict[str, jax.Array]:
    """Build batched command references for current command steps."""
    pass_steps = plans["pass_steps"]
    hold_end = pass_steps + plans["hold_steps"]
    slow_end = hold_end + plans["slow_steps"]
    total_steps = plans["total_steps"]

    hold_mask = (step >= pass_steps) & (step < hold_end)
    slow_mask = (step >= hold_end) & (step < slow_end)
    recover_mask = (step >= slow_end) & (step < total_steps)
    terminal_mask = ~(step < pass_steps) & ~hold_mask & ~slow_mask & ~recover_mask

    pass_distance, pass_speed = pass_distance_and_speed(plans, step, dt)
    pass_current, pass_heading = point_on_polyline(plans["pass_points"], pass_distance)
    pass_next, _ = point_on_polyline(plans["pass_points"], pass_distance + pass_speed * dt)
    pass_lookahead, _ = point_on_polyline(
        plans["pass_points"], pass_distance + pass_speed * dt * 3.0
    )

    hold_current = plans["brake_point"]
    hold_heading = plans["approach_heading"]
    hold_next = plans["brake_point"] + hold_heading * 0.01
    hold_lookahead = plans["brake_point"] + hold_heading * 0.02

    slow_step = jnp.maximum(step - hold_end, 0)
    slow_distance = slow_step.astype(jnp.float32) * dt * plans["slow_speed"]
    slow_current, slow_heading = point_on_polyline(plans["slow_points"], slow_distance)
    slow_next, _ = point_on_polyline(plans["slow_points"], slow_distance + plans["slow_speed"] * dt)
    slow_lookahead, _ = point_on_polyline(
        plans["slow_points"], slow_distance + plans["slow_speed"] * dt * 3.0
    )

    recover_step = jnp.maximum(step - slow_end, 0)
    recover_alpha = jnp.clip(
        recover_step.astype(jnp.float32)
        / jnp.maximum(plans["recover_steps"].astype(jnp.float32), 1.0),
        0.0,
        1.0,
    )
    smooth = recover_alpha * recover_alpha * (3.0 - 2.0 * recover_alpha)
    recover_speed = plans["slow_speed"] + (plans["recover_speed"] - plans["slow_speed"]) * smooth
    recover_distance = recover_step.astype(jnp.float32) * dt * recover_speed
    recover_current, recover_heading = point_on_polyline(plans["recover_points"], recover_distance)
    recover_next, _ = point_on_polyline(
        plans["recover_points"], recover_distance + recover_speed * dt
    )
    recover_lookahead, _ = point_on_polyline(
        plans["recover_points"], recover_distance + recover_speed * dt * 3.0
    )

    terminal_current = plans["recover_points"][:, -1]
    terminal_heading = safe_normalize(
        plans["recover_points"][:, -1] - plans["recover_points"][:, -2],
        fallback=plans["approach_heading"],
    )
    terminal_next = terminal_current + terminal_heading * 0.01
    terminal_lookahead = terminal_current + terminal_heading * 0.02

    current = pass_current
    next_point = pass_next
    lookahead = pass_lookahead
    heading = pass_heading
    speed = pass_speed
    waypoint_id = jnp.zeros_like(step, dtype=jnp.int32)

    def select(mask: jax.Array, old: jax.Array, new: jax.Array) -> jax.Array:
        return jnp.where(mask[:, None], new, old)

    current = select(hold_mask, current, hold_current)
    next_point = select(hold_mask, next_point, hold_next)
    lookahead = select(hold_mask, lookahead, hold_lookahead)
    heading = select(hold_mask, heading, hold_heading)
    speed = jnp.where(hold_mask, plans["hold_speed"], speed)
    waypoint_id = jnp.where(hold_mask, 1, waypoint_id)

    current = select(slow_mask, current, slow_current)
    next_point = select(slow_mask, next_point, slow_next)
    lookahead = select(slow_mask, lookahead, slow_lookahead)
    heading = select(slow_mask, heading, slow_heading)
    speed = jnp.where(slow_mask, plans["slow_speed"], speed)
    waypoint_id = jnp.where(slow_mask, 2, waypoint_id)

    current = select(recover_mask, current, recover_current)
    next_point = select(recover_mask, next_point, recover_next)
    lookahead = select(recover_mask, lookahead, recover_lookahead)
    heading = select(recover_mask, heading, recover_heading)
    speed = jnp.where(recover_mask, recover_speed, speed)
    waypoint_id = jnp.where(recover_mask, 3, waypoint_id)

    current = select(terminal_mask, current, terminal_current)
    next_point = select(terminal_mask, next_point, terminal_next)
    lookahead = select(terminal_mask, lookahead, terminal_lookahead)
    heading = select(terminal_mask, heading, terminal_heading)
    speed = jnp.where(terminal_mask, plans["hold_speed"], speed)
    waypoint_id = jnp.where(terminal_mask, 1, waypoint_id)

    horizon_direction = safe_normalize(lookahead - current, fallback=heading)
    desired_velocity = horizon_direction * speed[:, None]
    hold_like = waypoint_id == 1
    desired_velocity = jnp.where(hold_like[:, None], 0.0, desired_velocity)
    desired_heading = safe_normalize(heading)
    desired_heading = desired_heading.at[:, 2].set(0.0)
    desired_heading = safe_normalize(desired_heading)
    return {
        "current_point": current.astype(jnp.float32),
        "next_point": next_point.astype(jnp.float32),
        "lookahead_point": lookahead.astype(jnp.float32),
        "desired_velocity": desired_velocity.astype(jnp.float32),
        "desired_heading": desired_heading.astype(jnp.float32),
        "desired_speed": speed.astype(jnp.float32),
        "waypoint_type_id": waypoint_id,
        "stop_signal": hold_like.astype(jnp.float32),
        "brake_mask": hold_like.astype(jnp.float32),
        "slow_through_mask": (waypoint_id == 2).astype(jnp.float32),
    }


def command_observation(
    raw_obs: dict[str, jax.Array],
    reference: dict[str, jax.Array],
    history: jax.Array,
    last_action_norm: jax.Array,
) -> jax.Array:
    """Build command-v3 observations in JAX."""
    pos = raw_obs["pos"]
    vel = raw_obs["vel"]
    rot = quat_to_rotmat(raw_obs["quat"])
    rot_t = jnp.swapaxes(rot, 1, 2)
    ref_points = jnp.concatenate(
        [
            jnp.einsum("nij,nj->ni", rot_t, reference["current_point"] - pos),
            jnp.einsum("nij,nj->ni", rot_t, reference["next_point"] - pos),
            jnp.einsum("nij,nj->ni", rot_t, reference["lookahead_point"] - pos),
        ],
        axis=1,
    )
    desired_velocity_body = jnp.einsum("nij,nj->ni", rot_t, reference["desired_velocity"])
    heading_body = jnp.einsum("nij,nj->ni", rot_t, reference["desired_heading"])
    heading_error = jnp.stack([heading_body[:, 1], heading_body[:, 0]], axis=1)
    waypoint_one_hot = jax.nn.one_hot(
        jnp.clip(reference["waypoint_type_id"], 0, len(REFERENCE_TRACKER_WAYPOINT_TYPES) - 1),
        len(REFERENCE_TRACKER_WAYPOINT_TYPES),
        dtype=jnp.float32,
    )
    semantic = jnp.concatenate(
        [
            waypoint_one_hot,
            reference["stop_signal"][:, None],
            reference["brake_mask"][:, None],
            reference["slow_through_mask"][:, None],
        ],
        axis=1,
    )
    obs = jnp.concatenate(
        [
            pos[:, 2:3],
            jnp.einsum("nij,nj->ni", rot_t, vel),
            raw_obs["ang_vel"],
            rot.reshape(pos.shape[0], 9),
            ref_points,
            desired_velocity_body,
            reference["desired_speed"][:, None],
            heading_error,
            last_action_norm,
            history.reshape(pos.shape[0], -1),
            semantic,
        ],
        axis=1,
    )
    return obs.astype(jnp.float32)


def command_reward(
    prev_obs: dict[str, jax.Array],
    obs: dict[str, jax.Array],
    reference: dict[str, jax.Array],
    action_norm: jax.Array,
    prev_action_norm: jax.Array,
    terminated: jax.Array,
    truncated: jax.Array,
    *,
    reward_coefficients: dict[str, float] | None = None,
) -> tuple[jax.Array, dict[str, jax.Array]]:
    """Compute v60 clean command reward in JAX."""
    coeff = (
        REFERENCE_TRACKER_REWARD_DEFAULTS
        if reward_coefficients is None
        else REFERENCE_TRACKER_REWARD_DEFAULTS | reward_coefficients
    )
    pos = obs["pos"]
    prev_pos = prev_obs["pos"]
    vel = obs["vel"]
    pos_error = jnp.linalg.norm(reference["current_point"] - pos, axis=1)
    prev_error = jnp.linalg.norm(reference["current_point"] - prev_pos, axis=1)
    speed = jnp.linalg.norm(vel, axis=1)
    desired_speed = reference["desired_speed"]
    desired_speed_error = jnp.abs(speed - desired_speed)
    desired_heading = safe_normalize(reference["desired_heading"])
    current_heading = quat_to_rotmat(obs["quat"])[:, :, 0]
    current_heading = current_heading.at[:, 2].set(0.0)
    current_heading = safe_normalize(current_heading)
    heading_error = 1.0 - jnp.clip(jnp.sum(desired_heading * current_heading, axis=1), -1.0, 1.0)
    action_penalty = jnp.mean(jnp.square(action_norm), axis=1)
    delta_penalty = jnp.mean(jnp.square(action_norm - prev_action_norm), axis=1)
    brake_hold_speed_excess = jnp.maximum(0.0, speed - 0.12) * reference["brake_mask"]
    slow_through_speed_error = desired_speed_error * reference["slow_through_mask"]
    slow_through_stop_error = jnp.maximum(0.0, 0.12 - speed) * reference["slow_through_mask"]
    recover_mask = (reference["waypoint_type_id"] == 3).astype(jnp.float32)
    recover_speed_error = desired_speed_error * recover_mask

    segment = reference["lookahead_point"] - reference["current_point"]
    next_segment = reference["next_point"] - reference["current_point"]
    segment = jnp.where(
        jnp.linalg.norm(segment, axis=1, keepdims=True) < 1e-5, next_segment, segment
    )
    direction = safe_normalize(segment, fallback=reference["desired_heading"])
    rel = pos - reference["current_point"]
    prev_rel = prev_pos - reference["current_point"]
    along = jnp.sum(rel * direction, axis=1)
    prev_along = jnp.sum(prev_rel * direction, axis=1)
    cross_track = jnp.linalg.norm(rel - along[:, None] * direction, axis=1)
    along_speed = jnp.sum(vel * direction, axis=1)
    hold_mask = jnp.clip(jnp.maximum(reference["stop_signal"], reference["brake_mask"]), 0.0, 1.0)
    moving_mask = 1.0 - hold_mask
    desired_trajectory_velocity = direction * desired_speed[:, None] * moving_mask[:, None]
    command_velocity_error = jnp.linalg.norm(vel - desired_trajectory_velocity, axis=1)
    command_position_error = hold_mask * pos_error + moving_mask * (
        0.35 * pos_error + 0.65 * cross_track
    )
    point_progress = prev_error - pos_error
    trajectory_progress = along - prev_along
    command_progress = hold_mask * point_progress + moving_mask * trajectory_progress
    moving_along_speed_error = jnp.abs(along_speed - desired_speed) * moving_mask
    moving_reverse_speed = jnp.maximum(0.0, -along_speed) * moving_mask
    brake_hold_overshoot = jnp.maximum(0.0, along) * hold_mask

    rewards = (
        -coeff["pos_error_coef"] * command_position_error
        - coeff["vel_error_coef"] * command_velocity_error
        - coeff["heading_coef"] * heading_error
        - coeff["action_coef"] * action_penalty
        - coeff["action_delta_coef"] * delta_penalty
        + coeff["progress_bonus"] * command_progress
        - coeff["trajectory_cross_track_coef"] * cross_track
        - coeff["trajectory_along_speed_coef"] * moving_along_speed_error
        - coeff["trajectory_reverse_speed_coef"] * moving_reverse_speed
        - coeff["trajectory_overshoot_coef"] * brake_hold_overshoot
        - coeff["semantic_brake_speed_coef"] * brake_hold_speed_excess
        - coeff["semantic_slow_speed_coef"] * slow_through_speed_error
        - coeff["semantic_slow_stop_coef"] * slow_through_stop_error
        - coeff["semantic_recover_speed_coef"] * recover_speed_error
    )
    rewards = jnp.where(terminated & ~truncated, rewards - coeff["crash_penalty"], rewards)
    metrics = {
        "reward_mean": jnp.mean(rewards),
        "command_position_error": jnp.mean(command_position_error),
        "command_velocity_error": jnp.mean(command_velocity_error),
        "cross_track_error": jnp.mean(cross_track),
        "action_delta_penalty": jnp.mean(delta_penalty),
    }
    return rewards.astype(jnp.float32), metrics


def make_initial_state(
    env: Any,
    raw_obs: dict[str, jax.Array],
    key: jax.Array,
    dt: float,
    command_generator_profile: str = "default",
) -> brax_base.State:
    """Create a Brax-style State carrying race data and v60 tracker state."""
    plans = sample_command_plans(key, raw_obs["pos"], dt, command_generator_profile)
    command_steps = jnp.zeros((raw_obs["pos"].shape[0],), dtype=jnp.int32)
    history_row = history_rows(raw_obs)
    history = jnp.repeat(history_row[:, None, :], REFERENCE_TRACKER_HISTORY, axis=1)
    last_action_norm = jnp.zeros((raw_obs["pos"].shape[0], 4), dtype=jnp.float32)
    reference = command_reference(plans, command_steps, dt)
    obs = command_observation(raw_obs, reference, history, last_action_norm)
    zero_metric = jnp.array(0.0, dtype=jnp.float32)
    return brax_base.State(
        pipeline_state=env.data,
        obs=obs,
        reward=jnp.zeros((raw_obs["pos"].shape[0],), dtype=jnp.float32),
        done=jnp.zeros((raw_obs["pos"].shape[0],), dtype=jnp.float32),
        metrics={
            "reward_mean": zero_metric,
            "command_position_error": zero_metric,
            "command_velocity_error": zero_metric,
            "cross_track_error": zero_metric,
            "action_delta_penalty": zero_metric,
        },
        info={
            "raw_obs": raw_obs,
            "plans": plans,
            "command_steps": command_steps,
            "history": history,
            "last_action_norm": last_action_norm,
            "reference": reference,
        },
    )


def build_rollout_fn(
    step_fn: Any, action_low: jax.Array, action_high: jax.Array, *, dt: float, num_steps: int
) -> Any:
    """Build the jitted pure-JAX rollout scan."""

    def rollout_step(
        state: brax_base.State, policy_params: dict[str, jax.Array]
    ) -> tuple[brax_base.State, dict[str, jax.Array]]:
        action_norm = policy_apply(policy_params, state.obs)
        sim_action = scale_action_jax(action_norm, action_low, action_high)
        next_race_data, (raw_obs_full, _sparse_reward, terminated_full, truncated_full, _info) = (
            step_fn(state.pipeline_state, sim_action)
        )
        raw_obs = drop_drone_dim(raw_obs_full)
        terminated = terminated_full[:, 0]
        truncated = truncated_full[:, 0]
        done = terminated | truncated
        reference = state.info["reference"]
        rewards, reward_metrics = command_reward(
            state.info["raw_obs"],
            raw_obs,
            reference,
            action_norm,
            state.info["last_action_norm"],
            terminated,
            truncated,
        )
        history_row = history_rows(raw_obs)
        history = jnp.concatenate(
            [state.info["history"][:, 1:, :], history_row[:, None, :]], axis=1
        )
        reset_history = jnp.repeat(history_row[:, None, :], REFERENCE_TRACKER_HISTORY, axis=1)
        history = jnp.where(done[:, None, None], reset_history, history)
        last_action_norm = jnp.where(done[:, None], jnp.zeros_like(action_norm), action_norm)
        command_steps = jnp.where(done, 0, state.info["command_steps"] + 1)
        new_reference = command_reference(state.info["plans"], command_steps, dt)
        tracker_obs = command_observation(raw_obs, new_reference, history, last_action_norm)
        next_state = state.replace(
            pipeline_state=next_race_data,
            obs=tracker_obs,
            reward=rewards,
            done=done.astype(jnp.float32),
            metrics=reward_metrics,
            info={
                "raw_obs": raw_obs,
                "plans": state.info["plans"],
                "command_steps": command_steps,
                "history": history,
                "last_action_norm": last_action_norm,
                "reference": new_reference,
            },
        )
        return next_state, {
            "reward_mean": reward_metrics["reward_mean"],
            "done_mean": jnp.mean(done.astype(jnp.float32)),
            "obs_abs_mean": jnp.mean(jnp.abs(tracker_obs)),
        }

    @jax.jit
    def rollout(
        state: brax_base.State, policy_params: dict[str, jax.Array]
    ) -> tuple[brax_base.State, dict[str, jax.Array]]:
        return jax.lax.scan(
            lambda carry, _: rollout_step(carry, policy_params), state, None, length=num_steps
        )

    return rollout


def main() -> None:
    """Run the benchmark."""
    args = parse_args()
    device = jax.devices(args.jax_device)[0]
    with jax.default_device(device):
        env, config, action_low, action_high = make_base_env(args)
        raw_obs_np, _info = env.reset(seed=args.seed)
        raw_obs = {key: jax.device_put(value, device) for key, value in raw_obs_np.items()}
        init_key, policy_key = jax.random.split(jax.random.PRNGKey(args.seed))
        state = make_initial_state(
            env,
            raw_obs,
            init_key,
            dt=1.0 / float(config.env.freq),
            command_generator_profile=args.command_generator_profile,
        )
        policy_params = init_policy_params(
            policy_key, REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM, args.hidden_dim, 4
        )
        rollout = build_rollout_fn(
            env._step,  # noqa: SLF001
            action_low,
            action_high,
            dt=1.0 / float(config.env.freq),
            num_steps=args.num_steps,
        )

        compile_start = time.perf_counter()
        state, metrics = rollout(state, policy_params)
        jax.tree_util.tree_map(lambda value: value.block_until_ready(), state)
        jax.tree_util.tree_map(lambda value: value.block_until_ready(), metrics)
        compile_elapsed = time.perf_counter() - compile_start

        timed = []
        for _ in range(args.repeat):
            start = time.perf_counter()
            state, metrics = rollout(state, policy_params)
            jax.tree_util.tree_map(lambda value: value.block_until_ready(), state)
            jax.tree_util.tree_map(lambda value: value.block_until_ready(), metrics)
            timed.append(time.perf_counter() - start)

    steps = int(args.num_envs) * int(args.num_steps)
    mean_elapsed = float(np.mean(timed))
    median_elapsed = float(np.median(timed))
    print(
        {
            "backend": "pure_jax_brax_state_rollout",
            "config": args.config,
            "num_envs": int(args.num_envs),
            "num_steps": int(args.num_steps),
            "command_generator_profile": args.command_generator_profile,
            "steps_per_rollout": steps,
            "compile_plus_first_run_s": compile_elapsed,
            "mean_run_s": mean_elapsed,
            "median_run_s": median_elapsed,
            "mean_steps_per_s": steps / mean_elapsed,
            "median_steps_per_s": steps / median_elapsed,
            "run_times_s": [float(value) for value in timed],
            "repeat": int(args.repeat),
            "reward_mean_last": float(metrics["reward_mean"][-1]),
            "done_mean_last": float(metrics["done_mean"][-1]),
            "obs_abs_mean_last": float(metrics["obs_abs_mean"][-1]),
        }
    )
    env.close()


if __name__ == "__main__":
    main()
