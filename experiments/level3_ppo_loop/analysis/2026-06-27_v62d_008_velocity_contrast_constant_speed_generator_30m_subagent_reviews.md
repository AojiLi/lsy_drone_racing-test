# v62d_008 Subagent Reviews

Date: 2026-06-27

Candidate:

```text
v62d_008_velocity_contrast_constant_speed_generator_30m
```

## tracker_eval_metrics

Verdict: support `promote_candidate_as_current_best`, with caveat that this is
only a tracker-candidate frontier promotion and not planner-integration
approval.

Best checkpoint:

```text
lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_generator_30m/v62d_008_velocity_contrast_constant_speed_generator_30m_step_030000000.pkl
```

Key comparison:

| metric | v62c 7M | v62d_008 30M | reviewer note |
|---|---:|---:|---|
| reward | -4.8459 | -4.6294 | better |
| velocity error | 0.7397 | 0.5708 | 22.84% better, clears velocity bar |
| position error | 0.6573 | 0.7943 | 20.84% worse |
| cross-track | 0.5214 | 0.5449 | 4.50% worse |
| done mean | 0.00391 | 0.00219 | better |
| action delta | 0.00000639 | 0.00001553 | 2.43x worse but still small |
| balanced score | -7.5365 | -7.4853 | slightly better |

The reviewer notes that v62d_008 is the first candidate to clear the velocity
promotion bar and improves velocity versus v62d_004, v62d_006, and v62d_007,
while flagging spatial regression as the next issue.

## tracker_wandb_ppo

Verdict: PPO plumbing is healthy enough to trust the run and continue this
family, but not healthy or complete enough to promote as a balanced tracker or
run 60M+ maturation as-is.

Evidence:

```text
eval reward: -5.8990 -> -4.6284
eval position error: 0.8704 -> 0.7963
eval velocity error: 0.6748 -> 0.5710
eval cross-track: 0.5902 -> 0.5446
eval done mean: 0.00552 -> 0.00219
action clipping: 0.0
stored/env logprob consistency: ~3.24e-7
final KL: 0.00482
final clip fraction: 0.05795
final entropy: -2.730
```

Main PPO caveat:

```text
explained variance ~= 2.48e-5
returns ~= -291.23 +/- 28.23
values ~= -283.78 +/- 0.0012
```

The critic remains almost state-constant. Local W&B history showed velocity
improving late while position and cross-track drifted worse. Recommendation:
continue only as a bounded follow-up that preserves the velocity-contrast signal
while fixing spatial/critic tradeoffs.

## tracker_structure_research

Verdict: do not promote v62d_008 and do not run 60M confirmation. It hits the
velocity screen but misses the promotion contract because position worsens too
much.

Reasoning:

```text
velocity improves 22.8%: 0.7397 -> 0.5708
position worsens 20.8%: 0.6573 -> 0.7943
cross-track worsens 4.5%, barely inside the limit
done improves
audit is clean
```

Recommended next candidate:

```text
v62d_009_velocity_contrast_spatial_guarded_generator
```

Keep the v62d_008 paired low/medium/high speed contrast, but restore
speed-bin-like spatial guards:

```text
shorter pass_dist / slow_dist / recover_dist
earlier deceleration, closer to decel_fraction=0.42 than 0.70
same no-gate command structure
same command_v3 actor observation
same tanh-squashed Gaussian action distribution
same default reward coefficients
same 1024x32 rollout geometry
```

Builder/checker is required before 30M because the next candidate changes
generator semantics.

## Main-Agent Synthesis

The main decision follows the stricter promotion contract from the user goal:
v62d_008 is not promoted because position error worsened by more than the
allowed 5%. It is still a valuable candidate because it is the first run to
produce a large velocity-obedience improvement without action/logprob failure.

Next action:

```text
launch_best_of_family_combination:
v62d_009_velocity_contrast_spatial_guarded_generator
```

This should preserve the v62d_008 velocity signal while recovering the spatial
tracking discipline seen in v62d_004/speed-bin style generator settings.
