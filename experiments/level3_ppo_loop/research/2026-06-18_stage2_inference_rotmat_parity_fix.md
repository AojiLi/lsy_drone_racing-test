# Level3 PPO Stage 2 Fix Packet: Inference Rotmat Parity

## Scope

This packet approves one narrow inference bug fix and no training.

It does not approve reward changes, observation-layout changes, PPO
hyperparameter changes, network changes, environment changes, curriculum
changes, or another train/eval chunk.

## Evidence

Diagnostic command:

```text
pixi run -e gpu python scripts/check_level3_observation_event_parity.py \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt \
  --seed-start 1 \
  --num-seeds 20 \
  --max-steps 300 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_before_fix
```

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_before_fix_observation_rows.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_before_fix_event_rows.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_before_fix_summary.json`

Result:

- Observation dimensions matched: `103` vs `103`
- Controller layout: `obstacle_heading_xy_v1`
- `controller_include_prev_gate=true`
- Observation max abs diff: `0.4680071473121643`
- Observation failures: `1666 / 1675`
- Worst section: `rotmat`
- Event passed-gate mismatches: `0`
- Finish mismatches: `0`
- Timeout mismatches: `0`

## Root Cause

The inference `_obstacle_heading_xy` implementation takes a NumPy view into
`rot[:2, 0]`:

```python
heading_forward = np.asarray(rot[:2, 0], dtype=np.float32)
heading_forward /= max(float(np.linalg.norm(heading_forward)), 1e-6)
```

Because this is a view, the in-place `/=` mutates the original `rot` matrix
before `_obs_rl` appends `rot.reshape(-1)` to the flat observation.

The training `RaceObservation` path uses JAX arrays. Its analogous operation
does not mutate the original `rot` tensor. Therefore inference sends the policy
a normalized-XY first rotation column while training sends the full body-to-world
rotation matrix.

## Approved Fix

Change both inference modules to copy the heading vector before normalization:

- `lsy_drone_racing/control/ppo_level2_inference.py`
- `lsy_drone_racing/control/ppo_level3_inference.py`

No other semantics are approved.

## Required Verification

After the fix:

```text
pixi run -e gpu python scripts/check_level3_observation_event_parity.py \
  --config level3_dr.toml \
  --checkpoint lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt \
  --seed-start 1 \
  --num-seeds 20 \
  --max-steps 300 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_001_after_fix
```

Then re-evaluate the incumbent checkpoint because all previous hard-eval metrics
used the old inference observation:

```text
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3_dr.toml \
  --seed-start 1 \
  --num-seeds 20 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_incumbent_001_after_inference_rotmat_fix \
  lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Acceptance:

- observation/event parity summary is clean;
- incumbent hard-eval metrics are refreshed under fixed inference;
- no new training starts until these artifacts are reviewed.
