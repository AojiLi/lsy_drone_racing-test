# v55 Tracker Decision: Multi-Point Reference Passed, Unlock L-Shape Tracking

Date: 2026-06-25

Decision: `promote_to_next_tracker_stage`

Passed stage:

```text
multi_point_reference
```

Next stage:

```text
l_shape_tracking
```

## Decision

`multi_point_reference` passed its qualification gate. Advance the tracker
ladder to `l_shape_tracking`.

Use this checkpoint as the preferred initialization:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/multi_point_reference/v55_tracker_multi_point_from_heading_attempt001_step_020957760.ckpt
```

## Evidence

Official gate checker passed for:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_multi_point_from_heading_attempt001_step1m_metrics.json
```

Key metrics:

```text
segment_completion_rate = 1.0
crash_rate = 0.0
mean_position_error_m = 0.1784248650074005
p90_position_error_m = 0.2786217927932739
mean_switch_overshoot_m = 0.004599432460963726
mean_action_delta_l2 = 0.009103040210902691
```

## Next Action

Train `l_shape_tracking` with vectorized PPO:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 8000000
--checkpoint-interval 1000000
--hidden-dim 256
--num-minibatches 8
--update-epochs 4
--learning-rate 3e-4
--initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/multi_point_reference/v55_tracker_multi_point_from_heading_attempt001_step_020957760.ckpt
```

Evaluate all `l_shape_tracking` milestone checkpoints and require
`scripts/check_level3_tracker_stage_gate.py --stage l_shape_tracking` with
prerequisite history before unlocking `curve_tracking`.

Do not launch planner-driven Level3 training yet. The tracker still needs
L-shape, curve, sharp curve, gate-aperture, and planner integration gates.
