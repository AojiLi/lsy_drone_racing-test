# Level3 PPO Stage 2 Proposal: Observation/Event Parity Diagnostic

## Scope

This is a diagnostic-only Stage 2 packet.

It does not approve a train/eval chunk. It does not approve reward,
observation, PPO, network, environment, curriculum, or training-structure
changes.

## Current Status

The target is still unmet:

- Required: `success_rate >= 0.60`
- Required: `mean_time_s_success <= 7.0s`
- Current global best:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Current global-best hard eval:
  `success_rate=0.0`, `crash_rate=1.0`, `mean_gates=0.85`,
  `mean_time_s_success=null`

Stage 1 reward-only search is exhausted. The Stage 2 `sensor_range=1.5`
staging probe did not improve hard-eval performance and is rolled back.

## Why This Diagnostic

The previous Stage 2 parity check showed that `ppo_level2_inference` and
`ppo_level3_inference` produce identical rollout outcomes for the incumbent
checkpoint when the same checkpoint is injected.

That closes the controller-module path, but it does not yet prove:

- training `RaceObservation` and inference `_obs_rl` produce identical flat
  vectors on the same raw observations;
- reward wrapper event counters align with hard evaluator gate-passing
  semantics;
- shaped front/back/missed/wrong-side events are not hiding a geometry
  mismatch around the gate plane.

Because repeated W&B curves show no finish conversion and hard eval remains at
`0%` success, this diagnostic should run before another train/eval chunk.

## Approved Diagnostic

Add and run a read-only script:

```text
scripts/check_level3_observation_event_parity.py
```

Required command:

```text
pixi run -e gpu python scripts/check_level3_observation_event_parity.py \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt \
  --seed-start 1 \
  --num-seeds 20 \
  --max-steps 300 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001
```

The script must:

- compare training `RaceObservation._flatten_observations` against inference
  `ppo_level3_inference.PPOLevel2Inference._obs_rl` on identical raw reset and
  rollout observations;
- preserve each side's own history and last-action state while stepping a
  deterministic policy trajectory;
- record section-level observation diffs using the training layout slices;
- compare reward `passed_gate_rate` with hard environment `target_gate`
  transitions on the same rollout;
- record front, pass, back, missed, wrong-side, crash, finish, and timeout
  event counters;
- run a small synthetic gate-plane threshold grid to expose any difference
  between the hard gate box and shaped radius thresholds.

## Acceptance

Accept this diagnostic as closed only if artifacts are written:

- `<out-prefix>_observation_rows.csv`
- `<out-prefix>_event_rows.csv`
- `<out-prefix>_summary.json`

The diagnostic is considered clean only if:

- training and inference observation dimensions match;
- maximum observation diff is within the configured tolerance;
- reward `passed_gate_rate` has zero mismatches versus hard `target_gate`
  changes;
- finish and timeout labels have zero mismatches.

If the diagnostic is not clean, hold and write a focused fix proposal before
training.

If the diagnostic is clean but the synthetic threshold grid exposes meaningful
shaping/hard-gate mismatch, hold and write a separate proposal that either
explains why the mismatch is harmless or proposes one narrow reward-geometry
fix for user approval.

If the diagnostic is clean and no actionable mismatch appears, the next packet
should move to a narrow first-gate learnability intervention, still with hard
evaluation on the original `config/level3_dr.toml`.

## Not Approved

This packet does not approve:

- another train/eval chunk;
- changing active reward coefficients;
- enabling disabled reward channels;
- changing observation layout;
- changing PPO hyperparameters;
- changing the model architecture;
- changing hard evaluation config;
- continuing from the failed `level3_loop_008_stage2_gate0_sensor15_probe`
  checkpoint.
