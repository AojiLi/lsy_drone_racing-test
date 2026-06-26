# v55 Analysis: Gate-Aperture Demoted After Architecture Clarification

## Situation

`gate_aperture_reference` attempt002 is no longer running. It left two local
intermediate checkpoints:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/gate_aperture_reference/v55_tracker_gate_aperture_phase_completion_attempt002_step_043959872.ckpt
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/gate_aperture_reference/v55_tracker_gate_aperture_phase_completion_attempt002_step_044959872.ckpt
```

These checkpoints are generated artifacts and are not part of the committed
loop decision.

## Evidence

The required tracker ladder has already passed through:

```text
hover
point_hold
point_reach
brake_to_point
line_tracking
heading_tracking
multi_point_reference
l_shape_tracking
curve_tracking
zigzag_or_lemniscate_tracking
```

The selected zigzag checkpoint is:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

Its recorded gate metrics were:

```text
path_completion_rate = 1.0
crash_rate = 0.0
mean_cross_track_error_m = 0.0987461507320404
p90_cross_track_error_m = 0.28499993681907654
mean_action_delta_l2 = 0.01048266887664795
p90_action_delta_l2 = 0.014509669505059719
```

`gate_aperture_reference` attempt001 did not crash and had small Y/Z aperture
error, but all milestones had:

```text
valid_aperture_cross_rate = 0.0
post_gate_recovery_rate = 0.0
```

This looks like a pre-plane parking local optimum, not a useful next bottleneck
for the planner-tracker architecture.

## Interpretation

The tracker should be judged by whether it can follow reference points and short
trajectories. If the planner creates a safe local trajectory through a gate, the
PPO tracker should follow it. The tracker should not need a separate
reward-shaped semantic lesson that says "cross this gate plane now".

Therefore the next informative test is planner integration smoke:

```text
planner computes reference trajectory on unchanged config/level3.toml
tracker follows that trajectory
metrics report first-gate progress, gate-0 passes, early termination, finite actions
```

If planner smoke fails, the loop should inspect the generated references and
decide whether to improve the planner reference design or add a new
tracker-training stage matching the exact trajectory family that failed.

## State Change

`gate_aperture_reference` is optional diagnostic only. The required next stage is
`planner_integration_smoke`.
