# v60 Brake-Ramp Generator Support

## Judgment

The dense v60 command generator still had one important risk: it could move
from a fast `pass_through` command directly into `hold_or_brake`. That asks the
tracker to cancel inertia at the phase boundary and can train an unstable
"rush then panic-stop" behavior.

This support pass keeps the same clean v60 interface and adds a deceleration
zone before hold.

## Implemented

- Kept `level3_reference_tracker_command_v3` unchanged at `56` dims.
- Kept generic command types unchanged:
  `pass_through`, `hold_or_brake`, `low_speed_through`, `recover_speed`.
- Added per-plan brake-entry speed around `0.15-0.24m/s`.
- Split the pass approach into:
  - cruise section at about `0.55-0.78m/s`;
  - smooth deceleration section;
  - stationary hold/brake horizon.
- During deceleration, both `desired_speed` and reference-point spacing shrink
  smoothly with the speed ramp.
- Kept moving `desired_velocity` aligned with `current -> lookahead`.
- Kept `hold_or_brake` desired velocity at zero.

This teaches:

```text
fly -> slow down -> hold
```

instead of:

```text
fly -> instant stop
```

## Validation

Passed:

```bash
pixi run ruff check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py scripts/evaluate_level3_tracker_stage.py scripts/check_level3_tracker_stage_gate.py
pixi run ruff format --check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py
pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/scripts/test_level3_tracker_stage_gate.py -q
```

Result:

```text
ruff: passed
format check: passed
pytest: 42 passed, 1 warning
```

Tiny trainer smoke:

```text
checkpoint: lsy_drone_racing/control/checkpoints/v60_brake_ramp_generator_smoke/v60_brake_ramp_generator_smoke_final.ckpt
total_timesteps: 1024
num_envs: 8
num_steps: 64
jax_device: cpu
```

The first GPU tiny smoke failed with CUDA out-of-memory before training
started, so the same plumbing smoke was rerun on CPU and passed.

Checkpoint-backed evaluator smoke:

```text
metrics_json: experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_brake_ramp_generator_smoke_metrics.json
gate_json: experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_brake_ramp_generator_smoke_gate.json
episodes: 5
seeds: 101-105
all_finite: true
checkpoint_backed: true
semantic_waypoint_type_count: 4
crash_rate: 0.0
```

The stage gate still failed, as expected for a 1024-step smoke, mainly on
brake/slow tracking accuracy. This is not evidence against learning; it only
confirms the changed command generator is runnable.

## Boundaries

- `config/level3.toml` unchanged.
- No Level3 track geometry/randomization changes.
- No gate, obstacle, aperture, finish, race-progress, or stage-progress reward
  added to v60.
- No observation dimension/layout change.
- No long training launched.

## Next

Launch the v60 `8M` maturation using the brake-ramp dense command generator and
evaluate milestone checkpoints before planner integration.
