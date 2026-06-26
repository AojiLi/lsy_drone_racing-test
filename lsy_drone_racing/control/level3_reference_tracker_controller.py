"""v54 planner-reference tracker controller for unchanged Level3."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import torch

from lsy_drone_racing.control import Controller
from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_OBS_DIM,
    ReferenceTrackerObservation,
    ReferenceTrajectoryGenerator,
    TrackerMemory,
    TrackerPPOAgent,
    action_bounds_from_config,
    gate_local_axis_velocity_x,
    load_tracker_checkpoint,
    scale_action,
)

MODEL_NAME = (
    "checkpoints/v54_reference_tracker_ppo/"
    "v54_reference_tracker_ppo_final.ckpt"
)


class Level3ReferenceTrackerController(Controller):
    """Use a deterministic upper planner as observation, with PPO as action source."""

    def __init__(self, obs: dict[str, Any], info: dict[str, Any], config: Any) -> None:
        """Initialize planner, tracker memory, action scaling, and PPO checkpoint."""
        super().__init__(obs, info, config)
        if config.env.control_mode != "attitude":
            raise ValueError("Level3ReferenceTrackerController requires attitude control.")

        self.device = torch.device("cpu")
        self.model_path = self._resolve_model_path()
        self.rp_limit_deg = self._checkpoint_rp_limit_deg(default=50.0)
        self.action_low, self.action_high = action_bounds_from_config(
            config,
            rp_limit_deg=self.rp_limit_deg,
        )
        self.action_scale = (self.action_high - self.action_low) / 2.0
        self.action_mean = (self.action_high + self.action_low) / 2.0
        self._action_scale = self.action_scale
        self._action_mean = self.action_mean
        self.action_dim = 4
        self.obs_dim = REFERENCE_TRACKER_OBS_DIM

        self.generator = ReferenceTrajectoryGenerator(task="level3")
        self.observation_builder = ReferenceTrackerObservation()
        self.generator.reset(obs)
        self.memory = TrackerMemory.from_observation(obs)
        self.reference = self.generator.reference(obs)
        self._last_action_norm = np.zeros(self.action_dim, dtype=np.float32)
        self._last_diagnostics: dict[str, float] = {}
        self._step_count = 0
        self._finished = False
        self.checkpoint_loaded = 0.0
        self.agent = self._load_agent()
        self.agent.eval()

    def compute_control(
        self,
        obs: dict[str, Any],
        info: dict[str, Any] | None = None,
    ) -> np.ndarray:
        """Compute the attitude action from planner-reference tracker observation."""
        target_gate = int(np.asarray(obs.get("target_gate", -1)).item())
        if target_gate < 0:
            self._finished = True
            self._last_action_norm = np.zeros(self.action_dim, dtype=np.float32)
            return scale_action(self._last_action_norm, self.action_low, self.action_high)

        self._step_count += 1
        self.reference = self.generator.reference(obs)
        tracker_obs = self.observation_builder.build(obs, self.reference, self.memory)
        obs_tensor = torch.as_tensor(
            tracker_obs, dtype=torch.float32, device=self.device
        ).unsqueeze(0)
        with torch.no_grad():
            action_norm, _logprob, _entropy, _value = self.agent.get_action_and_value(
                obs_tensor,
                deterministic=True,
            )

        action_norm_np = action_norm.squeeze(0).detach().cpu().numpy().astype(np.float32)
        if not np.isfinite(action_norm_np).all():
            action_norm_np = np.zeros(self.action_dim, dtype=np.float32)
        action_norm_np = np.clip(action_norm_np, -1.0, 1.0)
        action = scale_action(action_norm_np, self.action_low, self.action_high)
        self.memory.update(obs, action_norm_np)
        self._last_action_norm = action_norm_np
        self._last_diagnostics = self._diagnostics(obs, tracker_obs, action)
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
        """Signal completion only after the race has actually finished."""
        if int(np.asarray(obs.get("target_gate", -1)).item()) < 0:
            self._finished = True
        return self._finished

    def episode_callback(self) -> None:
        """Reset completion state after an episode."""
        self._finished = False

    def reset_episode_state(self, obs: dict[str, Any] | None = None) -> None:
        """Reset planner-reference state when an external evaluator reuses the controller."""
        if obs is not None:
            self.generator.reset(obs)
            self.memory = TrackerMemory.from_observation(obs)
            self.reference = self.generator.reference(obs)
        self._last_action_norm = np.zeros(self.action_dim, dtype=np.float32)
        self._last_diagnostics = {}
        self._step_count = 0
        self._finished = False

    def mppi_diagnostics(self) -> dict[str, float]:
        """Expose v54 tracker diagnostics through the evaluator's existing hook."""
        return dict(self._last_diagnostics)

    def _resolve_model_path(self) -> Path:
        env_path = os.environ.get("V54_REFERENCE_TRACKER_CHECKPOINT")
        if env_path:
            return Path(env_path).expanduser().resolve()
        return Path(__file__).resolve().parent / MODEL_NAME

    def _checkpoint_rp_limit_deg(self, default: float = 50.0) -> float:
        """Read action roll/pitch envelope from checkpoint metadata when present."""
        if not self.model_path.exists():
            return float(default)
        checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict):
            return float(default)
        value = checkpoint.get("rp_limit_deg", default)
        try:
            rp_limit_deg = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid v54 tracker rp_limit_deg metadata: {value!r}") from exc
        if not np.isfinite(rp_limit_deg) or rp_limit_deg <= 0.0 or rp_limit_deg > 90.0:
            raise ValueError(f"Invalid v54 tracker rp_limit_deg metadata: {rp_limit_deg!r}")
        return rp_limit_deg

    def _load_agent(self) -> TrackerPPOAgent:
        if self.model_path.exists():
            agent, metadata = load_tracker_checkpoint(self.model_path, self.device)
            if int(metadata.get("obs_dim", REFERENCE_TRACKER_OBS_DIM)) != REFERENCE_TRACKER_OBS_DIM:
                raise ValueError(f"Unexpected v54 tracker obs_dim in {self.model_path}.")
            self.checkpoint_loaded = 1.0
            return agent
        if os.environ.get("V54_REFERENCE_TRACKER_ALLOW_UNTRAINED") == "1":
            self.checkpoint_loaded = 0.0
            return TrackerPPOAgent(obs_dim=REFERENCE_TRACKER_OBS_DIM, action_dim=4).to(self.device)
        raise FileNotFoundError(
            f"v54 reference tracker checkpoint not found: {self.model_path}. "
            "Set V54_REFERENCE_TRACKER_CHECKPOINT or train the tracker first."
        )

    def _diagnostics(
        self,
        obs: dict[str, Any],
        tracker_obs: np.ndarray,
        action: np.ndarray,
    ) -> dict[str, float]:
        position_error = float(
            np.linalg.norm(self.reference.current_point - np.asarray(obs["pos"]))
        )
        return {
            "v54_tracker_step": float(self._step_count),
            "v54_tracker_phase_id": float(self.reference.phase_id),
            "v54_tracker_target_gate": float(self.reference.target_gate),
            "v54_tracker_reference_x": float(self.reference.current_point[0]),
            "v54_tracker_reference_y": float(self.reference.current_point[1]),
            "v54_tracker_reference_z": float(self.reference.current_point[2]),
            "v54_tracker_next_reference_x": float(self.reference.next_point[0]),
            "v54_tracker_next_reference_y": float(self.reference.next_point[1]),
            "v54_tracker_next_reference_z": float(self.reference.next_point[2]),
            "v54_tracker_gate_local_x": float(self.reference.gate_local_position[0]),
            "v54_tracker_gate_local_y": float(self.reference.gate_local_position[1]),
            "v54_tracker_gate_local_z": float(self.reference.gate_local_position[2]),
            "v54_tracker_gate_local_vx": float(gate_local_axis_velocity_x(obs)),
            "v54_tracker_aperture_y": float(self.reference.aperture_yz[0]),
            "v54_tracker_aperture_z": float(self.reference.aperture_yz[1]),
            "v54_tracker_position_error_m": position_error,
            "v54_tracker_desired_speed": float(self.reference.desired_speed),
            "v54_tracker_obstacle_distance_m": float(self.reference.obstacle_distance),
            "v54_tracker_checkpoint_loaded": float(self.checkpoint_loaded),
            "v54_tracker_rp_limit_deg": float(self.rp_limit_deg),
            "v54_tracker_obs_abs_max": float(np.max(np.abs(tracker_obs))),
            "v54_tracker_action_norm_l2": float(np.linalg.norm(self._last_action_norm)),
            "v54_tracker_roll_cmd": float(action[0]),
            "v54_tracker_pitch_cmd": float(action[1]),
            "v54_tracker_yaw_cmd": float(action[2]),
            "v54_tracker_thrust_cmd": float(action[3]),
        }
