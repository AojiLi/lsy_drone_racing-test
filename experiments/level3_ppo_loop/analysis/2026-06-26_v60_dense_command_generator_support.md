# v60 Dense Command Generator Support

## Judgment

The user correction is right: the v60 tracker generator should not feed PPO a
few sparse points and expect it to infer the intended maneuver. Before 8M
maturation, `reference_command_no_gate_reward` needed a planner-like dense
reference generator.

This support change keeps the v60 actor input fixed:

```text
level3_reference_tracker_command_v3, obs_dim=56
```

It still excludes gate, obstacle, aperture, planner phase, race progress, and
target-gate semantics.

## Implemented

- Added an episode-local `ReferenceCommandPlan`.
- Replaced the old fixed x-axis sparse v60 command path with randomized
  planner-like sequences:
  `pass_through -> hold_or_brake -> low_speed_through -> recover_speed`.
- Randomized direction, length, height, curvature, speed, phase duration,
  braking distance, slow-through distance, and recovery angle.
- Made moving command `desired_velocity` follow the short visible horizon
  `current -> lookahead`.
- Made `hold_or_brake` look like a real hold/brake command:
  `current`, `next`, and `lookahead` stay close to the brake point and
  `desired_velocity` is zero.
- Kept old non-v60 reference tasks on their legacy desired-velocity path to
  avoid breaking existing v55/v57 planner smoke compatibility.
- Seeded vector-env generators per environment so parallel training does not
  show all envs the same command plan.

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
pytest: 41 passed, 1 warning
```

Tiny trainer smoke:

```text
checkpoint: lsy_drone_racing/control/checkpoints/v60_dense_command_generator_smoke/v60_dense_command_generator_smoke_final.ckpt
total_timesteps: 1024
num_envs: 16
num_steps: 64
task: reference_command_no_gate_reward
```

Checkpoint-backed evaluator smoke:

```text
metrics_json: experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_dense_command_generator_smoke_metrics.json
gate_json: experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_dense_command_generator_smoke_gate.json
episodes: 5
seeds: 101-105
all_finite: true
checkpoint_backed: true
semantic_waypoint_type_count: 4
crash_rate: 0.0
```

The stage gate still failed, as expected for a 1024-step smoke, mainly on
brake/slow tracking accuracy. This is plumbing and semantics evidence, not
learning evidence.

## Boundaries

- `config/level3.toml` unchanged.
- No Level3 track geometry/randomization changes.
- No gate, obstacle, aperture, finish, race-progress, or stage-progress reward
  added to v60.
- No observation dimension/layout change.
- No long training launched.

## Next

Run one bounded W&B-tracked v60 dense-generator smoke if live dashboard evidence
is desired, then launch the real `8M` v60 maturation chunk with milestone
evaluation. Do not judge learning from the 1024-step smoke.
