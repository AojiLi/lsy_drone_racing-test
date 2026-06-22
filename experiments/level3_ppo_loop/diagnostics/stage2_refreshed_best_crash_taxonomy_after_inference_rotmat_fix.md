# Level3 PPO Stage 2 Diagnostic: Refreshed-Best Crash Taxonomy After Inference Fix

## Scope

This is a diagnostic report only. It does not approve another training run.

## Inputs

Checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt
```

Reason:

- After the inference rotmat parity fix, this checkpoint is the refreshed
  20-seed best among representative candidates:
  `success_rate=0.0`, `crash_rate=1.0`, `mean_gates=0.9`,
  `score=-71.4`.

Command:

```text
pixi run -e gpu python scripts/analyze_level2_ppo_crashes.py \
  --mode single \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt \
  --inference-module ppo_level3_inference \
  --seed-start 1 \
  --num-seeds 40 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_004_30M_after_inference_rotmat_fix_crash_taxonomy
```

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_004_30M_after_inference_rotmat_fix_crash_taxonomy_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_004_30M_after_inference_rotmat_fix_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_004_30M_after_inference_rotmat_fix_crash_taxonomy_hotspots.png`

## Result

- Episodes: `40`
- Successes: `0`
- Crashes: `40`
- Timeouts: `0`

Crashes by target gate:

- gate `0`: `17`
- gate `1`: `15`
- gate `2`: `8`

Top likely crash objects:

- `gate_0_top`: `9`
- `obstacle_0`: `6`
- `gate_0_left`: `3`
- `obstacle_1`: `3`
- `gate_0_right`: `2`
- `gate_1_left`: `2`
- `gate_1_top`: `2`
- `gate_2_top`: `2`
- `obstacle_2`: `2`

Nearest gate part counts:

- `top`: `14`
- `stand`: `9`
- `left`: `7`
- `right`: `6`
- `bottom`: `4`

## Interpretation

The refreshed best can pass more gates than the old incumbent under corrected
inference, but it still has no success conversion and still crashes every
episode.

Failure is not only a first-gate reset issue:

- `17 / 40` crashes happen while still targeting gate `0`.
- `15 / 40` happen while targeting gate `1`.
- `8 / 40` happen while targeting gate `2`.

The object distribution points toward edge/clearance geometry rather than pure
PPO instability:

- gate-frame parts dominate, especially `top`;
- obstacle collisions remain meaningful, especially `obstacle_0`;
- the prior observation/event parity diagnostic is now clean, so this is no
  longer explained by an inference `rotmat` mismatch.

The synthetic threshold grid in the parity report remains relevant:

- hard gate pass uses a box half width of `0.225m`;
- shaped front/back/missed events use circular radii around `0.24m`/`0.25m`;
- this can create shaping disagreement near gate corners and edges even though
  the hard `passed_gate` event itself is aligned.

## Decision

Hold training.

The next packet should be a narrow Stage 2 reward-geometry proposal. It should
not change observation layout, algorithm, PPO hyperparameters, network,
environment, or curriculum. It should focus only on whether existing shaped
gate-front/gate-back/missed/wrong-side geometry should be aligned to the hard
gate box used by `gate_passed`.

No train/eval chunk should start until that packet is written.
