# Decision: V58 Semantic Support Passed, Launch Bounded Semantic Preflight

Date: 2026-06-26T19:59:33+02:00

Decision type: `launch_named_structural_lane`

Approved lane:

```text
v58_tracker_semantic_planner_reference_training
```

## Decision

The builder/checker-gated v58 semantic support preflight passed. The next step
is a bounded `semantic_planner_reference` tracker preflight or first training
stage. Do not launch direct Level3 long training yet.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-26_v58_semantic_reference_support_preflight.md
```

Read-only checker result:

```text
ALL GREEN
```

Key checks:

- `REFERENCE_TRACKER_OBS_DIM` remains `65`.
- New semantic layout is isolated as
  `level3_reference_tracker_semantic_v2`.
- Old v55 zigzag checkpoint remains v1 loadable.
- Planner smoke still uses v1 by default and runs on unchanged
  `config/level3.toml`.
- New semantic task exposes explicit waypoint intent:
  `through`, `brake_or_hold`, `slow_through`, `recover`, plus stop/brake/slow
  masks.
- Trainer and evaluator handle dynamic obs_dim.
- Focused tests passed: `33 passed, 1 warning`.
- Tiny semantic trainer smoke saved a checkpoint under `/tmp`.
- Old v55 planner smoke compatibility remained finite.

## Guardrails

- Do not change `config/level3.toml`.
- Do not edit Level3 track geometry or randomization.
- Do not treat tiny smoke runs as learning evidence.
- Do not load a v1 checkpoint as v2 unless an explicit v1 -> v2 transfer
  initializer is implemented and checked.
- Do not launch planner-driven Level3 long training until the semantic tracker
  stage has a checkpoint-backed evaluation packet and decision.

## Important Compatibility Note

V58 semantic layout has a larger observation dimension than v55:

```text
v1: 65
v2: 72
```

Therefore the existing zigzag-qualified v55 checkpoint cannot be directly used
as `--initial-model-path` for v58 semantic training. The immediate safe option
is to start a v2 semantic preflight from scratch. A future builder/checker task
may add an explicit transfer initializer that copies compatible v1 weights and
initializes the new semantic columns, but that is not silently allowed.

## Approved Next Command

This is a bounded smoke/preflight, not a maturity run:

```bash
pixi run -e gpu python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_free_space.toml \
  --task semantic_planner_reference \
  --tracker-env-mode free_space \
  --observation-layout auto \
  --total-timesteps 32768 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 8 \
  --update-epochs 2 \
  --jax-device gpu \
  --model-path lsy_drone_racing/control/checkpoints/v58_tracker_semantic_planner_reference/v58_semantic_preflight_smoke.ckpt \
  --max-episode-steps 180 \
  --wandb-enabled \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v58_semantic_reference_preflight_smoke
```

After that, evaluate the checkpoint:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage semantic_planner_reference \
  --checkpoint lsy_drone_racing/control/checkpoints/v58_tracker_semantic_planner_reference/v58_semantic_preflight_smoke.ckpt \
  --episodes 5 \
  --seeds 101-105 \
  --max-episode-steps 180 \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v58_semantic_preflight_smoke_metrics.json
```

Then run the tracker stage gate for diagnostics:

```bash
pixi run -e gpu python scripts/check_level3_tracker_stage_gate.py \
  --stage semantic_planner_reference \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v58_semantic_preflight_smoke_metrics.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v58_semantic_preflight_smoke_gate.json
```

The gate is not expected to pass after one 1024x32 rollout batch. This command checks
plumbing, W&B logging, checkpoint metadata, v2 evaluator loading, and semantic
metrics. If plumbing is clean, a later decision can approve a real maturation
chunk.

## Maturation Direction After Preflight

If the preflight is clean, the likely next real training budget is:

```text
8M semantic_planner_reference maturation
checkpoint interval 1M
evaluate all milestones
```

This still remains tracker training, not direct Level3 training.
