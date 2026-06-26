import numpy as np
import pytest

from scripts.check_level3_reference_tracker_smoke import make_level3_trace_row


def test_make_level3_trace_row_reports_aperture_yz_error() -> None:
    obs = {
        "pos": np.array([-0.5, 0.2, 0.6], dtype=np.float32),
        "gates_pos": np.array([[0.0, 0.0, 0.7]], dtype=np.float32),
        "gates_quat": np.array([[0.0, 0.0, 0.0, 1.0]], dtype=np.float32),
        "target_gate": np.array(0, dtype=np.int32),
        "vel": np.array([0.3, 0.0, 0.0], dtype=np.float32),
    }
    diagnostics = {
        "v54_tracker_aperture_y": 0.05,
        "v54_tracker_aperture_z": -0.15,
        "v54_tracker_gate_local_vx": 0.3,
        "v54_tracker_phase_id": 3.0,
    }

    row = make_level3_trace_row(
        seed=101,
        step=7,
        pre_target_gate=0,
        post_target_gate=0,
        max_gate_index=0,
        obs=obs,
        info={},
        action=np.zeros(4, dtype=np.float32),
        diagnostics=diagnostics,
        terminated=False,
        truncated=False,
        controller_finished=False,
    )

    assert row["aperture_y"] == pytest.approx(0.05)
    assert row["aperture_z"] == pytest.approx(-0.15)
    assert row["aperture_yz_error"] == pytest.approx(
        np.hypot(row["gate_local_y"] - 0.05, row["gate_local_z"] + 0.15)
    )
