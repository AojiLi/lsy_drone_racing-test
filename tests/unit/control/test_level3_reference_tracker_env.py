from argparse import Namespace
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from lsy_drone_racing.control.level3_reference_tracker import (
    COMMAND_REFERENCE_TRACKER_LAYOUT,
    REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,
    REFERENCE_TRACKER_LAYOUT,
    REFERENCE_TRACKER_OBS_DIM,
    SEMANTIC_REFERENCE_TRACKER_LAYOUT,
    SEMANTIC_REFERENCE_TRACKER_OBS_DIM,
    GeometricSlowGatePlanner,
    ReferenceCommandReward,
    ReferenceFrame,
    ReferenceTrackerObservation,
    ReferenceTrackerReward,
    ReferenceTrackerVectorEnv,
    ReferenceTrajectoryGenerator,
    TrackerMemory,
    TrackerPPOAgent,
    default_tracker_observation_layout,
    gate_local_axis_velocity_x,
    load_tracker_checkpoint,
    normalize_tracker_task,
    save_tracker_checkpoint,
    tracker_env_mode_from_config,
    tracker_reward_model_for_task,
    waypoint_semantic_features,
)
from lsy_drone_racing.control.train_level3_reference_tracker_ppo import (
    reward_coefficients_from_args,
    reward_model_name_from_task,
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
    assert normalize_tracker_task("semantic_reference") == "reference_command_no_gate_reward"
    assert (
        normalize_tracker_task("semantic_planner_reference") == "reference_command_no_gate_reward"
    )


def test_semantic_observation_layout_extends_v1_without_changing_v1() -> None:
    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator.reset(obs)
    reference = generator.reference(obs)
    memory = TrackerMemory.from_observation(obs)

    v1_obs = ReferenceTrackerObservation(REFERENCE_TRACKER_LAYOUT).build(obs, reference, memory)
    v2_obs = ReferenceTrackerObservation(SEMANTIC_REFERENCE_TRACKER_LAYOUT).build(
        obs, reference, memory
    )

    assert v1_obs.shape == (REFERENCE_TRACKER_OBS_DIM,)
    assert v2_obs.shape == (SEMANTIC_REFERENCE_TRACKER_OBS_DIM,)
    np.testing.assert_allclose(v2_obs[:REFERENCE_TRACKER_OBS_DIM], v1_obs, atol=1e-6)
    np.testing.assert_allclose(
        v2_obs[REFERENCE_TRACKER_OBS_DIM:], waypoint_semantic_features(reference), atol=1e-6
    )
    assert reference.waypoint_type == "pass_through"


def test_reference_command_layout_is_clean_tracker_baseline() -> None:
    assert (
        default_tracker_observation_layout("reference_command_no_gate_reward")
        == COMMAND_REFERENCE_TRACKER_LAYOUT
    )

    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator.reset(obs)
    reference = generator.reference(obs)
    memory = TrackerMemory.from_observation(obs)

    command_obs = ReferenceTrackerObservation(COMMAND_REFERENCE_TRACKER_LAYOUT).build(
        obs, reference, memory
    )
    modified_context = replace(
        reference,
        phase_id=5,
        gate_local_position=np.array([9.0, -8.0, 7.0], dtype=np.float32),
        aperture_yz=np.array([0.4, -0.3], dtype=np.float32),
        obstacle_relative=np.array([0.9, -0.8, 0.7], dtype=np.float32),
        obstacle_distance=0.05,
        obstacle_detected=1.0,
    )
    command_obs_with_context_noise = ReferenceTrackerObservation(
        COMMAND_REFERENCE_TRACKER_LAYOUT
    ).build(obs, modified_context, memory)
    v1_obs = ReferenceTrackerObservation(REFERENCE_TRACKER_LAYOUT).build(obs, reference, memory)
    v1_obs_with_context_noise = ReferenceTrackerObservation(REFERENCE_TRACKER_LAYOUT).build(
        obs, modified_context, memory
    )

    assert command_obs.shape == (REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM,)
    np.testing.assert_allclose(command_obs, command_obs_with_context_noise, atol=1e-6)
    assert not np.allclose(v1_obs, v1_obs_with_context_noise)


def test_reference_command_task_emits_explicit_no_gate_intents() -> None:
    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator.reset(obs, seed=11)

    references = [generator.reference(obs) for _ in range(220)]
    types = {reference.waypoint_type for reference in references}

    assert {"pass_through", "hold_or_brake", "low_speed_through", "recover_speed"} <= types
    brake = next(
        reference for reference in references if reference.waypoint_type == "hold_or_brake"
    )
    slow = next(
        reference for reference in references if reference.waypoint_type == "low_speed_through"
    )
    assert brake.stop_signal == pytest.approx(1.0)
    assert brake.brake_mask == pytest.approx(1.0)
    assert brake.desired_speed <= 0.10
    np.testing.assert_allclose(brake.desired_velocity, np.zeros(3), atol=1e-6)
    assert np.linalg.norm(brake.next_point - brake.current_point) <= 0.02
    assert np.linalg.norm(brake.lookahead_point - brake.current_point) <= 0.03
    assert slow.slow_through_mask == pytest.approx(1.0)
    assert 0.25 <= slow.desired_speed <= 0.35


def test_semantic_reference_intent_is_encoded_by_horizon_speed_and_heading() -> None:
    obs = sample_obs()
    generator = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator.reset(obs, seed=12)

    references = [generator.reference(obs) for _ in range(220)]
    through = next(
        reference for reference in references if reference.waypoint_type == "pass_through"
    )
    brake = next(
        reference for reference in references if reference.waypoint_type == "hold_or_brake"
    )
    slow = next(
        reference for reference in references if reference.waypoint_type == "low_speed_through"
    )
    recover = next(
        reference for reference in references if reference.waypoint_type == "recover_speed"
    )

    assert through.waypoint_type == "pass_through"
    assert 0.55 <= through.desired_speed <= 0.78
    assert np.linalg.norm(through.next_point - through.current_point) <= (
        through.desired_speed * generator.dt * 4.0 + 0.02
    )
    through_horizon = through.lookahead_point - through.current_point
    assert np.dot(safe_normalize_for_test(through_horizon), through.desired_velocity) > 0.0

    assert brake.waypoint_type == "hold_or_brake"
    assert np.linalg.norm(brake.next_point - brake.current_point) <= 0.02
    assert np.linalg.norm(brake.lookahead_point - brake.current_point) <= 0.03
    assert 0.02 <= brake.desired_speed <= 0.07
    np.testing.assert_allclose(brake.desired_velocity, np.zeros(3), atol=1e-6)

    assert slow.waypoint_type == "low_speed_through"
    assert np.linalg.norm(slow.lookahead_point - slow.current_point) <= (
        slow.desired_speed * generator.dt * 10.0 + 0.03
    )
    assert 0.25 <= slow.desired_speed <= 0.35
    slow_horizon = slow.lookahead_point - slow.current_point
    np.testing.assert_allclose(
        slow.desired_velocity, safe_normalize_for_test(slow_horizon) * slow.desired_speed, atol=1e-5
    )

    assert recover.waypoint_type == "recover_speed"
    assert np.linalg.norm(recover.lookahead_point - recover.current_point) <= (
        recover.desired_speed * generator.dt * 10.0 + 0.03
    )
    assert 0.25 <= recover.desired_speed <= 0.62
    recover_horizon = recover.lookahead_point - recover.current_point
    np.testing.assert_allclose(
        recover.desired_velocity,
        safe_normalize_for_test(recover_horizon) * recover.desired_speed,
        atol=1e-5,
    )


def safe_normalize_for_test(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-6:
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)
    return (np.asarray(vector, dtype=np.float32) / norm).astype(np.float32)


def test_reference_command_generator_is_dense_continuous_and_randomized() -> None:
    obs = sample_obs()
    generator_a = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator_a.reset(obs, seed=21)
    refs_a = [generator_a.reference(obs) for _ in range(220)]

    current_jumps = np.array(
        [
            np.linalg.norm(next_ref.current_point - reference.current_point)
            for reference, next_ref in zip(refs_a[:-1], refs_a[1:], strict=True)
        ],
        dtype=np.float32,
    )
    assert float(np.max(current_jumps)) <= 0.06

    for reference in refs_a:
        if reference.waypoint_type == "hold_or_brake":
            continue
        assert np.linalg.norm(reference.next_point - reference.current_point) <= (
            reference.desired_speed * generator_a.dt * 4.0 + 0.025
        )
        assert np.linalg.norm(reference.lookahead_point - reference.current_point) <= (
            reference.desired_speed * generator_a.dt * 10.0 + 0.045
        )

    generator_b = ReferenceTrajectoryGenerator("reference_command_no_gate_reward")
    generator_b.reset(obs, seed=22)
    ref_a = refs_a[0]
    ref_b = generator_b.reference(obs)
    assert not np.allclose(ref_a.lookahead_point, ref_b.lookahead_point)


def test_no_gate_command_tracker_forces_gate_reward_coefficients_to_zero() -> None:
    args = Namespace(
        task="reference_command_no_gate_reward",
        pos_error_coef=3.0,
        vel_error_coef=0.6,
        heading_coef=0.35,
        gate_center_coef=9.0,
        obstacle_margin=0.28,
        obstacle_coef=0.8,
        action_coef=0.02,
        action_delta_coef=0.04,
        progress_bonus=0.3,
        trajectory_cross_track_coef=1.2,
        trajectory_along_speed_coef=0.7,
        trajectory_reverse_speed_coef=0.5,
        trajectory_overshoot_coef=1.4,
        gate_x_progress_coef=9.0,
        gate_cross_bonus=9.0,
        gate_recover_bonus=9.0,
        gate_linger_penalty_coef=9.0,
        semantic_brake_speed_coef=0.2,
        semantic_slow_speed_coef=0.3,
        semantic_slow_stop_coef=0.4,
        semantic_recover_speed_coef=0.5,
        crash_penalty=250.0,
    )

    coefficients = reward_coefficients_from_args(args)

    assert coefficients["gate_center_coef"] == pytest.approx(0.0)
    assert coefficients["obstacle_coef"] == pytest.approx(0.0)
    assert coefficients["gate_x_progress_coef"] == pytest.approx(0.0)
    assert coefficients["gate_cross_bonus"] == pytest.approx(0.0)
    assert coefficients["gate_recover_bonus"] == pytest.approx(0.0)
    assert coefficients["gate_linger_penalty_coef"] == pytest.approx(0.0)
    assert coefficients["pos_error_coef"] == pytest.approx(3.0)
    assert coefficients["semantic_brake_speed_coef"] == pytest.approx(0.2)
    assert coefficients["semantic_recover_speed_coef"] == pytest.approx(0.5)


def test_v60_default_reward_has_command_speed_shaping_without_gate_reward() -> None:
    args = Namespace(
        task="reference_command_no_gate_reward",
        pos_error_coef=3.0,
        vel_error_coef=0.6,
        heading_coef=0.35,
        gate_center_coef=9.0,
        obstacle_margin=0.28,
        obstacle_coef=0.8,
        action_coef=0.02,
        action_delta_coef=0.04,
        progress_bonus=0.3,
        trajectory_cross_track_coef=1.2,
        trajectory_along_speed_coef=0.7,
        trajectory_reverse_speed_coef=0.5,
        trajectory_overshoot_coef=1.4,
        gate_x_progress_coef=9.0,
        gate_cross_bonus=9.0,
        gate_recover_bonus=9.0,
        gate_linger_penalty_coef=9.0,
        semantic_brake_speed_coef=1.0,
        semantic_slow_speed_coef=0.8,
        semantic_slow_stop_coef=0.8,
        semantic_recover_speed_coef=0.4,
        crash_penalty=250.0,
    )

    coefficients = reward_coefficients_from_args(args)

    assert coefficients["gate_center_coef"] == pytest.approx(0.0)
    assert coefficients["obstacle_coef"] == pytest.approx(0.0)
    assert coefficients["gate_x_progress_coef"] == pytest.approx(0.0)
    assert coefficients["gate_cross_bonus"] == pytest.approx(0.0)
    assert coefficients["gate_recover_bonus"] == pytest.approx(0.0)
    assert coefficients["gate_linger_penalty_coef"] == pytest.approx(0.0)
    assert coefficients["semantic_brake_speed_coef"] > 0.0
    assert coefficients["semantic_slow_speed_coef"] > 0.0
    assert coefficients["semantic_slow_stop_coef"] > 0.0
    assert coefficients["semantic_recover_speed_coef"] > 0.0
    assert coefficients["trajectory_cross_track_coef"] > 0.0
    assert coefficients["trajectory_along_speed_coef"] > 0.0
    assert coefficients["trajectory_reverse_speed_coef"] > 0.0
    assert coefficients["trajectory_overshoot_coef"] > 0.0


def test_v60_uses_clean_reference_command_reward_model() -> None:
    reward_model = tracker_reward_model_for_task(
        "reference_command_no_gate_reward",
        {"gate_center_coef": 9.0, "obstacle_coef": 9.0, "semantic_brake_speed_coef": 1.0},
    )

    assert isinstance(reward_model, ReferenceCommandReward)
    assert not isinstance(reward_model, ReferenceTrackerReward)
    assert (
        reward_model_name_from_task("reference_command_no_gate_reward")
        == "reference_command_reward"
    )
    assert reward_model_name_from_task("gate_aperture_reference") == (
        "legacy_reference_tracker_reward"
    )


def test_command_speed_reward_penalizes_wrong_motion_without_gate_terms() -> None:
    prev_obs = sample_obs()
    obs = sample_obs()
    reward_model = ReferenceCommandReward(
        pos_error_coef=0.0,
        vel_error_coef=0.0,
        heading_coef=0.0,
        action_coef=0.0,
        action_delta_coef=0.0,
        progress_bonus=0.0,
        trajectory_cross_track_coef=0.0,
        trajectory_along_speed_coef=0.0,
        trajectory_reverse_speed_coef=0.0,
        trajectory_overshoot_coef=0.0,
        semantic_brake_speed_coef=1.0,
        semantic_slow_speed_coef=0.8,
        semantic_slow_stop_coef=0.8,
        semantic_recover_speed_coef=0.4,
        crash_penalty=0.0,
    )

    brake_reference = ReferenceFrame(
        phase="slowdown",
        phase_id=2,
        target_gate=0,
        current_point=np.zeros(3, dtype=np.float32),
        next_point=np.zeros(3, dtype=np.float32),
        lookahead_point=np.array([0.1, 0.0, 0.0], dtype=np.float32),
        desired_velocity=np.zeros(3, dtype=np.float32),
        desired_heading=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_speed=0.05,
        gate_local_position=np.zeros(3, dtype=np.float32),
        aperture_yz=np.zeros(2, dtype=np.float32),
        obstacle_relative=np.zeros(3, dtype=np.float32),
        obstacle_distance=10.0,
        obstacle_detected=0.0,
        waypoint_type="hold_or_brake",
        waypoint_type_id=1,
        stop_signal=1.0,
        brake_mask=1.0,
        slow_through_mask=0.0,
    )
    obs["vel"] = np.array([0.32, 0.0, 0.0], dtype=np.float32)

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        brake_reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/brake_hold_speed_excess"] == pytest.approx(0.20)
    assert not any("gate" in key for key in diagnostics)
    assert not any("obstacle" in key for key in diagnostics)
    assert reward == pytest.approx(-0.20)

    slow_reference = replace(
        brake_reference,
        phase="cross",
        phase_id=4,
        desired_speed=0.30,
        waypoint_type="low_speed_through",
        waypoint_type_id=2,
        stop_signal=0.0,
        brake_mask=0.0,
        slow_through_mask=1.0,
    )
    obs["vel"] = np.zeros(3, dtype=np.float32)

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        slow_reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/slow_through_speed_error"] == pytest.approx(0.30)
    assert diagnostics["tracker/slow_through_stop_error"] == pytest.approx(0.12)
    assert reward == pytest.approx(-0.336)

    recover_reference = replace(
        brake_reference,
        phase="recover",
        phase_id=5,
        desired_speed=0.48,
        waypoint_type="recover_speed",
        waypoint_type_id=3,
        stop_signal=0.0,
        brake_mask=0.0,
        slow_through_mask=0.0,
    )

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        recover_reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/recover_speed_error"] == pytest.approx(0.48)
    assert reward == pytest.approx(-0.192)


def test_command_trajectory_reward_uses_horizon_not_only_current_point() -> None:
    prev_obs = sample_obs()
    obs = sample_obs()
    reward_model = ReferenceCommandReward(
        pos_error_coef=1.0,
        vel_error_coef=1.0,
        heading_coef=0.0,
        action_coef=0.0,
        action_delta_coef=0.0,
        progress_bonus=1.0,
        trajectory_cross_track_coef=1.0,
        trajectory_along_speed_coef=1.0,
        trajectory_reverse_speed_coef=1.0,
        trajectory_overshoot_coef=1.0,
        semantic_brake_speed_coef=0.0,
        semantic_slow_speed_coef=0.0,
        semantic_slow_stop_coef=0.0,
        semantic_recover_speed_coef=0.0,
        crash_penalty=0.0,
    )
    reference = ReferenceFrame(
        phase="cruise",
        phase_id=1,
        target_gate=0,
        current_point=np.zeros(3, dtype=np.float32),
        next_point=np.array([0.8, 0.0, 0.0], dtype=np.float32),
        lookahead_point=np.array([1.2, 0.0, 0.0], dtype=np.float32),
        desired_velocity=np.array([0.30, 0.0, 0.0], dtype=np.float32),
        desired_heading=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_speed=0.30,
        gate_local_position=np.zeros(3, dtype=np.float32),
        aperture_yz=np.zeros(2, dtype=np.float32),
        obstacle_relative=np.zeros(3, dtype=np.float32),
        obstacle_distance=10.0,
        obstacle_detected=0.0,
        waypoint_type="pass_through",
        waypoint_type_id=0,
        stop_signal=0.0,
        brake_mask=0.0,
        slow_through_mask=0.0,
    )
    prev_obs["pos"] = np.array([-0.10, 0.0, 0.0], dtype=np.float32)
    obs["pos"] = np.array([0.40, 0.0, 0.0], dtype=np.float32)
    obs["vel"] = np.array([0.30, 0.0, 0.0], dtype=np.float32)

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/pos_error"] == pytest.approx(0.40)
    assert diagnostics["tracker/command_position_error"] == pytest.approx(0.14)
    assert diagnostics["tracker/trajectory_cross_track_error"] == pytest.approx(0.0)
    assert diagnostics["tracker/moving_along_speed_error"] == pytest.approx(0.0, abs=1e-6)
    assert diagnostics["tracker/command_progress"] == pytest.approx(0.50)
    assert reward == pytest.approx(0.36)


def test_command_trajectory_reward_penalizes_brake_overshoot() -> None:
    prev_obs = sample_obs()
    obs = sample_obs()
    reward_model = ReferenceCommandReward(
        pos_error_coef=1.0,
        vel_error_coef=0.0,
        heading_coef=0.0,
        action_coef=0.0,
        action_delta_coef=0.0,
        progress_bonus=0.0,
        trajectory_cross_track_coef=1.0,
        trajectory_along_speed_coef=1.0,
        trajectory_reverse_speed_coef=1.0,
        trajectory_overshoot_coef=1.0,
        semantic_brake_speed_coef=0.0,
        semantic_slow_speed_coef=0.0,
        semantic_slow_stop_coef=0.0,
        semantic_recover_speed_coef=0.0,
        crash_penalty=0.0,
    )
    reference = ReferenceFrame(
        phase="slowdown",
        phase_id=2,
        target_gate=0,
        current_point=np.zeros(3, dtype=np.float32),
        next_point=np.zeros(3, dtype=np.float32),
        lookahead_point=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_velocity=np.zeros(3, dtype=np.float32),
        desired_heading=np.array([1.0, 0.0, 0.0], dtype=np.float32),
        desired_speed=0.05,
        gate_local_position=np.zeros(3, dtype=np.float32),
        aperture_yz=np.zeros(2, dtype=np.float32),
        obstacle_relative=np.zeros(3, dtype=np.float32),
        obstacle_distance=10.0,
        obstacle_detected=0.0,
        waypoint_type="hold_or_brake",
        waypoint_type_id=1,
        stop_signal=1.0,
        brake_mask=1.0,
        slow_through_mask=0.0,
    )
    obs["pos"] = np.array([0.20, 0.0, 0.0], dtype=np.float32)

    reward, diagnostics = reward_model.compute(
        prev_obs,
        obs,
        reference,
        np.zeros(4, dtype=np.float32),
        np.zeros(4, dtype=np.float32),
        terminated=False,
        truncated=False,
    )

    assert diagnostics["tracker/brake_hold_overshoot"] == pytest.approx(0.20)
    assert diagnostics["tracker/command_position_error"] == pytest.approx(0.20)
    assert diagnostics["tracker/command_cross_track_error"] == pytest.approx(0.0)
    assert reward == pytest.approx(-0.40)


def test_tracker_checkpoint_layout_versioning_preserves_v1_default(tmp_path: Path) -> None:
    v1_path = tmp_path / "tracker_v1.ckpt"
    v2_path = tmp_path / "tracker_v2.ckpt"
    v3_path = tmp_path / "tracker_v3.ckpt"
    save_tracker_checkpoint(
        v1_path,
        TrackerPPOAgent(obs_dim=REFERENCE_TRACKER_OBS_DIM),
        observation_layout=REFERENCE_TRACKER_LAYOUT,
    )
    save_tracker_checkpoint(
        v2_path,
        TrackerPPOAgent(obs_dim=SEMANTIC_REFERENCE_TRACKER_OBS_DIM),
        observation_layout=SEMANTIC_REFERENCE_TRACKER_LAYOUT,
    )
    save_tracker_checkpoint(
        v3_path,
        TrackerPPOAgent(obs_dim=REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM),
        observation_layout=COMMAND_REFERENCE_TRACKER_LAYOUT,
    )

    v1_agent, v1_metadata = load_tracker_checkpoint(v1_path)
    assert v1_agent.obs_dim == REFERENCE_TRACKER_OBS_DIM
    assert v1_metadata["observation_layout"] == REFERENCE_TRACKER_LAYOUT

    with pytest.raises(ValueError, match="does not match expected layout"):
        load_tracker_checkpoint(v2_path)

    v2_agent, v2_metadata = load_tracker_checkpoint(
        v2_path, expected_layout=SEMANTIC_REFERENCE_TRACKER_LAYOUT
    )
    assert v2_agent.obs_dim == SEMANTIC_REFERENCE_TRACKER_OBS_DIM
    assert v2_metadata["observation_layout"] == SEMANTIC_REFERENCE_TRACKER_LAYOUT

    v3_agent, v3_metadata = load_tracker_checkpoint(
        v3_path, expected_layout=COMMAND_REFERENCE_TRACKER_LAYOUT
    )
    assert v3_agent.obs_dim == REFERENCE_TRACKER_CLEAN_COMMAND_OBS_DIM
    assert v3_metadata["observation_layout"] == COMMAND_REFERENCE_TRACKER_LAYOUT


def test_existing_zigzag_v55_checkpoint_still_loads_when_present() -> None:
    checkpoint = (
        ROOT
        / "lsy_drone_racing/control/checkpoints/v55_tracker_qualification/"
        / "zigzag_or_lemniscate_tracking/"
        / "v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt"
    )
    if not checkpoint.exists():
        pytest.skip("local v55 zigzag checkpoint not present")

    agent, metadata = load_tracker_checkpoint(checkpoint)

    assert agent.obs_dim == REFERENCE_TRACKER_OBS_DIM
    assert metadata["observation_layout"] == REFERENCE_TRACKER_LAYOUT


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
        reference.current_point, np.array([0.9, 0.0, 0.65], dtype=np.float32), atol=1e-6
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
        cruise.current_point, np.array([-1.05, 0.0, 0.75], dtype=np.float32), atol=1e-6
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
    assert (
        np.linalg.norm(cross.current_point - align.current_point)
        <= GeometricSlowGatePlanner.CROSS_ENTRY_MAX_REFERENCE_STEP_M + 1e-6
    )
    assert cross.desired_speed == pytest.approx(0.32)

    obs["pos"] = np.array([0.34, 0.0, 0.75], dtype=np.float32)
    still_cross = generator.reference(obs)
    assert still_cross.phase == "cross"


def test_level3_geometric_planner_clamps_phase3_to_phase4_reference_jump() -> None:
    obs = sample_obs()
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75]], dtype=np.float32)
    obs["obstacles_visited"] = np.array([False])
    generator = ReferenceTrajectoryGenerator("level3")

    obs["pos"] = np.array([-0.50, 0.0, 0.75], dtype=np.float32)
    generator.reset(obs)
    align = generator.reference(obs)
    assert align.phase == "align"

    obs["pos"] = np.array([-0.24, 0.0, 0.75], dtype=np.float32)
    first_cross = generator.reference(obs)
    assert first_cross.phase == "cross"
    assert first_cross.desired_speed == pytest.approx(0.32)
    assert np.linalg.norm(first_cross.current_point - align.current_point) == pytest.approx(
        GeometricSlowGatePlanner.CROSS_ENTRY_MAX_REFERENCE_STEP_M, abs=1e-6
    )

    second_cross = generator.reference(obs)
    assert second_cross.phase == "cross"
    assert (
        np.linalg.norm(second_cross.current_point - first_cross.current_point)
        <= GeometricSlowGatePlanner.CROSS_ENTRY_MAX_REFERENCE_STEP_M + 1e-6
    )
    assert second_cross.current_point[0] > first_cross.current_point[0]


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
    obs["gates_pos"] = np.array([[0.0, 0.0, 0.75], [2.0, 0.0, 0.75]], dtype=np.float32)
    obs["gates_quat"] = np.array([[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32)
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
    assert tracker_env_mode_from_config(gate_config, "gate_aperture_reference") == "gate_aperture"
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
