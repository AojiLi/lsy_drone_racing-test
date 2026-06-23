# Loop102 Subagent Reviews: Reject v34 Offline PLR

Trial:
`level3_loop_102_structural_v34_lowprob_train_pool_plr_loop101_10m`

Decision context: loop102 tested v34 low-probability train-pool bounds/ground
seed replay from loop101 final, with unchanged deployed v5 Actor observation,
unchanged reward/PPO numbers, unchanged hard eval on `config/level3.toml`, and
v33 gate-phase reset curriculum still enabled.

## Evaluator Metrics

Recommendation: stop v34 offline PLR as-is.

- Best loop102 checkpoint was `1M`: `17/100` success, `1.59` mean gates,
  `83/100` crash, `7.593s` mean successful time.
- The `8M` checkpoint tied the same success/mean-gate/crash level but was
  slower at `7.665s`.
- The final checkpoint regressed to `10/100` success, `1.43` mean gates, and
  `90/100` crash.
- This fails the v34 promotion gate because loop101 remains better at
  `20/100` success, `1.69` mean gates, `80/100` crash, and `6.873s`.
- Failure mode is still dominated by contact/bounds-or-ground; timeout remains
  `0`.

## W&B/PPO Diagnostics

Recommendation: do not continue v34 and do not apply the analyzer's generic
reward-number patch as the next move.

- PPO did not explode: KL, clip fraction, entropy, and explained variance were
  stable.
- Training signals did not convert into hard-eval progress.
- Train reward/total reward fell and value loss rose, consistent with stable
  but ineffective updates plus mild negative transfer from the v34 training
  distribution.
- Next run should start from loop101 final, not from any loop102 checkpoint.

## Structure/Research Synthesis

Recommendation: launch a named competence-gated curriculum lane before GRU or
reward-number tuning.

- v34's only substantive change was static 8% offline replay, and it regressed
  validation-unseen hard eval.
- The next lane should keep v5 Actor observation, reward numbers, PPO numbers,
  rollout geometry, and `config/level3.toml` hard eval fixed.
- Add competence gating around gate-phase reset exposure: begin below the v33
  `0.45` reset probability and increase only when rollout pass/finish/crash
  signals are healthy.

## Main-Agent Synthesis

Decision: reject v34 as-is and launch
`v35_competence_gated_gate_phase_curriculum_from_loop101`.

The next experiment should explicitly test whether gradual gate-phase reset
pressure preserves loop101's 20% frontier while improving gate progress. It
must not change Level3 track geometry, validation seeds, Actor observation,
reward numbers, PPO hyperparameters, or inference-time controller structure.
