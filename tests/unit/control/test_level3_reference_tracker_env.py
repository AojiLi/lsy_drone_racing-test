from pathlib import Path

import numpy as np
import pytest

from lsy_drone_racing.control.level3_reference_tracker import (
    GeometricSlowGatePlanner,
    REFERENCE_TRACKER_OBS_DIM,
    ReferenceFrame,
    ReferenceTrackerReward,
    ReferenceTrackerVectorEnv,
    ReferenceTrajectoryGenerator,
    gate_local_axis_velocity_x,
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


def test_level3_geometric_planner_advances_conservatively() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-1.35, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    cruise = generator.reference(obs)
    assert cruise.phase == "cruise"
    assert cruise.desired_speed == pytest.approx(0.82)
    np.testing.assert_allclose(
        cruise.current_point,
        np.array([-1.05, 0.0, 0.75], dtype=np.float32),
        atol=1e-6,
    )

    obs["pos"] = np.array([-1.00, 0.0, 0.75], dtype=np.float32)
    slowdown = generator.reference(obs)
    assert slowdown.phase == "slowdown"
    assert slowdown.desired_speed < cruise.desired_speed

    obs["pos"] = np.array([-0.50, 0.0, 0.75], dtype=np.float32)
    align = generator.reference(obs)
    assert align.phase == "align"
    assert align.desired_speed < slowdown.desired_speed

    obs["pos"] = np.array([-0.24, 0.0, 0.75], dtype=np.float32)
    cross = generator.reference(obs)
    assert cross.phase == "cross"
    assert cross.current_point[0] > 0.0

    obs["pos"] = np.array([0.34, 0.0, 0.75], dtype=np.float32)
    still_cross = generator.reference(obs)
    assert still_cross.phase == "cross"


def test_level3_geometric_planner_requires_alignment_before_crossing() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-0.50, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    assert generator.reference(obs).phase == "align"

    obs["pos"] = np.array([-0.16, 0.32, 0.75], dtype=np.float32)
    obs["vel"] = np.array([0.1, 0.0, 0.0], dtype=np.float32)
    still_align = generator.reference(obs)
    assert still_align.phase == "align"

    obs["pos"] = np.array([-0.16, 0.05, 0.75], dtype=np.float32)
    obs["vel"] = np.array([1.2, 0.0, 0.0], dtype=np.float32)
    too_fast = generator.reference(obs)
    assert too_fast.phase == "align"

    obs["vel"] = np.array([0.1, 0.0, 0.0], dtype=np.float32)
    cross = generator.reference(obs)
    assert cross.phase == "cross"


def test_gate_axis_speed_uses_gate_local_x_velocity() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["gates_quat"] = np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32)

    obs["vel"] = np.array([0.0, 3.0, 0.0], dtype=np.float32)
    assert gate_local_axis_velocity_x(obs) == pytest.approx(0.0)
    assert GeometricSlowGatePlanner._gate_axis_speed(obs) == pytest.approx(0.0)

    obs["vel"] = np.array([-0.7, 3.0, 0.0], dtype=np.float32)
    assert gate_local_axis_velocity_x(obs) == pytest.approx(-0.7)
    assert GeometricSlowGatePlanner._gate_axis_speed(obs) == pytest.approx(0.7)


def test_level3_geometric_planner_uses_hysteresis_and_gate_reset() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array(
        [[0.0, 0.0, 0.75], [2.0, 0.0, 0.75]],
        dtype=np.float32,
    )
    obs["gates_quat"] = np.array(
        [[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]],
        dtype=np.float32,
    )
    obs["gates_visited"] = np.array([False, False])
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-0.20, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    cross = generator.reference(obs)
    assert cross.phase == "cross"

    obs["pos"] = np.array([-0.45, 0.0, 0.75], dtype=np.float32)
    still_cross = generator.reference(obs)
    assert still_cross.phase == "cross"

    obs["target_gate"] = np.array(1, dtype=np.int32)
    obs["pos"] = np.array([0.55, 0.0, 0.75], dtype=np.float32)
    reset_to_next_gate = generator.reference(obs)
    assert reset_to_next_gate.phase == "cruise"
    assert reset_to_next_gate.target_gate == 1


def test_level3_geometric_planner_forbids_same_target_recover() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-0.20, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    assert generator.reference(obs).phase == "cross"

    obs["pos"] = np.array([0.70, 0.0, 0.75], dtype=np.float32)
    same_target_after_plane = generator.reference(obs)
    assert same_target_after_plane.target_gate == 0
    assert same_target_after_plane.phase == "cross"


def test_level3_geometric_planner_backs_out_when_near_plane_misaligned() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-0.20, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    assert generator.reference(obs).phase == "cross"

    obs["pos"] = np.array([-0.10, 0.34, 0.75], dtype=np.float32)
    backout = generator.reference(obs)
    assert backout.phase == "align"

    obs["pos"] = np.array([-0.10, 0.05, 0.75], dtype=np.float32)
    realigned = generator.reference(obs)
    assert realigned.phase == "cross"


def test_level3_geometric_planner_offsets_visible_obstacle_on_segment() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["pos"] = np.array([-1.35, 0.0, 0.75], dtype=np.float32)
    obs["obstacles_pos"] = np.array([[-0.90, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([True])
    generator = ReferenceTrajectoryGenerator("level3")
    generator.reset(obs)

    reference = generator.reference(obs)

    assert reference.phase == "cruise"
    assert abs(float(reference.current_point[1])) > 0.05
    assert abs(float(reference.current_point[1])) <= 0.24


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
