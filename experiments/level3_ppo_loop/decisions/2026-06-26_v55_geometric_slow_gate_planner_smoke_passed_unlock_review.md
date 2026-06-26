# v55 Decision: Planner Smoke Passed, Unlock Manual Long-Training Review

## Decision

`planner_integration_smoke` passed. Unlock:

```text
manual_long_level3_training_review
```

Do not automatically start long Level3 planner-tracker training from this
result.

## Evidence

Formal smoke used:

```text
config: config/level3.toml
planner: GeometricSlowGatePlanner
tracker checkpoint: lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
seeds: 101-120
level3 steps: 150
```

Gate-check result:

```text
passed = true
next_stage_unlocked = manual_long_level3_training_review
failures = []
```

Key metrics:

```text
nonzero_first_gate_progress_ratio = 1.0
gate0_pass_count = 1
gate0_pass_seed = 113
early_termination_ratio = 0.1
all_finite = true
checkpoint_backed = true
level3_toml_diff_clean = true
```

## Interpretation

The geometric planner is not merely producing finite actions; it is now moving
the PPO tracker forward in the first-gate frame on every validation seed and has
one confirmed gate0 pass.

This is still not a Level3 success-rate result. It is a planner-interface gate.
The next decision should be a manual long-training/review packet, because a
longer Level3 run should decide what to optimize and what diagnostics to collect
instead of blindly continuing.

## Required Next Review

Before launching a longer run, decide:

1. Whether 150 steps is too short and a longer planner smoke should be run first.
2. Whether to add reference trajectory dumps for failed seeds.
3. Whether the planner should be tuned for slower cross phase or stronger
   pre-gate alignment.
4. Whether the tracker needs a new training stage based on planner-generated
   reference families.
5. Whether to approve a bounded longer Level3 planner-tracker run.
