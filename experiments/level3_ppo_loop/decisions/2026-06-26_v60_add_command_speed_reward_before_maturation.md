# Decision: Add V60 Command-Speed Reward Before Maturation

Date: 2026-06-26T21:24:00+02:00

Decision type: `change_tracker_reward_numbers`

## Decision

Before running the v60 `8M` maturation chunk, add small command-specific speed
reward terms for the generic no-gate command tracker:

```text
hold_or_brake:
  penalize speed above 0.12 m/s

low_speed_through:
  penalize speed error from desired_speed
  penalize stopping below 0.12 m/s

recover_speed:
  penalize speed error from desired_speed
```

This is not gate reward. It is local command-following reward for the bottom
tracker.

## Rationale

The bounded v60 smoke proved the pipeline is clean, but it also showed the old
default reward was too generic for the real v60 learning target. With the old
defaults, the tracker mostly learned from:

```text
current / next / lookahead reference
desired_velocity
desired_speed
desired_heading
generic position and velocity tracking
```

That is clean, but it may be too weak to teach the behaviors the planner needs:

```text
pass_through: keep moving
hold_or_brake: slow down and stabilize
low_speed_through: move slowly without stopping dead
recover_speed: restore speed smoothly
```

The new terms keep the boundary intact: no gate pass, aperture crossing,
finish, race progress, stage progress, or target-gate transition reward.

## Implemented Defaults

```text
semantic_brake_speed_coef = 1.0
semantic_slow_speed_coef = 0.8
semantic_slow_stop_coef = 0.8
semantic_recover_speed_coef = 0.4
```

For `reference_command_no_gate_reward`, gate/aperture coefficients are still
forced to zero by the trainer.

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
37 passed, 1 warning
```

Tiny trainer smoke:

```text
task = reference_command_no_gate_reward
observation_layout = level3_reference_tracker_command_v3
obs_dim = 56
total_timesteps = 1024
num_envs = 4
num_steps = 64
gate/aperture coefficients = 0.0
semantic_brake_speed_coef = 1.0
semantic_slow_speed_coef = 0.8
semantic_slow_stop_coef = 0.8
semantic_recover_speed_coef = 0.4
```

## Next Action

Because reward defaults changed after the previous bounded smoke, rerun the
bounded v60 smoke before the `8M` maturation chunk.

Do not launch planner-driven Level3 long training from this change.
