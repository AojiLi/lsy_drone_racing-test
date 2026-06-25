# Decision: Launch Gate Aperture Phase-Completion Attempt002

## Decision

Launch named structural fix:

```text
v55_gate_aperture_phase_completion_attempt002
```

Do not continue attempt001 with more steps under the same reward. Do not unlock
`planner_integration_smoke`.

## Evidence

Attempt001 failed the two core event metrics at every milestone:

- `valid_aperture_cross_rate = 0.0`
- `post_gate_recovery_rate = 0.0`

The final checkpoint was otherwise stable:

- `crash_rate = 0.0`
- `mean_aperture_yz_error_m = 0.04664`
- `p90_aperture_yz_error_m = 0.02694`
- `hold_time_ratio = 0.9006`

This means the tracker learned to park at the gate aperture, not to cross it.

## Approved Fix

The approved attempt002 fix is deliberately narrow:

1. Keep `config/level3.toml` unchanged.
2. Keep evaluator and gate thresholds unchanged.
3. Add gate-aperture completion-shaping coefficients to the tracker reward:
   - gate-X progress while aligned;
   - valid aperture crossing bonus;
   - post-gate recovery bonus;
   - near-plane lingering penalty.
4. Keep these coefficients defaulted to zero so previous free-space tracker
   stages are not silently changed.
5. Move `config/level3_tracker_gate_aperture.toml` to an airborne near-plane
   reset distribution so the stage trains crossing/recovery, not takeoff.

## Attempt002 Training Command

After checker approval, run a bounded smoke and then:

```bash
pixi run -e gpu python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_gate_aperture.toml \
  --task gate_aperture_reference \
  --tracker-env-mode gate_aperture \
  --seed 560202 \
  --total-timesteps 15000000 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 8 \
  --update-epochs 4 \
  --learning-rate 3e-4 \
  --hidden-dim 256 \
  --max-episode-steps 500 \
  --checkpoint-interval 1000000 \
  --initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/gate_aperture_reference/v55_tracker_gate_aperture_phase_completion_attempt002_final.ckpt \
  --vel-error-coef 1.0 \
  --gate-x-progress-coef 4.0 \
  --gate-cross-bonus 4.0 \
  --gate-recover-bonus 0.05 \
  --gate-linger-penalty-coef 0.3 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-run-name v55_tracker_gate_aperture_phase_completion_attempt002 \
  --jax-device gpu \
  --cuda
```

## Required Checks

Before launching the 15M run:

- unit tests for tracker env, stage evaluator, and gate checker must pass;
- `git diff --check` must pass;
- `git diff --exit-code -- config/level3.toml` must pass;
- a 1024x32 smoke must save a checkpoint;
- evaluator smoke must load the checkpoint and produce finite metrics;
- a read-only checker must approve the semantic fix.

## Next Gate

After attempt002 training, evaluate all 1M milestone checkpoints and final.
Only unlock `planner_integration_smoke` if
`scripts/check_level3_tracker_stage_gate.py` passes for
`gate_aperture_reference`.
