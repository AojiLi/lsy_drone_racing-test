# v62d_003 Subagent Reviews

Date: 2026-06-27

## Reviewer 1: tracker_eval_metrics

Best v62d_003 milestone is `20M`:

```text
lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_step_020000000.pkl
```

It is best by balanced score, behavior score, and velocity within this
candidate: velocity error `0.7219`, position error `0.6381`, cross-track error
`0.5022`, done mean `0.003906`, balanced score `-7.7744`.

Promotion verdict: do not promote. The threshold requires velocity improvement
of `10%-15%` versus v62c 7M with no material action-delta worsening. v62d_003
20M improves velocity by only `2.41%` versus v62c 7M
(`0.7397 -> 0.7219`), while action delta is `7.89x` worse
(`6.39e-06 -> 5.04e-05`).

Key tradeoffs:

- `20M` is the only decent candidate point: position improves `2.92%`,
  cross-track improves `3.68%`, done mean is unchanged, but reward is worse
  (`-4.8459 -> -5.1643`) and balanced score is worse
  (`-7.5365 -> -7.7744`).
- `10M` has best position/cross-track (`0.6111`, `0.4951`) but velocity
  collapses badly (`0.9728`, `31.5%` worse) and done worsens to `0.005859`.
- `30M/final` shows late regression: position `0.7259`, cross-track `0.5798`,
  velocity `0.7510`, action delta `13.9x` worse than baseline.

Recommendation: reject, keep v62c 7M as the frontier, and do not run 60M+
maturation from v62d_003.

## Reviewer 2: tracker_wandb_ppo

Action path looks healthy, not the failure source:

```text
distribution: tanh_squashed_gaussian
logprob mode: tanh_squashed_gaussian_logprob_with_jacobian
final train action clipping: 0.0
final any-dim clipping: 0.0
final stored/env logprob consistency error: 3.13e-7
best-audit stored/env logprob abs mean: 3.10e-7
best-audit verdicts: action clipping ok, action sampling/logprob ok
```

Final PPO update is finite and not explosively unstable:

```text
approx_kl: 0.00333
clip_fraction: 0.02893
entropy: -2.7874
policy_loss: -0.000707
all_finite: 1.0
```

Reward scale is acceptable in the best audit, but critic/value pressure remains
unhealthy:

```text
final rollout reward mean: -6.0054
final returns mean/std: -305.49 / 27.08
final advantages mean/std: -20.94 / 27.08
final value loss: 583.43
final explained variance: 0.000065
final values mean/std: -284.55 / 0.00189

20M audit reward abs mean/p95: 2.835 / 3.590
20M audit advantage mean/std: -10.70 / 4.75
20M audit return mean/std: -201.56 / 4.75
20M audit value mean/std: -190.86 / 0.0030
```

Verdict: this does not look like PPO action/logprob math or update explosion.
The failure is mostly reward weighting plus generator/curriculum, with
critic/value pressure as a secondary blocker. Doubling velocity coefficient did
not buy meaningful velocity obedience.

## Reviewer 3: tracker_structure_research

Decision recommendation: switch to Family C generator velocity distribution.

Next candidate:

```text
v62d_004_speed_bin_balanced_generator
```

Keep PPO/reward otherwise v62c-style:

```text
action_distribution=tanh_squashed_gaussian
value_target_scale=1.0
num_minibatches=4
update_epochs=1
train from scratch
```

Revert the failed generic `vel_error_coef=1.2` unless a later decision
explicitly approves a combination.

Why: local evidence says Family B's blunt velocity-coef increase did not solve
velocity obedience. The best checkpoint only improves velocity
`0.7397 -> 0.7219`, about `2.4%`, far below the `10%-15%` promotion bar. The
run also worsens action delta and drifts after 20M.

Family C should target the data/curriculum side: rebalance the generator toward
clearer speed-bin training, with longer clean constant-speed and
low-speed-through segments, explicit brake-ramp exposure, recover-speed
transitions, and strict reference spacing consistent with `desired_speed * dt`.

Hard boundaries preserved:

```text
no gate/aperture/race reward
no gate/obstacle/planner-phase actor inputs
keep level3_reference_tracker_command_v3
leave config/level3.toml unchanged
```
