# v62d_004 Hypothesis: Speed-Bin Balanced Generator

Date: 2026-06-27

## Candidate

```text
id: v62d_004
lane: v62d_004_speed_bin_balanced_generator_30m
family: C_generator_velocity_distribution
```

## Hypothesis

v62d_003 showed that simply doubling the generic velocity-error coefficient is
not enough: best velocity improved only about `2.4%`, while action smoothness
got materially worse. The next candidate should change the training data
distribution instead of further increasing the scalar reward.

Hypothesis:

```text
The v60/v62 command generator under-represents clean commanded-speed examples.
If the generator deliberately balances speed bins and transition types, the
tracker will learn speed obedience from the concrete reference horizon,
desired_velocity, desired_speed, and heading command itself.
```

## Intended Generator Change

Implement a generator variant that increases coverage of:

```text
constant-speed pass-through segments
explicit deceleration ramps
hold/brake segments
low-speed-through segments
recover-speed transitions
```

The generator should keep point spacing consistent with:

```text
spacing ~= desired_speed * dt
```

Suggested speed-bin coverage:

```text
hold/brake: 0.00-0.10 m/s
approach-decelerate: 0.55-0.78 -> 0.15-0.24 m/s
low-speed-through: 0.25-0.35 m/s
steady pass-through: 0.45-0.80 m/s
recover-speed: smooth ramp from low speed toward 0.55-0.80 m/s
```

The generator should produce longer clean windows for each behavior so the
policy can learn the command semantics from future points plus velocity, not
only from a one-step target.

## Fixed Settings

Use v62c-style PPO/reward settings unless builder/checker evidence requires a
small support change:

```text
action_distribution=tanh_squashed_gaussian
command_vel_error_coef=default
value_target_scale=1.0
num_minibatches=4
update_epochs=1
num_envs=1024
num_steps=32
checkpoint_interval=5M
total_timesteps=30,015,488
train_from_scratch=true
```

## Hard Boundaries

```text
do not modify config/level3.toml
do not add gate/aperture/race/finish/stage rewards
do not add gate/obstacle/planner-phase actor inputs
keep actor observation level3_reference_tracker_command_v3
keep tanh_squashed_gaussian action distribution
do not resume from v62c or v62d checkpoints
```

## Required Support Before Training

This candidate changes generator semantics, so run builder/checker before
training:

```text
builder: implement the smallest generator option/flag needed for v62d_004
checker: verify default generator behavior is unchanged unless the new flag is
         enabled; verify clean no-gate reward/input boundaries; verify both
         config/level3.toml and config/level3_tracker_free_space.toml unchanged
```

After support passes, train from scratch for 30M, evaluate
`5M/10M/15M/20M/25M/30M/final`, audit the best checkpoint, then run the three
reviewers before deciding whether to promote.
