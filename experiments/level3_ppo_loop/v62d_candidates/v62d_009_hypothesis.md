# v62d_009 Hypothesis

Date: 2026-06-27

## Candidate

```text
v62d_009_velocity_contrast_spatial_guarded_generator
```

Family:

```text
E_best_of_family_combination
```

## Hypothesis

v62d_008 proved that paired low/medium/high desired-speed contrast can strongly
improve command velocity obedience. Its best checkpoint improved velocity error
by `22.84%` versus v62c 7M.

But v62d_008 also worsened position error by `20.84%`, so it is not a balanced
tracker. The next candidate should preserve the velocity-contrast signal while
restoring spatial discipline from the earlier speed-bin generator family.

## Planned Knob

Add a new explicit command-generator profile:

```text
command_generator_profile=velocity_contrast_spatial_guarded
```

Generator intent:

```text
keep v62d_008 low/medium/high speed contrast bins
shorten pass_dist / slow_dist / recover_dist versus v62d_008
move decel_fraction closer to speed_bin_balanced behavior, around 0.42
keep brake-entry, hold, low-speed-through, and recover windows explicit
keep dense rolling command horizons
```

## Guardrails

Keep:

```text
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
train_from_scratch=true
num_envs=1024
num_steps=32
num_minibatches=4
update_epochs=1
value_target_scale=1.0
command_vel_error_coef=default
```

Do not add:

```text
gate/aperture/race/finish/stage rewards
gate/obstacle/planner-phase actor inputs
Level3 track config changes
planner action output
```

## Required Support Before 30M

This candidate changes generator semantics, so builder/checker support is
required before full training.

Checker must verify:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
COMMAND_GENERATOR_PROFILES includes velocity_contrast_spatial_guarded
trainer and audit accept the new profile through shared choices
checkpoint metadata records command_generator_profile=velocity_contrast_spatial_guarded
observation_layout remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
reward_coefficients remain default / no command_vel_error_coef override
no gate/aperture/obstacle/race/finish/stage reward is introduced
support smoke metrics are finite
action/logprob audit remains ok
```

Do not launch 30M until support and checker pass.
