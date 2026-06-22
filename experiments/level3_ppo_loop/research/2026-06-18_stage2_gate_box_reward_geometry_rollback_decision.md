# Level3 PPO Stage 2 Decision: Roll Back Gate-Box Reward Geometry

## Scope

This is the post-run decision for:

```text
level3_loop_009_stage2_gate_box_reward_geometry
```

It does not approve another training run.

## Verdict

Roll back / hold the gate-box reward-geometry direction.

Do not continue from any `009` checkpoint.

Keep the current fixed-inference global best:

```text
lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt
```

## Hard-Eval Result

Best `009` checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_020000000.ckpt
```

Metrics:

| Checkpoint | Success | Crash | Mean gates | Score | Target met |
| --- | ---: | ---: | ---: | ---: | --- |
| Current best `004:30M` | `0.0` | `1.0` | `0.90` | `-71.4` | no |
| Stage2 gate-box best `009:20M` | `0.0` | `1.0` | `0.75` | `-72.0` | no |

The `009` run did not meet any acceptance criterion:

- `success_rate > 0.0`: no
- `mean_gates > 0.9`: no
- `crash_rate < 1.0`: no
- linked gate-edge crash taxonomy improvement without lost progress: no

## W&B Evidence

W&B run:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_009_stage2_gate_box_reward_geometry
```

Analyzer report:

```text
experiments/level3_ppo_loop/analysis/level3_loop_009_stage2_gate_box_reward_geometry_analysis.md
```

Key signals:

- `race/finished_rate`: tail mean `0.0`
- `race/passed_gate_rate`: tail mean `0.009155`, flat
- `race/gate_stage`: tail mean `0.206818`, flat
- `race/gate_axis_x`: tail mean `-0.957882`, down
- `losses/approx_kl`: tail mean `0.001564`, below `target_kl=0.03`
- `losses/clipfrac`: tail mean `0.001108`
- `losses/entropy`: rising, not collapsed

Interpretation:

- No gate/finish conversion.
- No PPO-instability signature.
- The gate-box reward geometry hypothesis did not convert into hard-eval
  progress.

## Reviewer Consensus

Evaluator reviewer:

- Reject.
- `009:20M` has `success_rate=0.0`, `crash_rate=1.0`, `mean_gates=0.75`.
- Do not update best.
- Keep `004:30M`.

W&B/PPO reviewer:

- No gate/finish conversion.
- PPO metrics are stable.
- Do not continue or repeat the current gate-box geometry direction.

Tuning/decision reviewer:

- Roll back gate-box geometry.
- Do not continue from `009`.
- Hold training and continue structural diagnosis.

## Decision

Hold.

Do not launch another reward-geometry train/eval chunk.

Do not continue from:

```text
lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/
```

The target is still unmet:

- Required: `success_rate >= 0.60`
- Required: `mean_time_s_success <= 7.0s`
- Current best: `success_rate=0.0`, `crash_rate=1.0`, `mean_gates=0.90`,
  `mean_time_s_success=null`

## Next Action

Continue Stage 2 structural diagnosis, not reward-number search and not this
reward-geometry branch.

Recommended next diagnostic direction:

- inspect train/eval mismatch around the evaluator module default, because the
  `009` evaluator summary still labels `inference_module=ppo_level2_inference`
  while the fixed-inference best was refreshed with `ppo_level3_inference`;
- ensure future Level3 loop eval commands use the corrected Level3 inference
  module explicitly;
- only then propose the next narrow structural experiment.

## Evaluator Module Follow-Up

The loop evaluator command used the evaluator default, which labelled the
original `009` eval rows as:

```text
inference_module=ppo_level2_inference
```

Both Level2 and Level3 inference modules already include the rotmat parity fix,
but future Level3 loop evals should explicitly use:

```text
--inference-module ppo_level3_inference
```

Follow-up re-eval command:

```text
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3_dr.toml \
  --seed-start 1 \
  --num-seeds 20 \
  --inference-module ppo_level3_inference \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_loop_009_stage2_gate_box_reward_geometry_level3_inference_reval \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_005000000.ckpt \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_010000000.ckpt \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_015000000.ckpt \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_020000000.ckpt \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_025000000.ckpt \
  lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_final.ckpt
```

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_009_stage2_gate_box_reward_geometry_level3_inference_reval_summary.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_009_stage2_gate_box_reward_geometry_level3_inference_reval_episodes.csv`

Result:

- Best Level3-inference re-eval checkpoint: `009:20M`
- `success_rate=0.0`
- `crash_rate=1.0`
- `mean_gates=0.75`
- `mean_time_s_success=null`

This confirms the rollback decision under the explicit Level3 inference module.
