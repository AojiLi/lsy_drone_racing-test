# v62d 10-Candidate Hold Decision

Date: 2026-06-27

## Decision

```text
hold_for_user_review
```

Do not launch `v62d_011`.

Do not continue `v62d_010`.

Do not run 60M+ maturation from any v62d checkpoint.

## Why

The active v62d objective requires:

```text
Every 10 candidates, write a meta-review.
If 10 consecutive candidates fail to improve the frontier, pause candidate
execution and write a hold packet for user review.
```

That condition is now met:

```text
v62d_001 through v62d_010 all failed to promote over v62c 7M.
```

## Current Frontier

The current frontier remains:

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Frontier metrics:

```text
reward_mean=-4.8459
command_position_error=0.6573
cross_track_error=0.5214
command_velocity_error=0.7397
done_mean=0.00391
balanced_score=-7.5365
```

## Best Partial Signal

The best partial velocity signal is still:

```text
v62d_008_velocity_contrast_constant_speed_generator_30m:30M
```

It improved velocity strongly:

```text
command_velocity_error: 0.7397 -> 0.5708
improvement: 22.84%
```

But it failed promotion because position worsened too much:

```text
command_position_error: 0.6573 -> 0.7943
worsening: 20.84%
```

## Latest Candidate Result

`v62d_010_velocity_contrast_cross_track_guard_30m` did not solve the
velocity/spatial tradeoff.

Best balanced checkpoint:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_30m/v62d_010_velocity_contrast_cross_track_guard_30m_step_005000000.pkl
```

It improved spatial metrics under the same velocity-contrast profile but lost
velocity obedience:

```text
position error = 0.6613
cross-track error = 0.4946
velocity error = 0.9339
balanced score = -8.6649
```

The `30M/final` checkpoint had better velocity:

```text
velocity error = 0.6061
```

but spatial tracking collapsed:

```text
position error = 0.9581
cross-track error = 0.7451
balanced score = -9.9886
```

## Hard Boundaries Remain

Do not modify:

```text
config/level3.toml
```

Do not add:

```text
gate reward
aperture reward
race reward
finish reward
stage reward
gate/obstacle/planner-phase actor input
```

Keep:

```text
actor observation = level3_reference_tracker_command_v3
action_distribution = tanh_squashed_gaussian
```

unless the user explicitly approves a new structural lane.

## User Review Needed

The next candidate should not be chosen automatically. The user should choose
or approve the next direction:

```text
1. command-conditioned reward / generator fix
2. targeted critic/value support
3. staged command curriculum
4. architecture or capacity change
5. stop v62d and return to planner integration or another lane
```

Until then, v62d candidate execution is held.
