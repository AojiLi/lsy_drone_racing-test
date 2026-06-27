# Decision: Continue v62b After Positive 10M Signal, Do Not Tune Reward Yet

Date: 2026-06-27

## Decision

```text
continue_same_hypothesis
```

Continue the Brax/JAX clean reference-command tracker lane, but do not move to
reward tuning yet.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62b_brax_ppo_signal_fix_10m.md
```

The narrow v62b fix satisfied the intended PPO-signal requirements:

- `initial_log_std` is exposed and defaults to `-2.0`;
- `ent_coef` defaults to `0.0`;
- PPO stores/logprobs the env-executed bounded action;
- 10M training kept `rollout_action_clip_fraction=0.0`;
- 10M training kept `rollout_action_logprob_env_consistency_error=0.0`;
- final checkpoint audit had all PPO-signal verdicts ok.

The 10M deterministic eval had positive learning signal:

- reward mean improved `-4.1090 -> -2.7413`;
- command position error improved `0.5153 -> 0.4006`;
- cross-track error improved `0.4351 -> 0.2803`;
- done mean improved `0.00417 -> 0.0`;
- `has_eval_learning_signal=true`.

But the result is not complete:

- command velocity error worsened `0.5479 -> 0.6811`;
- action delta penalty worsened;
- final training batch still had advantage mean/std `-46.06 / 42.59`;
- final training batch value loss was `1962.39`.

## Next Action

Run a v62b milestone analysis before changing reward numbers:

```text
v62b_milestone_checkpoint_eval_and_value_scale_review
```

Required checks:

1. evaluate saved 1M-9M milestone checkpoints plus final with the same
   deterministic reference-command eval;
2. identify whether final is the best checkpoint or whether an earlier
   milestone has better velocity/smoothness;
3. inspect W&B curves for value loss, advantage scale, clip fraction, velocity
   error, and command position/cross-track error;
4. decide between:
   - continue same v62b settings longer;
   - add value/return normalization or critic-target scaling;
   - tune command reward only after PPO/value scale evidence is clean.

## Guardrails

- Do not add gate/aperture/race/finish/stage reward.
- Do not add gate/obstacle/planner-phase actor inputs to the clean tracker.
- Do not modify `config/level3.toml`.
- Keep checkpoint/metric JSON artifacts out of git.
- Do not promote this to planner integration until milestone eval and tracker
  stage gates justify it.
