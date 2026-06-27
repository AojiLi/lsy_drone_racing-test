# v62b Brax PPO Signal Audit

Date: 2026-06-27

## Purpose

Before changing the v60/v62 tracker reward again, audit the PPO learning signal
for the Brax/JAX lane:

```text
v62_brax_reference_command_tracker
```

This audit answers four questions:

1. Is action sampling consistent with the log-prob used by PPO?
2. Are advantages numerically reasonable?
3. Is reward scale reasonable?
4. Is the initial action standard deviation too large?

This is not a tracker-stage pass and not a Level3 hard eval.

## Command

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26221 \
  --num-envs 1024 \
  --num-steps 32 \
  --initial-log-std-values=-0.5,-1.0,-1.5,-2.0 \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_brax_ppo_signal_audit.json \
  --jax-device gpu
```

Audit JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62b_brax_ppo_signal_audit.json
```

That JSON is a generated metric artifact and remains ignored by git.

## Results

| Scenario | Verdicts | Std | Dim clip frac | Any-action clip frac | Raw vs clipped logprob abs mean | Advantage mean | Advantage std | Reward mean | Reward abs p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| initial log std -0.5 | action bad, advantage large, std too large, reward large | 0.6065 | 0.0999 | 0.3434 | 0.3427 | -36.4119 | 33.9009 | -3.2125 | 4.4583 |
| initial log std -1.0 | action ok, advantage large, std too large, reward ok | 0.3679 | 0.00735 | 0.0291 | 0.0274 | -28.3632 | 17.7455 | -2.6261 | 3.8679 |
| initial log std -1.5 | action ok, advantage large, std ok, reward ok | 0.2231 | 0.000008 | 0.000031 | 0.000048 | -25.6484 | 9.6552 | -2.4246 | 3.5353 |
| initial log std -2.0 | all ok | 0.1353 | 0.0 | 0.0 | 0.0 | -24.8073 | 9.4315 | -2.3574 | 3.3620 |
| v62 final checkpoint step 1048576 | action bad, advantage large, std too large, reward ok | 0.6110 | 0.1200 | 0.4012 | 0.3968 | -25.6474 | 11.5374 | -2.5044 | 4.1520 |

## Answers

### Action Sampling And Logprob

Not healthy at the default setting and not healthy in the v62 final checkpoint.

At default `initial_log_std=-0.5`, about `34.34%` of environment actions have
at least one clipped dimension. PPO currently records/logprobs the raw Gaussian
sample, while the environment receives the clipped action. The mean absolute
difference between raw-sample logprob and clipped-action proxy logprob is
`0.3427`.

The final v62 checkpoint is worse: about `40.12%` of actions have at least one
clipped dimension, and the logprob mismatch mean is `0.3968`.

This means PPO is often optimizing a probability for an action that is not the
action actually applied to the environment.

### Advantage

Not healthy at the default setting.

At default `initial_log_std=-0.5`, raw advantages had mean `-36.41` and std
`33.90`. The final v62 checkpoint still had advantage mean `-25.65` and std
`11.54`.

Lower exploration improves this. With `initial_log_std=-2.0`, advantage mean is
`-24.81` and std is `9.43`, which passes the audit threshold.

### Reward Scale

Borderline at the default setting, acceptable after reducing exploration.

At default `initial_log_std=-0.5`, reward mean was `-3.21`, which triggers the
audit's large-scale warning. At `initial_log_std=-2.0`, reward mean improves to
`-2.36` and reward abs p95 is `3.36`.

This suggests some of the reward-scale problem is caused by oversized
exploration actions rather than only by reward coefficients.

### Initial Std

Too large.

The default `initial_log_std=-0.5` means std about `0.6065` in normalized action
space. That is too high for a bounded action path that clips to `[-1, 1]`.
`initial_log_std=-1.5` almost eliminates clipping, and `initial_log_std=-2.0`
eliminates clipping in this audit.

## Conclusion

Do not tune the tracker reward yet.

The current failure is more likely a PPO signal problem than a reward-number
problem:

```text
large exploration std
-> frequent clipped env actions
-> stored logprob does not match applied action
-> noisy or misleading PPO update
-> deterministic eval gets worse after 1M
```

The next v62b step should keep the clean no-gate tracker reward unchanged and
fix PPO semantics first:

1. run the next bounded 1M test with `initial_log_std=-2.0`;
2. lower or zero `ent_coef` unless a decision packet justifies otherwise;
3. strongly consider a squashed-action or clipped-action-consistent logprob path;
4. keep reward coefficients unchanged until the four audit checks are healthy;
5. repeat deterministic pre/post eval before any 8M+ maturation.

## Boundaries

- `config/level3.toml` was not modified.
- No gate/aperture/race/finish/stage reward is recommended.
- No gate/obstacle/planner-phase actor input is recommended.
- SBX remains rejected for speed; the active fast backend remains Brax/JAX.
