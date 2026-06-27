# v62d_004 Subagent Reviews

Date: 2026-06-27

## tracker_eval_metrics

Verdict: do not promote `v62d_004`. Best milestone is `5M`:

```text
lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_step_005000000.pkl
```

Primary evidence:

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5M | -2.0530 | 0.1958 | 0.1634 | 0.7740 | 0.0000 | 0.000116 | -3.2704 |
| 10M | -2.0840 | 0.2004 | 0.1685 | 0.7873 | 0.0000 | 0.000291 | -3.3286 |
| 15M | -2.1321 | 0.2066 | 0.1754 | 0.8108 | 0.0000 | 0.000261 | -3.4170 |
| 20M | -2.1671 | 0.2125 | 0.1820 | 0.8285 | 0.0000 | 0.000416 | -3.4874 |
| 25M | -2.1752 | 0.2138 | 0.1833 | 0.8323 | 0.0000 | 0.000497 | -3.5029 |
| 30M/final | -2.2033 | 0.2184 | 0.1886 | 0.8484 | 0.0000 | 0.000578 | -3.5605 |

Against the v62c 7M default baseline, position and cross-track look much better,
but the generator distribution changed. Velocity is `4.63%` worse
(`0.7740` vs `0.7397`) and action delta is `18.2x` worse.

Against the v62c 7M speed-bin baseline, v62d_004 5M is modestly better on
reward, position, cross-track, and velocity, but velocity improves only
`5.37%`, below the `10%-15%` promotion threshold, while action delta is `3.42x`
worse.

Failure modes:

```text
early peak at 5M
monotonic milestone drift through final
velocity obedience improves only modestly under the fair speed-bin comparison
action smoothness regresses
```

## tracker_wandb_ppo

Verdict: action/PPO plumbing is healthy enough to trust the behavior metrics as
executed-policy metrics, but critic/value health is still weak. Use
checkpoint-backed milestone ranking rather than final-only training curves.

Evidence:

```text
action_distribution = tanh_squashed_gaussian
stored-vs-env logprob final ~= 3.15e-7
stored-vs-env logprob at 5M audit ~= 3.11e-7
rollout_action_any_dim_clipped_fraction = 0.0
rollout_action_clip_fraction = 0.0
final approx_kl = 0.00378
final clip_fraction = 0.0452
```

The main weakness remains critic/value scale:

```text
final advantages = -20.77 +/- 31.33
final returns = -305.64 +/- 31.34
final values = -284.87 +/- 0.0015
explained_variance = 0.000042
value_loss = 704
```

Late drift signs:

```text
action magnitude rises
entropy narrows
late clip fraction rises
value std collapses
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_004_speed_bin_balanced_generator_30m_20260627
```

## tracker_structure_research

Recommendation: launch a `v62d_005` value/return-scale candidate while keeping
the `speed_bin_balanced` generator profile.

Reasoning:

```text
v62d_004 helped command-distribution coverage
the 5M win is modest and fragile
milestones drift worse after 5M
velocity remains below promotion threshold
v62d_003 already showed blunt velocity reward scaling is insufficient
action/logprob path is healthy
critic/return scale remains the repeated structural issue
```

Next candidate should keep:

```text
command_generator_profile=speed_bin_balanced
action_distribution=tanh_squashed_gaussian
observation_layout=level3_reference_tracker_command_v3
no gate/aperture/race/finish/stage reward
```

and test a narrower value/return stabilization knob before more generator or
reward-number tuning.
