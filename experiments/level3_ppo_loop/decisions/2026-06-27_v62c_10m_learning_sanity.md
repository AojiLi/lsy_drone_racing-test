# Decision: v62c 10M Passed Learning Sanity, Hold Before Long Maturation

Date: 2026-06-27

## Decision

```text
continue_same_hypothesis
```

Continue the Brax/JAX clean reference-command tracker lane with
`tanh_squashed_gaussian`, but do not start 60M+ maturation yet.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62c_tanh_squashed_gaussian_10m_analysis.md
```

The bounded 10M run produced learning signal:

- reward mean improved `-4.6670 -> -3.0376`;
- command position error improved `0.4990 -> 0.4440`;
- cross-track error improved `0.4116 -> 0.3254`;
- done mean improved `0.0064 -> 0.0`;
- `has_eval_learning_signal=true`.

The PPO action path stayed clean:

- `action_distribution=tanh_squashed_gaussian`;
- `action_logprob_mode=tanh_squashed_gaussian_logprob_with_jacobian`;
- final training-batch action clip fraction `0.0`;
- final training-batch logprob/env consistency error about `3.15e-7`;
- final checkpoint audit stored-vs-env logprob abs mean about `3.18e-7`;
- final checkpoint audit verdicts: action/logprob/std/reward/advantage all ok.

Speed stayed good:

- steady-state `~1.305M env steps/s`;
- about `32.79x` the PyTorch fast path.

## Interpretation

This substantially lowers the probability that "JAX itself" or the
tanh-squashed action path is the current blocker. The JAX trainer can learn on
the command tracker task.

Remaining blockers are tracker-training quality issues:

- command velocity error worsened `0.6070 -> 0.7457`;
- action magnitude and action delta increased;
- train-batch value loss was still high at `1766.03`;
- train-batch advantage mean/std was still large at `-41.87 / 42.29`;
- milestone checkpoints have not yet been ranked.

## Next Action

Run:

```text
v62c_milestone_value_velocity_review
```

Required checks:

1. evaluate saved `1M-9M` v62c milestone checkpoints plus final;
2. choose the best checkpoint by command position error, cross-track error,
   command velocity error, done rate, and action smoothness;
3. inspect W&B curves for value loss, raw advantage scale, clip fraction,
   entropy/std, velocity error, and reward;
4. decide whether to:
   - continue v62c longer;
   - add value/return normalization or critic target scaling;
   - tune command velocity reward;
   - run fixed-policy parity only if milestone evidence contradicts the current
     learning-sanity result.

## Guardrails

- Do not add gate/aperture/race/finish/stage reward.
- Do not add gate/obstacle/planner-phase actor inputs.
- Do not modify `config/level3.toml`.
- Do not approve planner integration or 60M+ maturation until milestone review
  clarifies the velocity/value issue.
