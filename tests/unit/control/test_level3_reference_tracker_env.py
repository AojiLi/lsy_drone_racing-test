from pathlib import Path

import numpy as np
import pytest

from lsy_drone_racing.control.level3_reference_tracker import (
    REFERENCE_TRACKER_OBS_DIM,
    ReferenceFrame,
    ReferenceTrackerReward,
    ReferenceTrackerVectorEnv,
    ReferenceTrajectoryGenerator,
    normalize_tracker_task,
    tracker_env_mode_from_config,
)
from lsy_drone_racing.utils import load_config

ROOT = Path(__file__).parents[3]


def sample_obs() -> dict[str, np.ndarray]:
    return {
        "pos": np.array([0.0, 0.0, 0.01], dtype=np.float32),
        "quat": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "vel": np.zeros(3, dtype=np.float32),
        "ang_vel": np.zeros(3, dtype=np.float32),
        "target_gate": np.array(0, dtype=np.int32),
        "gates_pos": np.array([[8.0, 8.0, 0.7]], dtype=np.float32),
        "gates_quat": np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32),
        "gates_visited": np.array([False]),
        "obstacles_pos": np.array([[8.0, -8.0, 1.55]], dtype=np.float32),
        "obstacles_visited": np.array([False]),
    }


def test_legacy_task_aliases() -> None:
    assert normalize_tracker_task("point") == "point_reach"
    assert normalize_tracker_task("gate_aperture") == "gate_aperture_reference"


def test_free_space_reference_ignores_dummy_gate_and_obstacle() -> None:
    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("line_tracking")
    generator.reset(obs)
    reference = generator.reference(obs)

    assert reference.target_gate == 0
    np.testing.assert_allclose(reference.gate_local_position, np.zeros(3), atol=1e-6)
    np.testing.assert_allclose(reference.aperture_yz, np.zeros(2), atol=1e-6)
    np.testing.assert_allclose(reference.obstacle_relative, np.zeros(3), atol=1e-6)
    assert reference.obstacle_detected == 0.0
    assert reference.obstacle_distance == pytest.approx(10.0)
    assert reference.desired_speed > 0.0


def test_polyline_reference_terminal_hold_zeroes_desired_speed() -> None:
    obs = sample_obs()
    obs["pos"] = np.array([0.9, 0.0, 0.65], dtype=np.float32)
    generator = ReferenceTrajectoryGenerator("line_tracking")
    generator.reset(obs)

    reference = None
    steps_past_line_end = int(np.ceil(0.9 / (0.38 * generator.dt))) + 3
    for _ in range(steps_past_line_end):
        reference = generator.reference(obs)

    assert reference is not None
    assert reference.phase == "terminal_hold"
    assert reference.desired_speed == pytest.approx(0.0)
    np.testing.assert_allclose(reference.desired_velocity, np.zeros(3), atol=1e-6)
    np.testing.assert_allclose(
        reference.current_point,
        np.array([0.9, 0.0, 0.65], dtype=np.float32),
        atol=1e-6,
    )


def test_hover_reference_guides_toward_airborne_anchor_until_near() -> None:
    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("hover")
    generator.reset(obs)

    reference = generator.reference(obs)
    assert reference.current_point[2] == pytest.approx(0.65)
    assert reference.desired_speed > 0.0
    assert reference.desired_velocity[2] > 0.0
    assert reference.phase in {"cruise", "slowdown"}

    obs["pos"] = reference.current_point.copy()
    near_reference = generator.reference(obs)
    assert near_reference.desired_speed == pytest.approx(0.0)
    np.testing.assert_allclose(near_reference.desired_velocity, np.zeros(3), atol=1e-6)
    assert near_reference.phase == "hover"


