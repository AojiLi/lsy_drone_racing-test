# v62d_010 Subagent Reviews

Date: 2026-06-27

Candidate:

```text
v62d_010_velocity_contrast_cross_track_guard_30m
```

## tracker_eval_metrics

Recommendation:

```text
do not promote v62d_010
```

Best v62d_010 milestone is `5M`:

```text
lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_30m/v62d_010_velocity_contrast_cross_track_guard_30m_step_005000000.pkl
```

Against the same-profile v62c 7M eval:

| metric | v62c same-profile | v62d_010 5M | result |
|---|---:|---:|---|
| reward | -5.4641 | -5.8413 | worse |
| position err | 0.7297 | 0.6613 | 9.4% better |
| cross-track | 0.5185 | 0.4946 | 4.6% better |
| velocity err | 0.7954 | 0.9339 | 17.4% worse |
| done | 0.00391 | 0.00586 | worse |
| balanced | -8.3369 | -8.6649 | worse |

Against v62d_008 30M under the same velocity-contrast profile:

| metric | v62d_008 30M | v62d_010 5M | result |
|---|---:|---:|---|
| balanced | -7.8122 | -8.6649 | worse |
| position err | 0.7943 | 0.6613 | better |
| cross-track | 0.5449 | 0.4946 | better |
| velocity err | 0.5708 | 0.9339 | much worse |
| done | 0.00219 | 0.00586 | worse |

The `30M/final` checkpoint has the best velocity inside v62d_010:

```text
command_velocity_error = 0.6061
```

But it fails the promotion shape because:

```text
position error = 0.9581
cross-track error = 0.7451
balanced score = -9.9886
```

The intended combination did not land. Early checkpoints restore some spatial
discipline but lose velocity obedience; late checkpoints recover velocity only
by losing spatial tracking.

## tracker_wandb_ppo

Verdict:

```text
reject / hold v62d_010 as-is
```

Action path health is good:

```text
train/all_finite = 1.0
rollout_action_clip_fraction = 0.0
rollout_action_any_dim_clipped_fraction = 0.0
rollout_action_logprob_env_consistency_error ~= 3.25e-7
best-checkpoint action clipping/logprob/std verdicts = ok
```

W&B and throughput are healthy:

```text
run id: v62d_010_velocity_contrast_cross_track_guard_30m_20260627
url: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_010_velocity_contrast_cross_track_guard_30m_20260627
steady-state speed: about 1.273M env steps/s
```

PPO update pressure is acceptable but critic quality remains weak:

```text
approx_kl = 0.00743
clip_fraction = 0.107
explained_variance = 0.000058
value_loss = 1389.91
returns mean/std = -304.87 / 48.62
values mean/std = -284.35 / 0.0043
```

The critic is nearly state-constant against large return variance. This does
not invalidate the run, but it remains a repeated v62d training-health issue.

PPO plumbing is trustworthy enough to believe the negative result. The blocker
is not W&B or the tanh action path; it is the reward/generator/value-learning
tradeoff failing to produce one checkpoint that is both spatially accurate and
velocity-obedient.

## tracker_structure_research

Finding:

```text
do not promote v62d_010 and do not continue it as-is
```

v62d_010 tested:

```text
command_generator_profile=velocity_contrast_constant_speed
trajectory_cross_track_coef=1.8
```

Support passed. The candidate stayed inside the clean tracker lane:

```text
level3_reference_tracker_command_v3
tanh_squashed_gaussian
no gate/aperture/obstacle/race/finish/stage reward
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
```

It did not solve the v62d velocity/spatial tradeoff:

| checkpoint | position | cross-track | velocity | verdict |
|---|---:|---:|---:|---|
| v62c 7M baseline | 0.6573 | 0.5214 | 0.7397 | frontier |
| v62d_010 5M | 0.6613 | 0.4946 | 0.9339 | spatial ok, velocity collapses |
| v62d_010 30M/final | 0.9581 | 0.7451 | 0.6061 | velocity improves, spatial collapses |

Next required action:

```text
write a 10-candidate v62d meta-review before v62d_011
```

That meta-review should compare `v62c 7M` plus `v62d_001` through
`v62d_010`, especially the per-command failures in `v62d_008`, `v62d_009`, and
`v62d_010`. It should decide whether the next single knob should be a more
command-conditioned fix instead of another global coefficient or generator
contraction.
