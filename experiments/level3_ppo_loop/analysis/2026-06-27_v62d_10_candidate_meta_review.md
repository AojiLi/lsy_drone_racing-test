# v62d 10-Candidate Meta-Review

Date: 2026-06-27

## Purpose

The active v62d search requires a meta-review every 10 candidates. It also
requires a pause for user review if 10 consecutive candidates fail to improve
the tracker frontier.

This review covers:

```text
v62c 7M baseline
v62d_001
v62d_002
v62d_003
v62d_004
v62d_005
v62d_006
v62d_007
v62d_008
v62d_009
v62d_010
```

This is a generic reference-command tracker review, not a Level3 hard eval.
It does not modify `config/level3.toml`, does not add gate/aperture/race/
finish/stage rewards, and does not approve another training run.

## Frontier

The current frontier remains:

```text
v62c 7M
lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Frontier metrics:

| metric | v62c 7M |
|---|---:|
| reward | -4.8459 |
| command position error | 0.6573 |
| cross-track error | 0.5214 |
| command velocity error | 0.7397 |
| done mean | 0.00391 |
| balanced score | -7.5365 |

The v62c milestone review found that `7M` is the best overall checkpoint.
Velocity obedience is already worse than the initial policy by `1M`; within
the trained milestone curve, `7M` is the least-bad velocity point and `8M`
starts post-peak worsening.

## Candidate Summary

| id | family | changed knob | best | decision-relevant result |
|---|---|---|---|---|
| `v62d_001` | A value/return | `value_target_scale=50`, aggressive PPO update | 5M | position/cross improved, but velocity, done, reward, and action delta collapsed |
| `v62d_002` | D PPO stabilizer | `value_target_scale=50`, conservative PPO update | 5M | cleaner than v62d_001, but still worse than v62c on velocity, done, reward, action delta, and balanced score |
| `v62d_003` | B velocity reward | `vel_error_coef=1.2` | 20M | velocity improved only `2.4%`, below promotion threshold; action delta worsened about `7.9x` |
| `v62d_004` | C generator | `speed_bin_balanced` | 5M | useful spatial/generator signal, but same-profile velocity gain only `5.37%`; action delta worsened |
| `v62d_005` | A value/return | `speed_bin_balanced`, `value_target_scale=10` | 15M | critic diagnostics improved, but velocity and action smoothness regressed badly |
| `v62d_006` | D PPO stabilizer | `speed_bin_balanced`, `256 envs x 128 steps` | 20M | valid long-rollout test, but no velocity/frontier improvement; final drifted |
| `v62d_007` | E combination | `speed_bin_balanced`, `vel_error_coef=1.2` | 15M | failed velocity objective and late drifted |
| `v62d_008` | C generator | `velocity_contrast_constant_speed` | 30M | first strong velocity signal: velocity improved `22.84%`; position worsened `20.84%`, so not promoted |
| `v62d_009` | E combination | `velocity_contrast_spatial_guarded` | 15M | spatial restored, but velocity worsened; not promoted |
| `v62d_010` | E combination | `velocity_contrast_constant_speed`, `trajectory_cross_track_coef=1.8` | 5M | spatial improved early but velocity collapsed; 30M velocity recovered only by spatial collapse |

No candidate met the promotion contract.

## Family-Level Findings

### A. Value / Return Stabilization

Tested candidates:

```text
v62d_001
v62d_005
```

Result:

```text
not enough to promote
```

Value scaling changed critic/return behavior, but it did not produce a better
tracker. The pattern was:

```text
spatial metrics may improve,
but velocity obedience, done rate, or action smoothness regresses.
```

This does not mean critic health is solved. It means blunt value-target scaling
alone is not the next high-confidence knob.

### B. Velocity Reward Numbers

Tested candidate:

```text
v62d_003
```

Result:

```text
too blunt
```

Doubling the generic velocity coefficient produced only a `2.4%` velocity
improvement and worsened action delta. It did not reach the `10%-15%` velocity
promotion threshold.

### C. Generator Velocity Distribution

Tested candidates:

```text
v62d_004
v62d_008
```

Result:

```text
most informative family
```

`v62d_004` showed that generator distribution can strongly change spatial
behavior, but it did not solve velocity. `v62d_008` was the only candidate that
clearly taught velocity obedience:

```text
velocity error: 0.7397 -> 0.5708
velocity improvement: 22.84%
```

But `v62d_008` failed because spatial tracking loosened:

```text
position error: 0.6573 -> 0.7943
position worsening: 20.84%
```

The pre-v62d_010 per-command review showed this was concentrated in
pass-through spatial drift:

```text
pass-through position error worsened 26.7%
pass-through cross-track worsened 43.3%
```

This is the strongest partial signal in the search.

### D. PPO Stabilizer

Tested candidates:

```text
v62d_002
v62d_006
```

Result:

```text
not enough by itself
```

Conservative PPO pressure helped relative to v62d_001, and `256x128` was a
valid temporal-credit test. Neither crossed the frontier. The action/logprob
path stayed healthy, so the repeated failures are not explained by tanh
sampling math.

### E. Best-of-Family Combination

Tested candidates:

```text
v62d_007
v62d_009
v62d_010
```

Result:

```text
combinations did not preserve both benefits
```

The best-of-family attempts repeatedly split the behavior:

```text
spatial discipline improves -> velocity obedience weakens
velocity obedience improves -> spatial tracking collapses
```

The clearest example is `v62d_010`:

```text
5M:  position/cross ok, velocity bad
30M: velocity better, position/cross bad
```

That means the next useful idea is probably not another global coefficient or
coarse generator contraction.

## Repeated Training-Health Finding

Across v62d, action sampling is generally healthy:

```text
action_distribution=tanh_squashed_gaussian
action clipping ~= 0
stored-vs-env logprob error ~= 3e-7
```

The repeated issue is critic/value weakness:

```text
explained variance near 0
values std tiny compared with returns std
large value loss / return scale pressure
```

However, prior value-scaling candidates did not improve the frontier. The
critic issue should remain on the table, but it should be addressed with a more
targeted support design than simply scaling targets again.

## Main Diagnosis

The search has not found a strong generic tracker yet because the current
training setup is stuck in a velocity/spatial tradeoff:

```text
The policy can be pushed to follow speeds.
The policy can be pushed to stay spatially close to the reference.
But the current generator/reward/PPO setup has not made it do both at once.
```

The most useful evidence remains:

```text
v62d_008 proves velocity obedience is learnable.
v62d_009/v62d_010 prove the attempted spatial guards erase or split that gain.
```

## Hold Condition

The active objective says:

```text
If 10 consecutive candidates fail to improve the frontier, pause candidate
execution and write a hold packet for user review.
```

That condition is now met:

```text
v62d_001 through v62d_010 all failed to promote over v62c 7M.
```

Therefore the correct next action is not to launch `v62d_011`.

## Recommended Review Questions For User

Before v62d_011, decide whether to approve one of these broader directions:

1. Command-conditioned reward rather than global reward coefficients:
   apply spatial pressure mainly where moving-command drift appears, and avoid
   punishing speed obedience in hold/slow/recover segments.

2. Better critic/value support:
   add a targeted critic stabilization or return-normalization design with a
   clear behavioral gate, not only value-target scaling.

3. Staged command curriculum:
   train or evaluate pass-through, hold/brake, low-speed-through, and recover
   distributions separately before mixing them again.

4. Architecture/capacity change:
   consider whether the current feedforward tracker is too weak for command
   switching, but only after a packet defines how to compare it fairly.

## Decision-Relevant Conclusion

```text
hold_for_user_review
```

Current frontier remains:

```text
v62c 7M
```

Do not launch `v62d_011`, do not continue `v62d_010`, and do not run 60M+
maturation until the user reviews this hold and approves the next search
direction.
