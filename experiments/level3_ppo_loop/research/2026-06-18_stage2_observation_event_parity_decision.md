# Level3 PPO Stage 2 Decision: Observation/Event Parity Fixed

## Scope

This is a post-diagnostic Stage 2 decision report. It records one inference
bug fix and refreshed hard-eval evidence.

It does not approve a new train/eval chunk.

## Finding

The observation/event parity diagnostic found a real inference bug.

Before fix:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_before_fix_summary.json`
- Observation dimensions: `103` vs `103`
- Observation max abs diff: `0.4680071473121643`
- Observation failures: `1666 / 1675`
- Worst section: `rotmat`
- Event passed-gate mismatches: `0`
- Finish mismatches: `0`
- Timeout mismatches: `0`

Root cause:

- `ppo_level2_inference._obstacle_heading_xy` and
  `ppo_level3_inference._obstacle_heading_xy` normalized a NumPy view into
  `rot[:2, 0]` in place.
- That mutated `rot` before `_obs_rl` appended `rot.reshape(-1)`.
- Training `RaceObservation` uses JAX arrays and did not mutate the rotation
  matrix.

Fix:

- `lsy_drone_racing/control/ppo_level2_inference.py`
- `lsy_drone_racing/control/ppo_level3_inference.py`

The heading vector is now copied before normalization.

## Verification

After-fix diagnostic:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_after_fix_summary.json`
- Observation dimensions: `103` vs `103`
- Observation max abs diff: `4.76837158203125e-7`
- Observation failures: `0`
- `rotmat` max diff: `0.0`
- Event passed-gate mismatches: `0`
- Finish mismatches: `0`
- Timeout mismatches: `0`
- Summary clean: `true`

This closes the observation/event parity bug for the incumbent checkpoint path.

## Refreshed Hard Eval

Because previous evaluator metrics used the old inference observation, existing
best metrics were stale.

Refreshed incumbent eval:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_incumbent_001_after_inference_rotmat_fix_summary.csv`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Inference module: `ppo_level3_inference`
- Success: `0.0`
- Crash: `1.0`
- Mean gates: `0.6`
- Mean successful time: `null`

Representative prior-best refresh:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_representative_bests_after_inference_rotmat_fix_summary.csv`
- Best representative: `level3_loop_004_gate_acquisition_safety:30M`
- Success: `0.0`
- Crash: `1.0`
- Mean gates: `0.9`
- Mean successful time: `null`

All-checkpoint 10-seed screen:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_all_checkpoints_after_inference_rotmat_fix_10seed_summary.csv`
- All screened checkpoints remained at `0.0` success.
- The strongest candidates were still in the `level3_loop_004` family.

Top candidate 20-seed refresh:

- Artifact:
  `experiments/level3_ppo_loop/diagnostics/level3_top_screen_candidates_after_inference_rotmat_fix_summary.csv`
- `level3_loop_004_gate_acquisition_safety:55M`:
  `success=0.0`, `crash=1.0`, `mean_gates=0.85`
- `level3_loop_004_gate_acquisition_safety:70M`:
  `success=0.0`, `crash=1.0`, `mean_gates=0.9`

Decision:

- Refresh loop best to
  `lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt`.
- Its fixed-inference 20-seed score is `-71.4`.
- It is not a target success; it is only the current best search ordering point.

## Remaining Diagnostic Signal

The synthetic gate-plane threshold grid still shows shaped geometry thresholds
are not identical to the hard gate box:

- hard gate half width: `0.225m`
- reward stage radius: `0.24m`
- reward missed radius: `0.25m`
- hard-pass points outside stage radius: `1141 / 19881`
- stage-radius points outside hard box: `250 / 19881`
- hard-fail points not missed by reward radius: `578 / 19881`

This is not the same as a `passed_gate` mismatch. The actual rollout event
diagnostic found `0` hard/reward passed-gate mismatches. But the shaping
geometry mismatch remains a plausible next narrow Stage 2 packet if training
continues to fail at gate acquisition.

## Next Action

Do not restart reward-only Stage 1.

Do not continue from the failed `008` sensor-range checkpoint.

The next useful work is one of:

- run crash taxonomy on the refreshed fixed-inference best `004:30M`; or
- write a narrow Stage 2 reward-geometry packet focused only on aligning shaped
  front/back/missed radii with the hard gate box, without changing algorithm,
  observation layout, network, PPO hyperparameters, or environment.

No new training should start until that next packet is written.
