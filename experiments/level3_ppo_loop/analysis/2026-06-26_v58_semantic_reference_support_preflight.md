# V58 Semantic Reference Support Preflight

Date: 2026-06-26T19:59:33+02:00

Lane: `v58_tracker_semantic_planner_reference_training`

Decision context:

- v57a fixed the phase3 -> phase4 planner reference discontinuity.
- Gate0 pass/contact did not improve, and phase4 speed stayed too high.
- The next bottleneck is likely that the tracker sees where to go but not what a waypoint means.

## Scope

This preflight implemented and checked code support only. It did not launch long
training, did not change `config/level3.toml`, and did not change Level3 track
geometry.

## Implemented

- Added a new observation layout:
  `level3_reference_tracker_semantic_v2`.
- Preserved the old layout:
  `level3_reference_tracker_v1`, `REFERENCE_TRACKER_OBS_DIM=65`.
- Added explicit waypoint intent fields for v58:
  `through`, `brake_or_hold`, `slow_through`, `recover`, plus `stop_signal`,
  `brake_mask`, and `slow_through_mask`.
- Added `semantic_planner_reference` as a free-space tracker task.
- Added semantic reward diagnostics and optional reward coefficients. Defaults
  are zero, so old v55 reward behavior is not silently changed.
- Updated vectorized PPO trainer to derive `obs_dim` from the environment and
  store checkpoint layout metadata.
- Updated stage evaluator to load v1/v2 checkpoint layouts dynamically for
  tracker stages and report semantic metrics.
- Updated tracker gate spec so the required path is now:

```text
zigzag_or_lemniscate_tracking
  -> semantic_planner_reference
  -> planner_integration_smoke
```

`gate_aperture_reference` remains optional diagnostic only.

## Compatibility

The current v55 zigzag checkpoint remains default-v1 compatible:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/
  zigzag_or_lemniscate_tracking/
  v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

The deployed planner smoke controller still constructs `ReferenceTrackerObservation()`
with the default v1 layout. V2 checkpoints require explicit semantic layout use
and should not be loaded accidentally as old v1 controller checkpoints.

## Checks

Focused tests:

```text
pixi run -e tests pytest \
  tests/unit/scripts/test_level3_reference_tracker_smoke.py \
  tests/unit/control/test_level3_reference_tracker_env.py \
  tests/unit/scripts/test_level3_tracker_stage_evaluator.py \
  tests/unit/scripts/test_level3_tracker_stage_gate.py
```

Result:

```text
33 passed, 1 warning
```

Tiny v58 semantic trainer smoke:

```text
pixi run -e tests python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_free_space.toml \
  --task semantic_planner_reference \
  --tracker-env-mode free_space \
  --total-timesteps 32 \
  --num-envs 2 \
  --num-steps 8 \
  --num-minibatches 1 \
  --update-epochs 1 \
  --jax-device cpu \
  --model-path /tmp/v58_semantic_smoke_after_checker.ckpt \
  --max-episode-steps 24
```

Result: checkpoint saved successfully. This is plumbing only, not evidence of
learning.

Old v55 planner smoke compatibility:

```text
pixi run -e tests python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101 \
  --level3-steps 5 \
  --early-termination-step-threshold 2 \
  --output /tmp/v58_old_planner_smoke_after_checker.json
```

Result: finite action, checkpoint-backed, unchanged `config/level3.toml` path.

Read-only checker gate:

```text
ALL GREEN
```

Checker verified v1/v2 layout separation, old checkpoint compatibility,
planner smoke v1 default path, semantic waypoint intent fields, dynamic
trainer/evaluator obs_dim handling, empty `config/level3.toml` diff, JSON parse,
compile checks, and focused pytest.

## Next Action

Launch only a bounded v58 semantic stage preflight/first training-stage command,
not direct Level3 long training.

Recommended first v58 command shape:

```text
pixi run -e gpu python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_free_space.toml \
  --task semantic_planner_reference \
  --tracker-env-mode free_space \
  --observation-layout auto
```

But because v58 uses a new obs_dim, the old v55 checkpoint cannot be used
directly as an initial model. The next decision should either:

- start v58 semantic training from scratch with the v2 layout; or
- implement an explicit v1 -> v2 actor/critic transfer initializer that copies
  compatible old weights and initializes the new semantic columns safely.

Do not silently load v1 as v2.
