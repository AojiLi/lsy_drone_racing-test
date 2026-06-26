# v55 GeometricSlowGatePlanner 500-Step Trace Diagnostics

## Scope

This is a planner-integration diagnostic run, not PPO training.

```text
config: config/level3.toml
planner: GeometricSlowGatePlanner
tracker checkpoint: lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
seeds: 101-120
level3 steps: 500
trace rows: 4477
```

The evaluator now records per-step:

```text
position
target/first-gate local x/y/z
planner reference point
planner phase
desired speed
physical action
max gate index
environment termination reason
```

## Result

```text
nonzero_first_gate_progress_count = 20 / 20
gate0_pass_count = 3 / 20
gate0_pass_seeds = 113, 117, 120
early_termination_count = 2 / 20
termination_reasons = {"contact": 15, "max_steps": 5}
all_finite = true
checkpoint_backed = true
config/level3.toml unchanged = true
```

Compared with the prior 150-step smoke, gate0 passes increased from `1/20` to
`3/20`. More horizon helps, but the main blocker is not just insufficient
time.

## Failure Types

```text
passed_gate0_then_contact_later: 3 seeds
contact_before_gate_plane: 7 seeds
contact_near_gate_without_pass: 3 seeds
crossed_plane_far_outside_aperture_timeout: 5 seeds
immediate_or_early_contact: 2 seeds
```

The dominant failure is contact near or before the first gate. For seeds that
crossed the first-gate plane without a pass, the drone was usually far outside
the aperture in Y/Z.

## Successful Versus Failed Crossings

Successful gate0 pass examples:

```text
seed 113: best near-plane x=0.107, YZ error=0.095
seed 117: best near-plane x=-0.037, YZ error=0.186
seed 120: best near-plane x=0.072, YZ error=0.145
```

Failed plane-crossing examples:

```text
seed 103: best near-plane x=0.194, YZ error=0.623
seed 104: best near-plane x=0.198, YZ error=0.614
seed 110: best near-plane x=0.193, YZ error=1.133
seed 112: best near-plane x=0.195, YZ error=0.590
```

Interpretation: the planner/tracker loop can move through the first-gate plane,
but most failures do not pass through the aperture. The successful seeds are
centered within roughly `0.10m-0.19m`; the failed crossing seeds are commonly
`0.5m+` off-center.

## Diagnosis

The current geometry planner is too eager to enter cross/recover once the drone
is near or past the gate plane. It does not sufficiently require stable Y/Z
centering before crossing, and several seeds begin effectively near/past the
first-gate plane with large lateral/vertical error. The PPO tracker follows the
given references reasonably on some seeds, but the planner reference sequence is
not conservative enough around the aperture.

This is a planner/reference-design problem first, not a reason to start another
long PPO training run immediately.

## Recommended Next Action

Do a planner-only tuning pass before any long Level3 training:

1. Hold `align` until aperture Y/Z error is much lower, with a hard guard for
   near-plane seeds.
2. Move `pre_align` farther back and reduce cross speed until centered.
3. Add a recovery guard so phase 5 does not run while target gate is still 0
   and the first-gate aperture has not been passed.
4. For seeds initialized near or past the gate plane but far off aperture, back
   out to a safe pre-gate reference instead of treating the state as recover.
5. Re-run the same 500-step trace smoke on seeds `101-120`.

Do not launch long PPO/tracker training from this diagnostic alone.
