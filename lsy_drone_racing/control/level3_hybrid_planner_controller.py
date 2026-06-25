"""Completion-first Level3 hybrid controller.

This controller keeps the Level3 track unchanged and uses a deterministic upper
planner only to create observations for a stable Level2 PPO tracker. The action
source remains the Level2 PPO network, which outputs roll/pitch/yaw/thrust.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("SCIPY_ARRAY_API", "1")

import numpy as np
import torch
from drone_models.core import load_params
from scipy.spatial.transform import Rotation as R

from lsy_drone_racing.control import Controller
from lsy_drone_racing.control.ppo_level2_inference import (
    GATE_CORNERS_LOCAL,
    HISTORY_DIM,
    N_HISTORY,
    PPOAgent,
)
from lsy_drone_racing.control.ppo_level2_observation import (
    LEGACY_OBSERVATION_LAYOUT,
    OBSERVATION_LAYOUT,
    checkpoint_hidden_dim,
    unpack_checkpoint,
)


TRACKER_MODEL_NAME = (
    "checkpoints/level2_DR_latencyobs_middlemanuever/"
    "level2_DR_latencyobs_middlemanuever_final.ckpt"
)
OBSTACLE_LAYOUT = "obstacle_heading_xy_v1"
EXPECTED_OBS_DIM = 103
SENSOR_SLOWDOWN_RANGE_M = 0.70
PLANNER_REPLAN_RANGE_M = 1.00
MAX_ROLL_PITCH_RAD = np.deg2rad(50.0)
MAX_YAW_RAD = np.deg2rad(90.0)
MIN_COMPLETION_THRUST = 0.32


@dataclass(frozen=True)
class PlannerReference:
    target_gate: int
    phase_id: int
    phase: str
    reference_point: np.ndarray
    reference_velocity: np.ndarray
    desired_heading: np.ndarray
    desired_speed: float
    aperture_offset_yz: np.ndarray
    gate_distance: float
    gate_local_position: np.ndarray


class Level3HybridPlannerController(Controller):
    """Planner-guided Level2 PPO tracker for Level3 completion attempts."""

    def __init__(self, obs: dict[str, Any], info: dict[str, Any], config: Any) -> None:
        super().__init__(obs, info, config)
        if config.env.control_mode != "attitude":
            raise ValueError("Level3HybridPlannerController requires attitude control.")

        self._device = torch.device("cpu")
        drone_params = load_params(config.sim.physics, config.sim.drone_model)
        self.thrust_min = float(drone_params["thrust_min"] * 4)
        self.thrust_max = float(drone_params["thrust_max"] * 4)
        self.action_low = np.array(
            [-np.pi / 2.0, -np.pi / 2.0, -np.pi / 2.0, self.thrust_min], dtype=np.float32
        )
        self.action_high = np.array(
            [np.pi / 2.0, np.pi / 2.0, np.pi / 2.0, self.thrust_max],
            dtype=np.float32,
        )
        self.action_scale = (self.action_high - self.action_low) / 2.0
        self.action_mean = (self.action_high + self.action_low) / 2.0
        self._action_scale = self.action_scale
        self._action_mean = self.action_mean
        self.action_dim = 4
        self._n_gates = int(len(obs["gates_pos"]))
        self._n_obstacles = int(len(obs["obstacles_pos"]))
        self._obs_dim = (
            1
            + 3
            + 3
            + 9
            + 1
            + 12
            + 12
            + 12
            + 4 * self._n_obstacles
            + self._n_gates
            + 4
            + N_HISTORY * HISTORY_DIM
        )
        if self._obs_dim != EXPECTED_OBS_DIM:
            raise ValueError(
                f"Level2 tracker expects obs_dim={EXPECTED_OBS_DIM}, got {self._obs_dim}."
            )
        self.obs_dim = self._obs_dim
        self.observation_layout = OBSERVATION_LAYOUT
        self._include_prev_gate = True

        self._tracker = self._load_tracker()
        self._history = [self._basic_history(obs) for _ in range(N_HISTORY)]
        self._last_action_norm = np.zeros(4, dtype=np.float32)
        self._step_count = 0
        self._last_reference = self._plan_reference(obs)
        self._last_diagnostics: dict[str, float] = {}
        self._finished = False

    def compute_control(self, obs: dict[str, Any], info: dict[str, Any] | None = None) -> np.ndarray:
        if int(obs.get("target_gate", -1)) < 0:
            self._finished = True
            return self._finish_hold_action(obs)

        self._step_count += 1
        reference = self._plan_reference(obs)
        synthetic_obs = self._build_virtual_gate_observation(obs, reference)
        tracker_obs = self._obs_rl(synthetic_obs)

        with torch.no_grad():
            obs_tensor = torch.as_tensor(
                tracker_obs, dtype=torch.float32, device=self._device
            ).unsqueeze(0)
            action_norm, *_ = self._tracker.get_action_and_value(obs_tensor, deterministic=True)

        action_norm_np = action_norm.squeeze(0).detach().cpu().numpy().astype(np.float32)
        if not np.isfinite(action_norm_np).all():
            action_norm_np = np.zeros(self.action_dim, dtype=np.float32)
        action = self._scale_action(action_norm_np)
        action = self._completion_safety_clip(action, obs, reference)
        self._last_action_norm = self._normalize_action(action)
        self._update_history(obs)
        self._last_reference = reference
        self._last_diagnostics = self._diagnostics(obs, reference, action)
        return action.astype(np.float32)

    def step_callback(
        self,
        action: np.ndarray,
        obs: dict[str, Any],
        reward: float,
        terminated: bool,
        truncated: bool,
        info: dict[str, Any],
    ) -> bool:
        self._finished = bool(terminated or truncated or int(obs.get("target_gate", -1)) < 0)
        return self._finished

    def mppi_diagnostics(self) -> dict[str, float]:
        return dict(self._last_diagnostics)

    def reset_episode_state(self, obs: dict[str, Any] | None = None) -> None:
        if obs is not None:
            self._history = [self._basic_history(obs) for _ in range(N_HISTORY)]
            self._last_reference = self._plan_reference(obs)
        self._last_action_norm = np.zeros(4, dtype=np.float32)
        self._last_diagnostics = {}
        self._step_count = 0
        self._finished = False

    def _load_tracker(self) -> PPOAgent:
        model_path = Path(__file__).resolve().parent / TRACKER_MODEL_NAME
        if not model_path.exists():
            raise FileNotFoundError(f"Level2 tracker checkpoint not found: {model_path}")

        checkpoint = torch.load(model_path, map_location=self._device, weights_only=False)
        state_dict, layout = unpack_checkpoint(checkpoint)
        if layout not in (LEGACY_OBSERVATION_LAYOUT, OBSERVATION_LAYOUT):
            raise ValueError(f"Unsupported Level2 tracker observation layout {layout!r}.")

        obs_dim = int(state_dict["actor_mean.0.weight"].shape[1])
        if obs_dim != EXPECTED_OBS_DIM:
            raise ValueError(
                f"Unsupported Level2 tracker obs_dim={obs_dim}; expected {EXPECTED_OBS_DIM}."
            )

        action_dim = int(state_dict["actor_mean.4.weight"].shape[0])
        hidden_dim = checkpoint_hidden_dim(checkpoint, state_dict)
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.observation_layout = layout
        self._include_prev_gate = True
        agent = PPOAgent((obs_dim,), (action_dim,), hidden_dim=hidden_dim).to(self._device)
        agent.load_state_dict(state_dict, strict=True)
        agent.eval()
        return agent

    def _plan_reference(self, obs: dict[str, Any]) -> PlannerReference:
        pos = np.asarray(obs["pos"], dtype=np.float32)
        vel = np.asarray(obs["vel"], dtype=np.float32)
        target_gate = int(np.clip(obs.get("target_gate", 0), 0, self._n_gates - 1))
        gate_pos = np.asarray(obs["gates_pos"][target_gate], dtype=np.float32)
        gate_rot = R.from_quat(np.asarray(obs["gates_quat"][target_gate], dtype=np.float32))
        gate_local = gate_rot.inv().apply(pos - gate_pos).astype(np.float32)
        gate_distance = float(np.linalg.norm(pos - gate_pos))
        aperture_yz = self._select_aperture_offset(obs, target_gate, gate_rot)
        corrected_yz = np.clip(
            aperture_yz - 0.65 * (gate_local[1:3] - aperture_yz),
            -0.16,
            0.16,
        ).astype(np.float32)

        if pos[2] < 0.35 and self._step_count < 100:
            phase = "takeoff"
            phase_id = 0
            local_ref = np.array([-0.60, aperture_yz[0], aperture_yz[1]], dtype=np.float32)
            desired_speed = 0.45
        elif gate_local[0] < -PLANNER_REPLAN_RANGE_M:
            phase = "cruise"
            phase_id = 1
            local_ref = np.array([-0.72, aperture_yz[0], aperture_yz[1]], dtype=np.float32)
            desired_speed = 0.95
        elif gate_local[0] < -SENSOR_SLOWDOWN_RANGE_M:
            phase = "visibility_slowdown"
            phase_id = 2
            local_ref = np.array([-0.45, aperture_yz[0], aperture_yz[1]], dtype=np.float32)
            desired_speed = 0.62
        elif gate_local[0] < -0.30:
            phase = "align"
            phase_id = 3
            local_ref = np.array([-0.24, corrected_yz[0], corrected_yz[1]], dtype=np.float32)
            lateral_error = float(np.linalg.norm(gate_local[1:3] - aperture_yz))
            desired_speed = 0.45 if lateral_error > 0.24 else 0.58
        elif gate_local[0] < 0.35:
            phase = "cross"
            phase_id = 4
            lateral_error = float(np.linalg.norm(gate_local[1:3] - aperture_yz))
            cross_yz = corrected_yz if lateral_error > 0.09 else aperture_yz
            local_ref = np.array([0.36, cross_yz[0], cross_yz[1]], dtype=np.float32)
            desired_speed = 0.68 if lateral_error > 0.09 else 0.78
        else:
            phase = "recover"
            phase_id = 5
            local_ref = np.array([0.72, aperture_yz[0], aperture_yz[1]], dtype=np.float32)
            desired_speed = 0.88

        reference_point = gate_pos + gate_rot.apply(local_ref)
        to_reference = reference_point - pos
        direction = self._safe_normalize(to_reference)
        heading = gate_rot.apply(np.array([1.0, 0.0, 0.0], dtype=np.float32))
        heading[2] = 0.0
        heading = self._safe_normalize(heading, fallback=gate_rot.apply([1.0, 0.0, 0.0]))

        if gate_distance <= 1.05:
            closing_speed = float(np.dot(vel, heading))
            if closing_speed > desired_speed + 0.25:
                desired_speed *= 0.75

        reference_velocity = direction * desired_speed
        return PlannerReference(
            target_gate=target_gate,
            phase_id=phase_id,
            phase=phase,
            reference_point=reference_point.astype(np.float32),
            reference_velocity=reference_velocity.astype(np.float32),
            desired_heading=heading.astype(np.float32),
            desired_speed=float(desired_speed),
            aperture_offset_yz=aperture_yz.astype(np.float32),
            gate_distance=gate_distance,
            gate_local_position=gate_local,
        )

    def _select_aperture_offset(
        self, obs: dict[str, Any], target_gate: int, gate_rot: R
    ) -> np.ndarray:
        gate_pos = np.asarray(obs["gates_pos"][target_gate], dtype=np.float32)
        candidates = np.array(
            [
                [0.00, 0.00],
                [0.12, 0.00],
                [-0.12, 0.00],
                [0.00, 0.12],
                [0.00, -0.12],
                [0.12, 0.10],
                [-0.12, 0.10],
                [0.12, -0.10],
                [-0.12, -0.10],
            ],
            dtype=np.float32,
        )
        detected = np.asarray(obs.get("obstacles_visited", np.ones(self._n_obstacles)), dtype=bool)
        obstacles = np.asarray(obs["obstacles_pos"], dtype=np.float32)
        best_offset = candidates[0]
        best_score = -np.inf
        for offset in candidates:
            clearance = 3.0
            for obstacle_idx, obstacle_pos in enumerate(obstacles):
                if obstacle_idx < len(detected) and not detected[obstacle_idx]:
                    continue
                obstacle_local = gate_rot.inv().apply(obstacle_pos - gate_pos)
                near_corridor = -0.65 <= obstacle_local[0] <= 0.85
                if not near_corridor:
                    continue
                clearance = min(clearance, float(np.linalg.norm(obstacle_local[1:3] - offset)))
            center_penalty = 0.20 * float(np.linalg.norm(offset))
            score = clearance - center_penalty
            if score > best_score:
                best_score = score
                best_offset = offset
        return np.clip(best_offset, -0.16, 0.16).astype(np.float32)

    def _build_virtual_gate_observation(
        self, obs: dict[str, Any], reference: PlannerReference
    ) -> dict[str, Any]:
        synthetic = {
            key: np.array(value, copy=True) if isinstance(value, np.ndarray) else value
            for key, value in obs.items()
        }
        gates_pos = np.array(obs["gates_pos"], dtype=np.float32, copy=True)
        gates_quat = np.array(obs["gates_quat"], dtype=np.float32, copy=True)

        current_idx = reference.target_gate
        previous_idx = max(current_idx - 1, 0)
        next_idx = min(current_idx + 1, self._n_gates - 1)
        heading = self._safe_normalize(reference.desired_heading)
        yaw = float(np.arctan2(heading[1], heading[0]))
        virtual_quat = R.from_euler("z", yaw).as_quat().astype(np.float32)
        post_gate = reference.reference_point + heading * max(0.42, reference.desired_speed * 0.55)
        pre_gate = np.asarray(obs["pos"], dtype=np.float32) - heading * 0.24

        gates_pos[current_idx] = reference.reference_point
        gates_quat[current_idx] = virtual_quat
        if current_idx > 0:
            gates_pos[previous_idx] = pre_gate.astype(np.float32)
            gates_quat[previous_idx] = virtual_quat
        if next_idx != current_idx:
            gates_pos[next_idx] = post_gate.astype(np.float32)
            gates_quat[next_idx] = virtual_quat

        synthetic["gates_pos"] = gates_pos
        synthetic["gates_quat"] = gates_quat
        return synthetic

    def _obs_rl(self, obs: dict[str, Any]) -> np.ndarray:
        pos = np.asarray(obs["pos"], dtype=np.float32)
        quat = np.asarray(obs["quat"], dtype=np.float32)
        vel = np.asarray(obs["vel"], dtype=np.float32)
        ang_vel = np.asarray(obs["ang_vel"], dtype=np.float32)
        rot = self.quat_to_rotmat(quat)
        rot_t = rot.T
        vel_body = rot_t @ vel
        raw_target_gate = int(np.asarray(obs.get("target_gate", 0)).item())
        target_gate = int(np.clip(raw_target_gate, 0, self._n_gates - 1))
        active_target_gate = self._n_gates - 1 if raw_target_gate < 0 else target_gate
        prev_gate = max(active_target_gate - 1, 0)
        gate_prev = self._gate_corners_body(obs, prev_gate, pos, rot_t)
        if active_target_gate <= 0:
            gate_prev = np.zeros_like(gate_prev)
        gate_current = self._gate_corners_body(obs, target_gate, pos, rot_t)
        next_gate = min(max(target_gate, 0) + 1, self._n_gates - 1)
        gate_next = self._gate_corners_body(obs, next_gate, pos, rot_t)
        obstacles = self._obstacle_heading_xy(obs, pos, rot)
        target_progress = np.array(
            [self._n_gates if raw_target_gate < 0 else target_gate], dtype=np.float32
        ) / self._n_gates
        gates_visited = np.asarray(obs.get("gates_visited", np.zeros(self._n_gates)), dtype=np.float32)
        if gates_visited.shape[0] != self._n_gates:
            gates_visited = np.resize(gates_visited, self._n_gates).astype(np.float32)
        history = np.concatenate(self._history).astype(np.float32)

        obs_parts = [
            pos[2:3],
            vel_body,
            ang_vel,
            rot.reshape(-1),
            target_progress,
            gate_prev,
            gate_current,
            gate_next,
            obstacles,
            gates_visited.astype(np.float32),
            self._last_action_norm,
            history,
        ]
        obs_rl = np.concatenate(obs_parts).astype(np.float32)
        if obs_rl.shape[0] != self._obs_dim:
            raise ValueError(f"Tracker observation dim mismatch: {obs_rl.shape[0]} != {self._obs_dim}")
        return obs_rl

    def _gate_corners_body(
        self, obs: dict[str, Any], gate_idx: int, pos: np.ndarray, rot_t: np.ndarray
    ) -> np.ndarray:
        gate_idx = gate_idx % self._n_gates
        gate_pos = np.asarray(obs["gates_pos"][gate_idx], dtype=np.float32)
        gate_quat = np.asarray(obs["gates_quat"][gate_idx], dtype=np.float32)
        gate_rot = self.quat_to_rotmat(gate_quat)
        corners_world = gate_pos[None, :] + GATE_CORNERS_LOCAL @ gate_rot.T
        return ((corners_world - pos[None, :]) @ rot_t.T).reshape(-1).astype(np.float32)

    def _obstacle_heading_xy(self, obs: dict[str, Any], pos: np.ndarray, rot: np.ndarray) -> np.ndarray:
        obstacle_pos = np.asarray(obs["obstacles_pos"], dtype=np.float32)
        relative_xy = obstacle_pos[:, :2] - pos[None, :2]
        heading_forward = np.array(rot[:2, 0], dtype=np.float32, copy=True)
        heading_forward /= max(float(np.linalg.norm(heading_forward)), 1e-6)
        heading_left = np.array([-heading_forward[1], heading_forward[0]], dtype=np.float32)
        relative_forward = relative_xy @ heading_forward
        relative_left = relative_xy @ heading_left
        distance_xy = np.linalg.norm(relative_xy, axis=-1)
        detected = np.asarray(obs.get("obstacles_visited", np.ones(len(obstacle_pos))), dtype=np.float32)
        features = np.stack([relative_forward, relative_left, distance_xy, detected], axis=-1)
        return features.reshape(-1).astype(np.float32)

    def _basic_history(self, obs: dict[str, Any]) -> np.ndarray:
        return np.concatenate(
            [
                np.asarray(obs["pos"], dtype=np.float32),
                np.asarray(obs["quat"], dtype=np.float32),
                np.asarray(obs["vel"], dtype=np.float32),
                np.asarray(obs["ang_vel"], dtype=np.float32),
            ]
        ).astype(np.float32)

    def _update_history(self, obs: dict[str, Any]) -> None:
        self._history.append(self._basic_history(obs))
        self._history = self._history[-N_HISTORY:]

    def _scale_action(self, action_norm: np.ndarray) -> np.ndarray:
        return np.clip(action_norm, -1.0, 1.0) * self._action_scale + self._action_mean

    def _normalize_action(self, action: np.ndarray) -> np.ndarray:
        return np.clip((action - self._action_mean) / self._action_scale, -1.0, 1.0).astype(np.float32)

    def _completion_safety_clip(
        self, action: np.ndarray, obs: dict[str, Any], reference: PlannerReference
    ) -> np.ndarray:
        clipped = np.asarray(action, dtype=np.float32).copy()
        clipped[0] = np.clip(clipped[0], -MAX_ROLL_PITCH_RAD, MAX_ROLL_PITCH_RAD)
        clipped[1] = np.clip(clipped[1], -MAX_ROLL_PITCH_RAD, MAX_ROLL_PITCH_RAD)
        clipped[2] = np.clip(clipped[2], -MAX_YAW_RAD, MAX_YAW_RAD)
        if reference.phase_id in (0, 2):
            clipped[0] = np.clip(clipped[0], -np.deg2rad(36.0), np.deg2rad(36.0))
            clipped[1] = np.clip(clipped[1], -np.deg2rad(36.0), np.deg2rad(36.0))
        if float(obs["pos"][2]) < 0.25:
            clipped[3] = max(clipped[3], self.thrust_min + MIN_COMPLETION_THRUST * self.action_scale[3])
        return np.clip(clipped, self.action_low, self.action_high).astype(np.float32)

    def _finish_hold_action(self, obs: dict[str, Any]) -> np.ndarray:
        yaw = float(obs.get("rpy", np.zeros(3, dtype=np.float32))[2])
        thrust = self.thrust_min + 0.42 * self.action_scale[3]
        action = np.array([0.0, 0.0, yaw, thrust], dtype=np.float32)
        self._last_action_norm = self._normalize_action(action)
        return np.clip(action, self.action_low, self.action_high).astype(np.float32)

    def _diagnostics(
        self, obs: dict[str, Any], reference: PlannerReference, action: np.ndarray
    ) -> dict[str, float]:
        pos = np.asarray(obs["pos"], dtype=np.float32)
        heading = reference.desired_heading
        return {
            "hybrid_phase_id": float(reference.phase_id),
            "hybrid_target_gate": float(reference.target_gate),
            "hybrid_gate_distance_m": float(reference.gate_distance),
            "hybrid_gate_local_x_m": float(reference.gate_local_position[0]),
            "hybrid_gate_local_y_error_m": float(reference.gate_local_position[1] - reference.aperture_offset_yz[0]),
            "hybrid_gate_local_z_error_m": float(reference.gate_local_position[2] - reference.aperture_offset_yz[1]),
            "hybrid_reference_error_m": float(np.linalg.norm(reference.reference_point - pos)),
            "hybrid_desired_speed_mps": float(reference.desired_speed),
            "hybrid_reference_vx_mps": float(reference.reference_velocity[0]),
            "hybrid_reference_vy_mps": float(reference.reference_velocity[1]),
            "hybrid_reference_vz_mps": float(reference.reference_velocity[2]),
            "hybrid_desired_heading_yaw_rad": float(np.arctan2(heading[1], heading[0])),
            "hybrid_action_roll_rad": float(action[0]),
            "hybrid_action_pitch_rad": float(action[1]),
            "hybrid_action_yaw_rad": float(action[2]),
            "hybrid_action_thrust": float(action[3]),
        }

    @staticmethod
    def _safe_normalize(vector: np.ndarray, fallback: Any | None = None) -> np.ndarray:
        vec = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 1e-6:
            return (vec / norm).astype(np.float32)
        if fallback is None:
            fallback_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        else:
            fallback_vec = np.asarray(fallback, dtype=np.float32)
        fallback_norm = float(np.linalg.norm(fallback_vec))
        if fallback_norm <= 1e-6:
            fallback_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            fallback_norm = 1.0
        return (fallback_vec / fallback_norm).astype(np.float32)

    @staticmethod
    def quat_to_rotmat(quat: np.ndarray) -> np.ndarray:
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
