# Decision: Split V60 Clean Command Reward From Legacy Reward

Date: 2026-06-26T21:32:00+02:00

Decision type: `launch_tracker_structural_fix`

## Decision

Do not delete the historical tracker reward fields globally. Keep the legacy
reward path for old v1/v2 checkpoints, gate-aperture diagnostics, and older
tests.

For v60, use a separate clean reward model:

```text
ReferenceCommandReward
```

The legacy reward path remains:

```text
ReferenceTrackerReward
LegacyTrackerReward = ReferenceTrackerReward
```

## V60 Clean Reward Scope

`ReferenceCommandReward` contains only local tracker-command terms:

```text
pos_error
vel_error / desired_speed_error
heading_error
action_penalty
action_delta_penalty
progress_to_current_reference
brake/hold speed penalty
low-speed-through speed penalty
low-speed-through stop penalty
recover speed error
crash_penalty
```

It does not compute or log reward diagnostics for:

```text
gate_center
gate_x_progress
gate_cross_bonus
gate_recover_bonus
gate_linger_penalty
obstacle_penalty
finish
race_progress
stage_progress
```

## Routing Rule

When the task is:

```text
reference_command_no_gate_reward
```

the tracker env now defaults to `ReferenceCommandReward`.

Other tracker tasks continue to use the legacy `ReferenceTrackerReward` unless a
custom reward model is explicitly passed.

## Metadata Rule

v60 checkpoints now record:

```text
reward_model = reference_command_reward
```

and `reference_command_no_gate_reward` still forces these coefficients to zero
in checkpoint metadata:

```text
gate_center_coef
obstacle_coef
gate_x_progress_coef
gate_cross_bonus
gate_recover_bonus
gate_linger_penalty_coef
```

## Validation

Focused tests:

```text
pixi run -e tests pytest \
  tests/unit/control/test_level3_reference_tracker_env.py \
  tests/unit/scripts/test_level3_tracker_stage_evaluator.py \
  tests/unit/scripts/test_level3_tracker_stage_gate.py -q
```

Result:

```text
38 passed, 1 warning
```

Tiny trainer smoke:

```text
task = reference_command_no_gate_reward
observation_layout = level3_reference_tracker_command_v3
obs_dim = 56
reward_model = reference_command_reward
gate/obstacle coefficients = 0.0
semantic command-speed coefficients active
```

## Next Action

Rerun the bounded v60 smoke with this clean reward model before any `8M`
maturation chunk.

Do not launch planner-driven Level3 long training from this change.
