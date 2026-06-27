# v62d Meta-Review Decision: Launch v62d_010 Support

Date: 2026-06-27

Decision outcome:

```text
launch_best_of_family_combination
```

Approved next candidate:

```text
v62d_010_velocity_contrast_cross_track_guard
```

## Rationale

The meta-review shows a specific velocity/spatial tradeoff:

```text
v62d_008 teaches velocity obedience but loosens pass-through spatial tracking.
v62d_009 restores spatial discipline but erases the velocity breakthrough.
```

Per-command evidence points to pass-through cross-track drift as the v62d_008
failure:

```text
pass-through position error: +26.7%
pass-through cross-track error: +43.3%
```

But v62d_008 improves the harder speed-behavior segments:

```text
hold/brake velocity error: -56.0%
low-speed-through velocity error: -44.7%
recover velocity error: -27.1%
```

So the next candidate should keep the `velocity_contrast_constant_speed`
generator and add one generic spatial reward guard, rather than shrinking the
generator again.

## Candidate Spec

Train from scratch for 30M after support passes:

```text
candidate_id=v62d_010
lane_name=v62d_010_velocity_contrast_cross_track_guard_30m
family=E_best_of_family_combination
command_generator_profile=velocity_contrast_constant_speed
trajectory_cross_track_coef=1.8
value_target_scale=1.0
num_envs=1024
num_steps=32
num_minibatches=4
update_epochs=1
action_distribution=tanh_squashed_gaussian
```

## Required Support Gate

Before training, run builder/checker support:

```text
1. Add a narrow reward-coefficient override path for trajectory_cross_track_coef
   or a generic safe reward coefficient parser.
2. Ensure checkpoint metadata records reward_coefficients.
3. Ensure audit uses the same reward coefficient overrides.
4. Run py_compile and a support smoke.
5. Verify unchanged config/level3.toml and config/level3_tracker_free_space.toml.
```

## Hard Boundaries

Do not modify `config/level3.toml`.

Do not add gate/aperture/race/finish/stage reward.

Do not add gate/obstacle/planner-phase actor inputs.

Keep actor observation as:

```text
level3_reference_tracker_command_v3
```

Keep action distribution as:

```text
tanh_squashed_gaussian
```

Do not resume from v62c or v62d_008. Train v62d_010 from scratch after support
passes.

## Acceptance For v62d_010

Promotion still requires the original v62d gates:

```text
velocity improves by at least 10%-15% versus v62c 7M
position worsens by no more than 5%
cross-track worsens by no more than 5%
done_mean does not worsen
action_delta does not materially worsen
action/logprob audit remains ok
```

The most important diagnostic is whether `v62d_010` can preserve v62d_008's
velocity gain while reducing pass-through spatial drift.
