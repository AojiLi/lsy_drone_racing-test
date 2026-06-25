# v55 Zigzag/Lemniscate Tracker Attempt001 Passed

## Summary

- Stage: `zigzag_or_lemniscate_tracking`
- Run: `v55_tracker_zigzag_from_curve_attempt001`
- W&B: <https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/pfo4433u>
- Training config: `config/level3_tracker_free_space.toml`
- Target Level3 config check: `config/level3.toml` unchanged
- Initial checkpoint: `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/curve_tracking/v55_tracker_curve_from_l_shape_attempt001_step_034958400.ckpt`
- Selected checkpoint: `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Selected metrics JSON: `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_zigzag_from_curve_attempt001_step8m_metrics.json`
- Gate checker output: `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_zigzag_from_curve_attempt001_step8m_gate.json`

## Command

```bash
pixi run -e gpu python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_free_space.toml \
  --task zigzag_or_lemniscate_tracking \
  --tracker-env-mode free_space \
  --seed 559101 \
  --total-timesteps 12000000 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 8 \
  --update-epochs 4 \
  --learning-rate 3e-4 \
  --hidden-dim 256 \
  --max-episode-steps 500 \
  --checkpoint-interval 1000000 \
  --initial-model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/curve_tracking/v55_tracker_curve_from_l_shape_attempt001_step_034958400.ckpt \
  --model-path lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_final.ckpt \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-run-name v55_tracker_zigzag_from_curve_attempt001 \
  --jax-device gpu \
  --cuda
```

## Milestone Sweep

All milestone checkpoints were evaluated on seeds `101-120` with
`scripts/evaluate_level3_tracker_stage.py`.

| checkpoint | completion | crash | mean cross-track m | p90 cross-track m | mean action delta | p90 action delta |
|---|---:|---:|---:|---:|---:|---:|
| step1m | 1.000 | 0.000 | 0.1786 | 0.3192 | 0.0098 | 0.0130 |
| step2m | 1.000 | 0.000 | 0.1141 | 0.3200 | 0.0089 | 0.0108 |
| step3m | 1.000 | 0.000 | 0.0980 | 0.3209 | 0.0300 | 0.0683 |
| step4m | 1.000 | 0.000 | 0.0999 | 0.3205 | 0.0351 | 0.0781 |
| step5m | 1.000 | 0.000 | 0.0988 | 0.3083 | 0.0201 | 0.0438 |
| step6m | 1.000 | 0.000 | 0.0943 | 0.3092 | 0.0249 | 0.0605 |
| step7m | 1.000 | 0.000 | 0.0970 | 0.2958 | 0.0104 | 0.0127 |
| step8m | 1.000 | 0.000 | 0.0987 | 0.2850 | 0.0105 | 0.0145 |
| step9m | 1.000 | 0.000 | 0.0941 | 0.2966 | 0.0105 | 0.0142 |
| step10m | 1.000 | 0.000 | 0.0825 | 0.2844 | 0.0583 | 0.1511 |
| step11m | 1.000 | 0.000 | 0.0806 | 0.2773 | 0.0780 | 0.2075 |
| final | 1.000 | 0.000 | 0.0784 | 0.2712 | 0.0594 | 0.1781 |

## Gate Result

The selected step8m checkpoint passed every required metric:

- `checkpoint_backed == true`
- `all_finite == true`
- `path_completion_rate = 1.0 >= 0.75`
- `crash_rate = 0.0 <= 0.08`
- `mean_cross_track_error_m = 0.098746 <= 0.22`
- `p90_cross_track_error_m = 0.285000 <= 0.4`
- `mean_action_delta_l2 = 0.010483 <= 0.4`
- `p90_action_delta_l2 = 0.014510 <= 0.65`

## Interpretation

The zigzag stage is solved with a large margin. Later checkpoints reduce
cross-track error further, but their action delta rises materially. Because this
stage is meant to prove a smooth low-level tracker, step8m is the best balanced
checkpoint: it keeps p90 cross-track error well below the gate while preserving
very smooth actions.

## Next Action

Unlock `gate_aperture_reference`. The next stage should start from the selected
step8m checkpoint and use the gate-aperture mini environment. Do not approve
planner-driven Level3 long training yet.
