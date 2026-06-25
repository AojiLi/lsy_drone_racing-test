from pathlib import Path

import numpy as np
import pytest

from lsy_drone_racing.control.level3_reference_tracker import (
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
    assert (
        tracker_env_mode_from_config(gate_config, "gate_aperture_reference")
        == "gate_aperture"
    )


def test_tracker_training_config_rejects_wrong_task_family() -> None:
    gate_config = load_config(ROOT / "config/level3_tracker_gate_aperture.toml")

    with pytest.raises(ValueError, match="not valid for gate_aperture"):
        tracker_env_mode_from_config(gate_config, "line_tracking")
