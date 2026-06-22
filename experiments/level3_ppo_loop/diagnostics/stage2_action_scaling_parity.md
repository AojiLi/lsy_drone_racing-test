# Level3 PPO Stage 2 Diagnostic: Action Scaling Parity

## Result

Clean. Training and inference action scaling match exactly for the refreshed
best checkpoint.

## Check

- Config: `config/level3_dr.toml`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt`
- Inference module: `ppo_level3_inference`
- Samples: `1000`
- Tolerance: `1e-6`
- Summary JSON:
  `experiments/level3_ppo_loop/diagnostics/level3_action_scaling_parity_004_30M.json`

## Evidence

All measured diffs were zero:

- `action_low_max_abs_diff = 0.0`
- `action_high_max_abs_diff = 0.0`
- `action_scale_max_abs_diff = 0.0`
- `action_mean_max_abs_diff = 0.0`
- `sample_scaled_max_abs_diff = 0.0`
- `sample_scaled_mean_abs_diff = 0.0`

## Decision

Action scaling is not the current Level3 failure source. Keep the global best
as `level3_loop_004_gate_acquisition_safety:30M` and continue Stage 2 structural
diagnosis before launching any new train/eval chunk.

The next most likely diagnostic branch is train/eval distribution pressure:
train-only robustness wrappers and domain-randomization settings may be making
full Level3 acquisition too hard before the policy has stable gate competence.
