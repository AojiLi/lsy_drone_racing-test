# loop103 Subagent Review Synthesis

Trial: `level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m`

## Evaluator Metrics

- loop103 did not beat the frontier. Best checkpoint was 9M:
  `19%` success, `1.68` mean gates, `81%` crash, `7.245s` mean successful time.
- Global best remains loop101 final:
  `20%` success, `1.69` mean gates, `80%` crash, `6.873s` mean successful time.
- Main failure mode is contact / bounds-or-ground. At 9M:
  `contact=81`, `finish=19`; failures concentrated at gate 0 and gate 2
  (`gate0=29`, `gate2=29`).
- Recommendation: reject v35 as-is; do not continue from loop103 final.

## W&B / PPO Diagnostics

- PPO did not obviously blow up. KL, clip fraction, explained variance, and
  value loss were stable enough to treat this as a conversion problem, not a
  training crash.
- v35 competence-gated reset never opened:
  `curriculum/gate_phase_reset_prob=0.12` and
  `curriculum/competence_gate_met=0` for the run.
- The pass-rate threshold was barely touched, but finish rate never cleared the
  v35 gate. This means v35 correctly refused to increase curriculum pressure.
- Recommendation: reject v35 as-is. If choosing only between MLP/v5 extension
  and GRU, prefer a memory/GRU packet over another unchanged MLP/v5 extension.

## Structure / Research Synthesis

- v34 showed static train-pool replay can cause negative transfer.
- v35 showed low fixed gate-phase reset exposure did not expand validation
  coverage and did not reach competence needed to increase pressure.
- Recommendation: launch a named online competence-gated level replay lane from
  loop101. Keep `config/level3.toml` unchanged, keep v5 Actor observation,
  MLP policy, reward numbers, PPO numbers, and rollout geometry fixed, and use
  train-pool-only replay seeds with competence-gated replay probability.

## Main-Agent Synthesis

Decision: reject v35 as-is and launch v36 online competence-gated level replay.

Rationale:

- Re-running static replay would repeat v34's failure mode.
- Re-running the old from-scratch GRU lane would repeat loop062, which reached
  `0%` success and `0.10` mean gates at best.
- v36 is the narrow next structural step: it starts from loop101 best and
  changes only training-time level sampling. If v36 fails the 10M screen, the
  next packet should move to a GRU transfer/memory-structure design rather than
  another replay-probability tweak.
