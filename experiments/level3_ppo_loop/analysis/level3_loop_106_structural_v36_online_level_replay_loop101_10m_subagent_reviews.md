# Subagent Reviews: loop106 v36 Online Level Replay

Trial:
`level3_loop_106_structural_v36_online_level_replay_loop101_10m`

Analysis:
`experiments/level3_ppo_loop/analysis/level3_loop_106_structural_v36_online_level_replay_loop101_10m_analysis.md`

## Evaluator Metrics

Decision: reject v36.

Best loop106 checkpoint was the 1M checkpoint:

- success: `20%`
- mean gates: `1.63`
- crash rate: `80%`
- mean successful time: `7.744s`

It only tied loop101 on success and crash, while underperforming loop101 on
mean gates and successful time. Later checkpoints collapsed: final reached only
`14%` success, `1.41` mean gates, and `86%` crash.

The v36 promotion gate was not met: no checkpoint reached `>20%` success, and
no checkpoint reached `>1.69` mean gates with crash `<=80%`. Failures were all
contact / bounds-or-ground, concentrated around target gate 0 and target gate 2.

## W&B / PPO Diagnostics

Decision: reject v36 and do not tune replay probability further.

The training run did not show PPO instability:

- approximate KL stayed well below `target_kl=0.03`
- clip fraction stayed near zero
- entropy remained stable
- explained variance stayed around the `0.71-0.74` range
- value loss did not explode

The training issue is conversion, not optimizer blow-up. Online level replay
did not meaningfully open: replay probability rose only from `0.03` to `0.04`,
and both the online replay and gate-phase reset competence gates remained
closed. Race passed-gate and finished rates stayed below the thresholds needed
to increase the curriculum pressure. Hard eval then degraded after the 1M
checkpoint, so training reward movement did not convert into validation-unseen
progress.

## Structure / Research Synthesis

Decision: reject v36 and launch a new named structural lane:
`v37_gru_transfer_memory_structure_from_loop101`.

Do not repeat the old from-scratch GRU lane. The next GRU attempt must be a
transfer / memory-structure packet starting from loop101 final, with explicit
support for MLP-to-GRU initialization, hidden-state reset checks,
zero-update/parity checks where meaningful, sequence rollout/BPTT validation,
and unchanged hard eval on `config/level3.toml`.

Priority order after loop106:

1. Build and verify the GRU transfer / memory-structure lane from loop101.
2. Do not continue v36 or tune replay probability.
3. Keep reward-number changes as a later fallback after the memory lane is
   tested.
4. Do not modify Level3 track geometry or randomization.
