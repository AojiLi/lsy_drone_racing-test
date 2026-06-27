# v62d_009 Subagent Reviews

Date: 2026-06-27

Candidate:

```text
v62d_009_velocity_contrast_spatial_guarded_generator_30m
```

## tracker_eval_metrics

Recommendation:

```text
do not promote v62d_009
```

Best v62d_009 milestone is `15M`:

```text
lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_generator_30m/v62d_009_velocity_contrast_spatial_guarded_generator_30m_step_015000000.pkl
```

Against v62c 7M baseline:

| metric | v62c 7M | v62d_009 15M | result |
|---|---:|---:|---|
| reward | -4.8459 | -4.8927 | slightly worse |
| position err | 0.6573 | 0.6570 | flat / slightly better |
| cross-track | 0.5214 | 0.4833 | 7.3% better |
| velocity err | 0.7397 | 0.7811 | 5.6% worse |
| done | 0.00391 | 0.00391 | flat |
| action delta | 0.000006 | 0.000012 | about 2x, still tiny |
| balanced | -7.5365 | -7.5566 | slightly worse |

Promotion threshold fails on the main gate: velocity needed to improve by
`10%-15%`, but the best balanced checkpoint worsens velocity. The best velocity
checkpoint, `30M`, improves velocity versus v62c by only about `5.1%` and badly
regresses position/cross-track, so it also fails.

Compared with v62d_008 best `30M`, v62d_009 `15M` restores spatial discipline
but loses the velocity breakthrough: velocity is `36.8%` worse than v62d_008,
while position and cross-track improve.

Audit: selected checkpoint action path looks ok: no clipping, stored-vs-env
logprob abs mean about `3.18e-7`, action sampling/logprob/std/reward/advantage
verdicts ok for the checkpoint. No audit blocker, but metrics do not clear
promotion.

## tracker_wandb_ppo

Verdict:

```text
do not promote v62d_009 and do not continue it as-is to 60M
```

PPO plumbing is clean enough to trust the run as evidence, but the learned
policy is not healthy enough to promote. Best balanced point is `15M`, then the
run drifts/collapses, and the final checkpoint only recovers some velocity by
sacrificing spatial tracking.

Findings:

- Action/logprob path is healthy: tanh-squashed Gaussian, clipping `0.0`,
  stored-vs-env logprob error about `3.2e-7`, all finite.
- PPO update pressure is mostly moderate but not perfectly calm: final KL
  `0.0033`, clip fraction `0.0375`; late spikes hit KL around `0.033` and clip
  fraction around `0.315` between roughly `21M-28M`.
- Critic remains weak: final explained variance is about `5.45e-5`; values are
  nearly state-constant (`values_std ~0.0025`) while targets are large
  (`-311.9 +/- 41.1`).
- Entropy/std did not explode. Entropy decreased from about `-2.33` to `-2.78`;
  best audit checkpoint has log std mean about `-2.045` and std about `0.129`.
- Milestones show late collapse: `15M` is best balanced, `20M-25M` degrade
  badly, and `30M/final` still has poor spatial tracking.
- The summary's `has_eval_learning_signal=true` is too weak for promotion:
  final eval worsens reward, position, velocity, cross-track, and action
  magnitude versus initial; only done rate improves trivially.

Next action: reject same-hypothesis continuation, keep `15M` only as a
diagnostic checkpoint, and require a changed follow-up focused on critic/value
stability plus preserving velocity contrast without spatial drift.

## tracker_structure_research

Finding:

```text
reject v62d_009 for promotion
```

Its best balanced checkpoint is `15M`: position is basically tied with v62c 7M,
cross-track improves, but velocity worsens (`0.7811` vs `0.7397`) and balanced
score is slightly worse (`-7.5566` vs `-7.5365`).

The `30M/final` checkpoint gets only a small velocity gain (`0.7021`, about
`5.1%` better than v62c 7M), below the `10%-15%` bar, while position and
cross-track collapse by roughly `39%-41%`. That violates the v62d promotion
guardrail.

Structurally, the spatial guard did not combine cleanly with velocity contrast.
It either restores spatial tracking and loses velocity, or keeps some velocity
and loses spatial tracking. Action/logprob plumbing is clean, so this does not
look like an action-distribution bug. The critic remains suspiciously weak:
final explained variance is near zero, values are nearly state-constant, and
value loss/return scale remain high.

Recommendation:

```text
hold / meta-review, not another immediate 30M candidate
```

Concrete next step: write the v62d_009 decision as `rejected_not_promoted`, keep
`v62c 7M` as the frontier, and run a short v62d meta-review focused on whether
the next real knob should be critic/value normalization or a staged generator
curriculum. Do not continue generator-only tuning, reward-number tuning, or PPO
rollout tweaks until that review compares v62d_008/v62d_009 per-command
failures and critic diagnostics.
