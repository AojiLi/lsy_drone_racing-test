# v55 Tracker Decision: Launch Hover Airborne Error Curriculum

Date: 2026-06-25

Decision: `launch_tracker_structural_fix`

Stage: `hover`

Approved next lane:

```text
v55_hover_airborne_error_curriculum_attempt003
```

## Decision

Do not continue the same `hover` setup for more steps.
Do not unlock `point_hold`.
Do not switch to `256 x 128` as the first fix.

First fix the hover task semantics:

1. Make the free-space tracker config start near an airborne hover altitude,
   not on the floor.
2. Make hover reference generation command a small desired velocity toward the
   anchor when outside the hold band, and only command zero speed once near.
3. Increase crash penalty enough that early crash cannot outscore imperfect
   survival.
4. Add PPO diagnostics for `approx_kl`, `old_approx_kl`, and
   `explained_variance`.

This touches tracker env/reference/reward/trainer semantics, so it requires a
builder/checker gate before training.

## Evidence

Attempt002 completed a bounded `1024 envs x 32 steps` hover maturation chunk.
The best checkpoint was:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_vector1024_attempt002_step_000500000.ckpt
```

Its hard stage metrics were:

```text
success_rate = 0.0
crash_rate = 0.0
mean_position_error_m = 0.6509503126144409
p90_position_error_m = 0.6510815620422363
mean_speed_mps = 0.0034038268495351076
mean_action_delta_l2 = 0.0008624627371318638
```

This is stable non-movement, not successful hover. Later checkpoints regressed
to `100%` crash, so the same hypothesis did not improve with more of the
default chunk.

## Next Training Command Shape

After checker approval, run attempt003 with the same baseline rollout geometry
to isolate the curriculum/reward fix:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 1000000
--checkpoint-interval 250000
```

Use W&B run name:

```text
v55_tracker_hover_airborne_error_curriculum_attempt003
```

Evaluate `250k`, `500k`, `750k`, and final. Run the existing hover stage gate.

If attempt003 still fails but shows real position-error improvement without
late crash collapse, consider same-stage extension. If it still plateaus or
collapses, run the three-review analysis again before changing horizon to
`256 x 128` or making a larger reward/curriculum change.
