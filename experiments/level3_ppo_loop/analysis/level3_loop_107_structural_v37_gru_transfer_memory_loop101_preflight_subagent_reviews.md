# Subagent Reviews: loop107 v37 Residual-GRU Transfer

Trial:
`level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight`

## Evaluator Metrics

Recommendation: modify v37, do not continue it as-is.

- Best checkpoint is `1M`: `21%` success, `1.66` mean gates,
  `7.578s` mean successful time, `79%` crash, `0%` timeout.
- This is a narrow success/crash improvement over loop101, but worse than
  loop101 on mean gates and successful time.
- Later checkpoints degrade: `2M` to `15%`, `3M/4M` to `12%`, final to `17%`.
- v37 has a small early signal, but training past that point damages hard-eval
  performance.

## W&B / PPO Diagnostics

Recommendation: continue v37 only as cautious maturation from the `1M`
checkpoint with milestone evals.

- PPO does not look unstable: approximate KL falls to about `0.0002`,
  clip fraction ends at `0`, entropy stays high and stable around `4.34`.
- Critic does not explode: value loss drops and explained variance rises to
  about `0.77`.
- Reward conversion is mixed: some gate-acquisition signals nudge upward, but
  finished rate falls and later hard-eval checkpoints do not beat `1M`.
- Teacher-retention/distillation is inactive.

## Structure / Research Synthesis

Recommendation: keep v37 alive only by maturing the `1M` checkpoint.

- Do not continue from the final checkpoint.
- Do not tune reward numbers as the immediate next step.
- Do not change `config/level3.toml` geometry or randomization.
- The next step should evaluate dense early milestones and keep checkpoint
  selection milestone-aware.
- If the `1M` maturation fails to reproduce or improve the `21%` / `1.66`
  frontier and remains contact-dominated, move to a named
  retention/distillation GRU lane rather than blindly continuing v37.

## Main-Agent Synthesis

Decision: `continue_same_hypothesis`, implemented as the named follow-up lane
`v37b_residual_gru_maturation_from_loop107_1m`.

Rationale:

- v37 is not a breakthrough and must not be matured to 30M/60M as-is.
- The `1M` checkpoint is the only useful signal, and it is also the current
  best success-rate checkpoint in the corrected Level3 loop state.
- The failure pattern is early benefit followed by forgetting/drift, not PPO
  explosion.
- A short continuation from `1M` with dense milestone evaluation is the
  smallest useful test before escalating to retention/distillation.