def test_gate_aperture_reference_uses_gate_aperture_phase() -> None:
    obs = sample_obs()
    obs["pos"] = np.array([0.0, 0.0, 0.75], dtype=np.float32)
    obs["gates_pos"] = np.array([[0.5, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("gate_aperture_reference")
    generator.reset(obs)
    reference = generator.reference(obs)

    assert reference.phase == "align"
    assert reference.phase_id == 3


def test_tracker_training_configs_resolve_modes() -> None:
    free_config = load_config(ROOT / "config/level3_tracker_free_space.toml")
    gate_config = load_config(ROOT / "config/level3_tracker_gate_aperture.toml")

    assert tracker_env_mode_from_config(free_config, "line_tracking") == "free_space"
    np.testing.assert_allclose(
        np.asarray(free_config.env.track.drones[0]["pos"], dtype=np.float32),
        np.array([0.0, 0.0, 0.65], dtype=np.float32),
        atol=1e-6,
    )
    assert (
        tracker_env_mode_from_config(gate_config, "gate_aperture_reference")
        == "gate_aperture"
    )
    np.testing.assert_allclose(
        np.asarray(gate_config.env.track.drones[0]["pos"], dtype=np.float32),
        np.array([0.55, 0.0, 0.75], dtype=np.float32),
        atol=1e-6,
    )
    np.testing.assert_allclose(
        np.asarray(gate_config.env.randomizations.drone_pos.kwargs["minval"], dtype=np.float32),
        np.array([-0.18, -0.08, -0.04], dtype=np.float32),
        atol=1e-6,
    )
    np.testing.assert_allclose(
        np.asarray(gate_config.env.randomizations.drone_pos.kwargs["maxval"], dtype=np.float32),
        np.array([0.18, 0.08, 0.04], dtype=np.float32),
        atol=1e-6,
    )


def test_tracker_training_config_rejects_wrong_task_family() -> None:
    gate_config = load_config(ROOT / "config/level3_tracker_gate_aperture.toml")

    with pytest.raises(ValueError, match="not valid for gate_aperture"):
        tracker_env_mode_from_config(gate_config, "line_tracking")


def test_reference_tracker_vector_env_reset_step_shapes() -> None:
    env = ReferenceTrackerVectorEnv(
        config_name="level3_tracker_free_space.toml",
        task="hover",
        tracker_env_mode="free_space",
        num_envs=2,
        max_episode_steps=8,
        seed=123,
        jax_device="cpu",
    )
    try:
        obs, _info = env.reset(seed=123)
        assert obs.shape == (2, REFERENCE_TRACKER_OBS_DIM)
        assert np.isfinite(obs).all()

        next_obs, reward, terminated, truncated, _info = env.step(
            np.zeros((2, 4), dtype=np.float32)
        )

        assert next_obs.shape == (2, REFERENCE_TRACKER_OBS_DIM)
        assert reward.shape == (2,)
        assert terminated.shape == (2,)
        assert truncated.shape == (2,)
        assert np.isfinite(next_obs).all()
        assert np.isfinite(reward).all()
        assert "tracker/reward" in env.last_diagnostics
    finally:
        env.close()


def test_gate_completion_reward_adds_cross_and_recovery_events() -> None:
    prev_obs = sample_obs()
    obs = sample_obs()
    prev_obs["gates_pos"] = np.array([[0.85, 0.0, 0.75]], dtype=np.float32)
    obs["gates_pos"] = prev_obs["gates_pos"].copy()
    prev_obs["pos"] = np.array([0.84, 0.0, 0.75], dtype=np.float32)
    obs["pos"] = np.array([1.21, 0.0, 0.75], dtype=np.float32)
    obs["vel"] = np.array([0.2, 0.0, 0.0], dtype=np.float32)
    reference = ReferenceFrame(
        phase="cross",
        phase_id=4,
        target_gate=0,
        current_point=np.array([1.2, 0.0, 0.75], dtype=np.float32),
        next_point=np.array([1.3, 0.0, 0.75], dtype=np.float32),
        lookahead_point=np.array([1.4, 0.0, 0.75], dtype=np.float32),
        desired_velocity=np.zeros(3, dtype=np.float32),
        desired_heading=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_speed=0.0,
        gate_local_position=np.array([-0.01, 0.0, 0.0], dtype=np.float32),
        aperture_yz=np.zeros(2, dtype=np.float32),
        obstacle_relative=np.zeros(3, dtype=np.float32),
        obstacle_distance=10.0,
        obstacle_detected=0.0,
    )
    reward_model = ReferenceTrackerReward(
        pos_error_coef=0.0,
        vel_error_coef=0.0,
        heading_coef=0.0,
        gate_center_coef=0.0,
        obstacle_coef=0.0,
        action_coef=0.0,
        action_delta_coef=0.0,
        progress_bonus=0.0,
        gate_x_progress_coef=1.0,
        gate_cross_bonus=5.0,
        gate_recover_bonus=7.0,
        gate_linger_penalty_coef=0.0,
    )

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/valid_aperture_cross_event"] == pytest.approx(1.0)
    assert diagnostics["tracker/post_gate_recovery_event"] == pytest.approx(1.0)
    assert diagnostics["tracker/gate_x_progress"] == pytest.approx(0.37, abs=1e-6)
    assert reward > 12.0


def test_gate_completion_reward_penalizes_near_plane_linger() -> None:
    prev_obs = sample_obs()
    obs = sample_obs()
    prev_obs["gates_pos"] = np.array([[0.85, 0.0, 0.75]], dtype=np.float32)
    obs["gates_pos"] = prev_obs["gates_pos"].copy()
    prev_obs["pos"] = np.array([0.56, 0.0, 0.75], dtype=np.float32)
    obs["pos"] = np.array([0.59, 0.0, 0.75], dtype=np.float32)
    reference = ReferenceFrame(
        phase="align",
        phase_id=3,
        target_gate=0,
        current_point=np.array([0.63, 0.0, 0.75], dtype=np.float32),
        next_point=np.array([0.7, 0.0, 0.75], dtype=np.float32),
        lookahead_point=np.array([0.8, 0.0, 0.75], dtype=np.float32),
        desired_velocity=np.zeros(3, dtype=np.float32),
        desired_heading=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_speed=0.0,
        gate_local_position=np.array([-0.29, 0.0, 0.0], dtype=np.float32),
        aperture_yz=np.zeros(2, dtype=np.float32),
        obstacle_relative=np.zeros(3, dtype=np.float32),
        obstacle_distance=10.0,
        obstacle_detected=0.0,
    )
    reward_model = ReferenceTrackerReward(
        pos_error_coef=0.0,
        vel_error_coef=0.0,
        heading_coef=0.0,
        gate_center_coef=0.0,
        obstacle_coef=0.0,
        action_coef=0.0,
        action_delta_coef=0.0,
        progress_bonus=0.0,
        gate_x_progress_coef=0.0,
        gate_cross_bonus=0.0,
        gate_recover_bonus=0.0,
        gate_linger_penalty_coef=2.0,
    )

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/near_plane_linger_event"] == pytest.approx(1.0)
    assert reward == pytest.approx(-2.0)
