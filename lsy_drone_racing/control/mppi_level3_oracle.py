"""MPPI oracle controller for the Level3 hard-eval track.

This controller is intentionally separate from PPO inference. It uses the
current Level3 observation, samples short attitude-command sequences, rolls them
out with a lightweight point-mass model, scores gate progress and safety, and
applies the first action of the best weighted sequence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import numpy as np
from drone_models.core import load_params
from scipy.spatial.transform import Rotation as R

from lsy_drone_racing.control import Controller

if TYPE_CHECKING:
    from numpy.typing import NDArray


GATE_HALF_SIZE = np.array([0.225, 0.225], dtype=np.float64)
ARENA_LOW = np.array([-2.9, -2.9, 0.05], dtype=np.float64)
ARENA_HIGH = np.array([2.9, 2.9, 2.35], dtype=np.float64)


@dataclass(frozen=True)
class MPPICostWeights:
    """Cost weights for the MPPI rollout objective."""

    gate_axis: float = 12.0
    gate_centerline: float = 30.0
    gate_aperture: float = 48.0
    gate_miss: float = 160.0
    gate_pass_bonus: float = 260.0
    finish_bonus: float = 520.0
    obstacle_clearance: float = 80.0
    bounds: float = 700.0
    altitude: float = 80.0
    tilt: float = 4.0
    thrust: float = 0.15
    smooth: float = 6.0
    speed: float = 0.02
    terminal_gate: float = 80.0


class MPPILevel3Oracle(Controller):
    """Sampling-based Level3 controller returning ``[roll, pitch, yaw, thrust]``."""

    def __init__(self, obs: dict[str, NDArray[np.floating]], info: dict, config: dict):
        """Initialize MPPI parameters and action scaling."""
        super().__init__(obs, info, config)
        if config.env.control_mode != "attitude":
            raise ValueError("MPPILevel3Oracle expects env.control_mode = 'attitude'.")

        drone_params = load_params(config.sim.physics, config.sim.drone_model)
        self.mass = float(drone_params["mass"])
        self.thrust_min = float(drone_params["thrust_min"] * 4)
        self.thrust_max = float(drone_params["thrust_max"] * 4)
        self.hover_thrust = float(np.clip(self.mass * 9.81, self.thrust_min, self.thrust_max))
        rp_limit = np.deg2rad(32.0)
        yaw_limit = np.deg2rad(15.0)
        self.action_low = np.array(
            [-rp_limit, -rp_limit, -yaw_limit, self.thrust_min],
            dtype=np.float32,
        )
        self.action_high = np.array(
            [rp_limit, rp_limit, yaw_limit, self.thrust_max],
            dtype=np.float32,
        )
        self.action_scale = (self.action_high - self.action_low) / 2.0
        self.action_mean = (self.action_high + self.action_low) / 2.0
        self.action_dim = 4

        self.dt = 1.0 / float(config.env.freq)
        self.horizon_steps = int(getattr(config.controller, "mppi_horizon_steps", 42))
        self.num_samples = int(getattr(config.controller, "mppi_num_samples", 256))
        self.temperature = float(getattr(config.controller, "mppi_temperature", 22.0))
        self.elite_frac = float(getattr(config.controller, "mppi_elite_frac", 0.18))
        self.action_lowpass_alpha = float(getattr(config.controller, "mppi_action_alpha", 0.8))
        self.weights = MPPICostWeights()
        self.rng = np.random.default_rng(int(getattr(config.env, "seed", 0)) & 0xFFFFFFFF)

        self._last_action = np.array([0.0, 0.0, 0.0, self.hover_thrust], dtype=np.float32)
        self._last_action_norm = np.zeros(self.action_dim, dtype=np.float32)
        self._warm_sequence = np.repeat(self._last_action[None, :], self.horizon_steps, axis=0)
        self._finished = False
        self._last_best_cost = float("nan")
        self._last_cost_quantiles = np.full(3, float("nan"), dtype=np.float32)

    def compute_control(
        self,
        obs: dict[str, NDArray[np.floating]],
        info: dict | None = None,
    ) -> NDArray[np.floating]:
        """Return one finite attitude action in ``[roll, pitch, yaw, thrust]`` order."""
        if int(np.asarray(obs["target_gate"]).item()) < 0:
            self._finished = True
            action = np.array([0.0, 0.0, self._yaw_from_obs(obs), self.hover_thrust], dtype=np.float32)
            self._record_action(action)
            return action

        guide = self._guide_action(obs)
        candidates = self._sample_action_sequences(guide)
        costs = self._rollout_cost(obs, candidates)
        if not np.isfinite(costs).all():
            costs = np.nan_to_num(costs, nan=1e9, posinf=1e9, neginf=-1e9)

        elite_count = max(1, int(self.num_samples * self.elite_frac))
        elite_idx = np.argpartition(costs, elite_count - 1)[:elite_count]
        elite_costs = costs[elite_idx]
        elite_sequences = candidates[elite_idx]
        shifted = elite_costs - float(np.min(elite_costs))
        weights = np.exp(-shifted / max(self.temperature, 1e-6))
        weights_sum = float(np.sum(weights))
        if weights_sum <= 1e-12 or not np.isfinite(weights_sum):
            chosen_sequence = elite_sequences[int(np.argmin(elite_costs))]
        else:
            chosen_sequence = np.tensordot(weights / weights_sum, elite_sequences, axes=(0, 0))

        self._warm_sequence = np.vstack([chosen_sequence[1:], chosen_sequence[-1:]]).astype(np.float32)
        raw_action = (0.75 * chosen_sequence[0] + 0.25 * guide).astype(np.float32)
        filtered = self._last_action + self.action_lowpass_alpha * (raw_action - self._last_action)
        action = np.clip(filtered, self.action_low, self.action_high).astype(np.float32)
        pos_z = float(np.asarray(obs["pos"], dtype=np.float32)[2])
        target_idx = int(np.asarray(obs["target_gate"]).item())
        if target_idx >= 0:
            target_z = float(np.asarray(obs["gates_pos"], dtype=np.float32)[target_idx, 2])
            vel_z = float(np.asarray(obs["vel"], dtype=np.float32)[2])
            if target_z - pos_z > 0.25 and vel_z < 0.7:
                action[3] = max(action[3], min(self.thrust_max, 1.45 * self.hover_thrust))
            if pos_z < 0.16:
                action[3] = max(action[3], min(self.thrust_max, 1.65 * self.hover_thrust))
        self._last_best_cost = float(np.min(costs))
        self._last_cost_quantiles = np.percentile(costs, [10, 50, 90]).astype(np.float32)
        self._record_action(action)
        return action

    def step_callback(
        self,
        action: NDArray[np.floating],
        obs: dict[str, NDArray[np.floating]],
        reward: float,
        terminated: bool,
        truncated: bool,
        info: dict,
    ) -> bool:
        """Signal completion only when the race is actually finished."""
        if int(np.asarray(obs["target_gate"]).item()) < 0:
            self._finished = True
        return self._finished

    def reset_episode_state(self, obs: dict[str, NDArray[np.floating]]) -> None:
        """Reset warm-start and action history between evaluation seeds."""
        yaw = self._yaw_from_obs(obs)
        self._last_action = np.array([0.0, 0.0, yaw, self.hover_thrust], dtype=np.float32)
        self._last_action_norm = np.zeros(self.action_dim, dtype=np.float32)
        self._warm_sequence = np.repeat(self._last_action[None, :], self.horizon_steps, axis=0)
        self._finished = False
        self._last_best_cost = float("nan")
        self._last_cost_quantiles = np.full(3, float("nan"), dtype=np.float32)

    def mppi_diagnostics(self) -> dict[str, float]:
        """Return latest MPPI diagnostics for evaluators."""
        return {
            "mppi_best_cost": self._last_best_cost,
            "mppi_cost_p10": float(self._last_cost_quantiles[0]),
            "mppi_cost_p50": float(self._last_cost_quantiles[1]),
            "mppi_cost_p90": float(self._last_cost_quantiles[2]),
        }

    @staticmethod
    def quat_to_rotmat(quat: NDArray[np.floating]) -> NDArray[np.float32]:
        """Convert xyzw quaternion to a body-to-world rotation matrix."""
        x, y, z, w = np.asarray(quat, dtype=np.float32)
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z
        return np.array(
            [
                [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
                [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
                [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
            ],
            dtype=np.float32,
        )

    def _record_action(self, action: NDArray[np.floating]) -> None:
        action = np.clip(np.asarray(action, dtype=np.float32), self.action_low, self.action_high)
        self._last_action = action
        self._last_action_norm = np.clip(
            (action - self.action_mean) / np.maximum(self.action_scale, 1e-6),
            -1.0,
            1.0,
        ).astype(np.float32)

    def _guide_action(self, obs: dict[str, NDArray[np.floating]]) -> NDArray[np.float32]:
        pos = np.asarray(obs["pos"], dtype=np.float64)
        vel = np.asarray(obs["vel"], dtype=np.float64)
        target_idx = int(np.asarray(obs["target_gate"]).item())
        gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64)
        gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64)
        target_pos = gates_pos[target_idx]
        target_rot = R.from_quat(gates_quat[target_idx])
        gate_x_axis = target_rot.as_matrix()[:, 0]
        local = target_rot.inv().apply(pos - target_pos)

        if local[0] < -0.25:
            aim = target_pos + 0.30 * gate_x_axis
        elif abs(local[1]) > 0.16 or abs(local[2]) > 0.16:
            aim = target_pos - 0.18 * gate_x_axis
        else:
            aim = target_pos + 0.62 * gate_x_axis

        aim = self._avoid_obstacles(pos, aim, np.asarray(obs["obstacles_pos"], dtype=np.float64))
        to_aim = aim - pos
        desired_vel_xy = np.clip(2.4 * to_aim[:2], -2.2, 2.2)
        desired_acc = np.zeros(3, dtype=np.float64)
        desired_acc[:2] = 2.8 * (desired_vel_xy - vel[:2])
        desired_acc[2] = 5.0 * (aim[2] - pos[2]) - 4.2 * vel[2]
        yaw = 0.0

        roll = np.clip(-desired_acc[1] / 9.81, self.action_low[0], self.action_high[0])
        pitch = np.clip(desired_acc[0] / 9.81, self.action_low[1], self.action_high[1])
        thrust = np.clip(self.mass * (9.81 + desired_acc[2]), self.thrust_min, self.thrust_max)
        if target_pos[2] - pos[2] > 0.25 and vel[2] < 0.7:
            thrust = max(thrust, min(self.thrust_max, 1.55 * self.hover_thrust))
        if pos[2] < 0.16:
            thrust = max(thrust, min(self.thrust_max, 1.75 * self.hover_thrust))
        return np.array([roll, pitch, yaw, thrust], dtype=np.float32)

    def _avoid_obstacles(
        self,
        pos: NDArray[np.floating],
        aim: NDArray[np.floating],
        obstacles_pos: NDArray[np.floating],
    ) -> NDArray[np.float64]:
        adjusted = np.asarray(aim, dtype=np.float64).copy()
        segment = adjusted[:2] - pos[:2]
        seg_norm_sq = float(np.dot(segment, segment))
        if seg_norm_sq < 1e-8:
            return adjusted
        for obstacle in obstacles_pos:
            t = float(np.clip(np.dot(obstacle[:2] - pos[:2], segment) / seg_norm_sq, 0.0, 1.0))
            closest = pos[:2] + t * segment
            clearance = float(np.linalg.norm(obstacle[:2] - closest))
            if clearance < 0.34 and abs(obstacle[2] - pos[2]) < 1.5:
                lateral = np.array([-segment[1], segment[0]], dtype=np.float64)
                lateral /= np.linalg.norm(lateral) + 1e-8
                sign = 1.0 if np.cross(np.append(segment, 0.0), np.append(obstacle[:2] - pos[:2], 0.0))[2] <= 0 else -1.0
                adjusted[:2] += sign * lateral * (0.34 - clearance + 0.12)
        return adjusted

    def _sample_action_sequences(self, guide: NDArray[np.floating]) -> NDArray[np.float32]:
        base = 0.62 * self._warm_sequence + 0.38 * np.asarray(guide, dtype=np.float32)[None, :]
        samples = np.repeat(base[None, :, :], self.num_samples, axis=0)
        noise_scale = np.array(
            [np.deg2rad(12.0), np.deg2rad(12.0), np.deg2rad(4.0), 0.18 * self.hover_thrust],
            dtype=np.float32,
        )
        noise = self.rng.normal(0.0, noise_scale, size=samples.shape).astype(np.float32)
        temporal = np.linspace(1.0, 0.35, self.horizon_steps, dtype=np.float32)[None, :, None]
        samples += noise * temporal
        samples[0] = np.repeat(np.asarray(guide, dtype=np.float32)[None, :], self.horizon_steps, axis=0)
        samples[1] = self._warm_sequence
        return np.clip(samples, self.action_low, self.action_high).astype(np.float32)

    def _rollout_cost(
        self,
        obs: dict[str, NDArray[np.floating]],
        actions: NDArray[np.floating],
    ) -> NDArray[np.float64]:
        n_samples = actions.shape[0]
        pos = np.repeat(np.asarray(obs["pos"], dtype=np.float64)[None, :], n_samples, axis=0)
        vel = np.repeat(np.asarray(obs["vel"], dtype=np.float64)[None, :], n_samples, axis=0)
        target_idx = np.full(n_samples, int(np.asarray(obs["target_gate"]).item()), dtype=np.int32)
        gates_pos = np.asarray(obs["gates_pos"], dtype=np.float64)
        gates_quat = np.asarray(obs["gates_quat"], dtype=np.float64)
        gate_rots = R.from_quat(gates_quat)
        gate_mats = gate_rots.as_matrix()
        gate_inv_mats = np.transpose(gate_mats, (0, 2, 1))
        obstacles_pos = np.asarray(obs["obstacles_pos"], dtype=np.float64)

        cost = np.zeros(n_samples, dtype=np.float64)
        prev_pos = pos.copy()
        prev_action = np.repeat(self._last_action[None, :], n_samples, axis=0)
        finished = np.zeros(n_samples, dtype=bool)

        for step in range(self.horizon_steps):
            action = np.asarray(actions[:, step, :], dtype=np.float64)
            acc = self._action_to_acceleration(action)
            vel = np.clip(vel + acc * self.dt, -4.0, 4.0)
            pos = pos + vel * self.dt

            active = ~finished
            if np.any(active):
                cost[active] += self._stage_cost(
                    pos[active],
                    vel[active],
                    target_idx[active],
                    gates_pos,
                    gate_inv_mats,
                    obstacles_pos,
                    action[active],
                    prev_action[active],
                )
                passed = self._passed_targets(
                    prev_pos[active],
                    pos[active],
                    target_idx[active],
                    gates_pos,
                    gate_inv_mats,
                )
                active_indices = np.flatnonzero(active)
                passed_indices = active_indices[passed]
                if passed_indices.size:
                    cost[passed_indices] -= self.weights.gate_pass_bonus
                    target_idx[passed_indices] += 1
                    just_finished = target_idx[passed_indices] >= len(gates_pos)
                    if np.any(just_finished):
                        finished_indices = passed_indices[just_finished]
                        cost[finished_indices] -= self.weights.finish_bonus
                        finished[finished_indices] = True
                        target_idx[finished_indices] = len(gates_pos) - 1

            prev_pos = pos.copy()
            prev_action = action

        cost += self.weights.terminal_gate * (len(gates_pos) - 1 - target_idx.clip(max=len(gates_pos) - 1))
        cost[finished] -= self.weights.finish_bonus * 0.25
        return cost

    def _action_to_acceleration(self, action: NDArray[np.floating]) -> NDArray[np.float64]:
        roll = action[:, 0]
        pitch = action[:, 1]
        yaw = action[:, 2]
        thrust = action[:, 3]
        cr, sr = np.cos(roll), np.sin(roll)
        cp, sp = np.cos(pitch), np.sin(pitch)
        cy, sy = np.cos(yaw), np.sin(yaw)
        body_z = np.column_stack(
            [
                cy * sp * cr + sy * sr,
                sy * sp * cr - cy * sr,
                cp * cr,
            ]
        )
        acc = body_z * (thrust / self.mass)[:, None]
        acc[:, 2] -= 9.81
        return acc

    def _stage_cost(
        self,
        pos: NDArray[np.floating],
        vel: NDArray[np.floating],
        target_idx: NDArray[np.integer],
        gates_pos: NDArray[np.floating],
        gate_inv_mats: NDArray[np.floating],
        obstacles_pos: NDArray[np.floating],
        action: NDArray[np.floating],
        prev_action: NDArray[np.floating],
    ) -> NDArray[np.float64]:
        target_pos = gates_pos[target_idx]
        local = np.einsum("nij,nj->ni", gate_inv_mats[target_idx], pos - target_pos)
        axis_cost = np.maximum(-local[:, 0], 0.0) ** 2
        centerline_cost = np.sum(local[:, 1:3] ** 2, axis=1)
        centerline_weight = 0.25 + 0.75 * np.exp(-np.maximum(-local[:, 0], 0.0) * 0.7)
        aperture_error = np.maximum(np.abs(local[:, 1:3]) - GATE_HALF_SIZE[None, :] * 0.72, 0.0)
        near_plane = np.exp(-np.abs(local[:, 0]) * 2.0)
        miss_cost = ((local[:, 0] > 0.08) & (np.any(np.abs(local[:, 1:3]) > GATE_HALF_SIZE[None, :], axis=1))).astype(np.float64)

        obs_cost = np.zeros(pos.shape[0], dtype=np.float64)
        for obstacle in obstacles_pos:
            dxy = np.linalg.norm(pos[:, :2] - obstacle[None, :2], axis=1)
            vertical_overlap = (pos[:, 2] > 0.03) & (pos[:, 2] < obstacle[2] + 0.08)
            clearance = np.maximum(0.36 - dxy, 0.0)
            obs_cost += (clearance**2) * vertical_overlap

        low_violation = np.maximum(ARENA_LOW[None, :] - pos, 0.0)
        high_violation = np.maximum(pos - ARENA_HIGH[None, :], 0.0)
        bounds_cost = np.sum(low_violation**2 + high_violation**2, axis=1)
        altitude_cost = np.maximum(0.25 - pos[:, 2], 0.0) ** 2
        tilt_cost = np.sum((action[:, :2] / np.deg2rad(32.0)) ** 2, axis=1)
        thrust_cost = ((action[:, 3] - self.hover_thrust) / max(self.hover_thrust, 1e-6)) ** 2
        smooth_cost = np.sum(((action - prev_action) / np.maximum(self.action_scale, 1e-6)) ** 2, axis=1)
        speed_cost = np.sum(vel**2, axis=1)
        return (
            self.weights.gate_axis * axis_cost
            + self.weights.gate_centerline * centerline_weight * centerline_cost
            + self.weights.gate_aperture * near_plane * np.sum(aperture_error**2, axis=1)
            + self.weights.gate_miss * miss_cost
            + self.weights.obstacle_clearance * obs_cost
            + self.weights.bounds * bounds_cost
            + self.weights.altitude * altitude_cost
            + self.weights.tilt * tilt_cost
            + self.weights.thrust * thrust_cost
            + self.weights.smooth * smooth_cost
            + self.weights.speed * speed_cost
        )

    @staticmethod
    def _passed_targets(
        prev_pos: NDArray[np.floating],
        pos: NDArray[np.floating],
        target_idx: NDArray[np.integer],
        gates_pos: NDArray[np.floating],
        gate_inv_mats: NDArray[np.floating],
    ) -> NDArray[np.bool_]:
        target_pos = gates_pos[target_idx]
        inv = gate_inv_mats[target_idx]
        prev_local = np.einsum("nij,nj->ni", inv, prev_pos - target_pos)
        local = np.einsum("nij,nj->ni", inv, pos - target_pos)
        crossed = (prev_local[:, 0] < 0.0) & (local[:, 0] > 0.0)
        denom = np.maximum(local[:, 0] - prev_local[:, 0], 1e-6)
        alpha = np.clip(-prev_local[:, 0] / denom, 0.0, 1.0)
        yz = prev_local[:, 1:3] + alpha[:, None] * (local[:, 1:3] - prev_local[:, 1:3])
        in_gate = (np.abs(yz[:, 0]) < GATE_HALF_SIZE[0]) & (np.abs(yz[:, 1]) < GATE_HALF_SIZE[1])
        return crossed & in_gate

    @staticmethod
    def _yaw_from_obs(obs: dict[str, NDArray[np.floating]]) -> float:
        quat = np.asarray(obs["quat"], dtype=np.float64)
        return float(np.clip(R.from_quat(quat).as_euler("xyz")[2], -np.pi / 2, np.pi / 2))
