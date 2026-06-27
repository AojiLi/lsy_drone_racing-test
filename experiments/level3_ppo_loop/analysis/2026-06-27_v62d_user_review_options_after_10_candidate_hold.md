# v62d User Review Options After 10-Candidate Hold

Date: 2026-06-27

## Current State

v62d candidate execution is held.

Reason:

```text
v62d_001 through v62d_010 all failed to promote over v62c 7M.
```

Current frontier:

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Do not launch `v62d_011` until the user approves a direction.

## What The First 10 Candidates Proved

The search is not blocked by action-distribution plumbing:

```text
tanh_squashed_gaussian action path is healthy
action clipping is effectively zero
stored-vs-env logprob error is around 3e-7
W&B / JAX rollout speed are healthy
```

The search is blocked by behavior:

```text
speed obedience and spatial tracking are not being preserved together
```

Best partial signal:

```text
v62d_008 velocity_contrast_constant_speed
velocity error: 0.7397 -> 0.5708
improvement: 22.84%
```

But:

```text
position error: 0.6573 -> 0.7943
worsening: 20.84%
```

The attempted fixes failed:

```text
v62d_009: restored spatial behavior but lost velocity gain
v62d_010: global cross-track guard split into 5M spatial / 30M velocity collapse
```

## Option 1: Command-Conditioned Reward / Generator Fix

Status:

```text
recommended
```

Hypothesis:

```text
The v62d_008 generator has the only strong velocity signal.
The failure is concentrated in moving-command spatial drift, especially
pass-through. A global cross-track coefficient is too blunt. The next fix should
condition spatial pressure by command type and avoid fighting speed obedience
in hold/slow/recover segments.
```

What this would mean:

```text
Keep command_generator_profile=velocity_contrast_constant_speed as the base.
Add command-conditioned reward support, for example:
  pass_through: stronger cross-track / along-track corridor
  low_speed_through: moderate cross-track, strict desired-speed band
  hold_or_brake: low speed + overshoot/settle, not moving-corridor pressure
  recover_speed: smooth speed recovery, light spatial pressure
```

Why it is better than v62d_010:

```text
v62d_010 used one global trajectory_cross_track_coef=1.8.
That punished all situations similarly and did not preserve the velocity gain.
Command-conditioned reward can target the failing segment instead of damping
the whole behavior distribution.
```

First approved step:

```text
builder/checker support packet for command-conditioned reward coefficients and
per-command metric reporting, with no training until support passes.
```

Risk:

```text
More code complexity in reward/eval.
Needs careful checker validation to ensure no gate/aperture/race reward enters.
```

## Option 2: Staged Command Curriculum

Status:

```text
also strong, possibly paired with Option 1
```

Hypothesis:

```text
The mixed command generator is asking one policy to learn pass-through,
braking/hold, low-speed-through, and recover all at once. The 10-candidate
history suggests the policy can improve one axis while forgetting another.
```

What this would mean:

```text
Train/evaluate command stages separately before mixing:
  stage A: pass-through spatial corridor
  stage B: brake/hold settle
  stage C: low-speed-through non-stop motion
  stage D: recover-speed smoothness
  stage E: mixed command distribution
```

First approved step:

```text
write staged curriculum support: generator profiles + per-command gates.
Then run the first 30M candidate from scratch only after support/checker passes.
```

Risk:

```text
More candidate budget.
Stage-specific wins may not transfer into the mixed policy unless the final
mixing curriculum is designed carefully.
```

## Option 3: Targeted Critic / Value Support

Status:

```text
worth doing, but not my first choice as the next candidate
```

Hypothesis:

```text
The critic is repeatedly weak: explained variance near zero, values almost
constant, and high value loss/return pressure. This may be limiting stable
learning.
```

Why not first:

```text
v62d_001, v62d_002, and v62d_005 already tried value-target scaling variants.
They changed value behavior but did not improve the tracker frontier.
```

Better version if approved:

```text
Do not just change value_target_scale again.
Instead design a targeted critic-support packet:
  return normalization or PopArt-like value normalization
  critic loss coefficient sweep with fixed behavior gates
  per-command value diagnostics
```

Risk:

```text
Could improve PPO diagnostics without solving the behavioral velocity/spatial
tradeoff.
```

## Option 4: Architecture / Capacity Change

Status:

```text
reasonable later, not the cleanest immediate next step
```

Hypothesis:

```text
The current feedforward tracker may be weak at switching between command
semantics such as pass-through, brake, slow-through, and recover.
```

Possible changes:

```text
larger MLP
GRU / recurrent tracker
command-history features
asymmetric critic
```

Why not first:

```text
The current data already shows a strong generator/reward conflict. Changing
architecture now could hide whether the command interface/reward is wrong.
```

Risk:

```text
More moving parts and less interpretable comparisons.
```

## Option 5: Stop v62d And Return To Planner Integration

Status:

```text
valid if the user wants to stop optimizing the generic tracker
```

Rationale:

```text
Planner integration may reveal that the current v62c/v62d tracker is enough for
some conservative geometry planner work, even if it has not met tracker
excellence.
```

Risk:

```text
The prior planner smoke suggested the tracker/reference interface was still a
major bottleneck near gate crossing, so this may return to the same problem.
```

## My Recommendation

Approve a combined direction:

```text
Option 1 first, with Option 2 structure:
command-conditioned reward/generator support + staged per-command gates
```

Concrete next approved lane would be:

```text
v62d_011_command_conditioned_velocity_contrast_curriculum_support
```

But it should start with support only:

```text
1. add command-conditioned reward coefficient support
2. add per-command gate/metric reporting
3. add stage-specific command generator profiles
4. checker verifies no gate/aperture/race/finish/stage reward or inputs
5. only then approve a 30M from-scratch v62d_011 candidate
```

Reason:

```text
v62d_008 proves speed obedience can be learned.
v62d_009/v62d_010 prove global/coarse spatial fixes are too blunt.
The next test should target the exact failure mode: pass-through spatial drift
without suppressing speed obedience in other command modes.
```

## Required User Choice

Choose one:

```text
A. Approve Option 1+2 as v62d_011 support-first lane.
B. Approve targeted critic/value support first.
C. Approve architecture/capacity change.
D. Stop v62d and return to planner integration.
E. Hold all training/search for now.
```

Until the user chooses, v62d candidate execution remains held.
