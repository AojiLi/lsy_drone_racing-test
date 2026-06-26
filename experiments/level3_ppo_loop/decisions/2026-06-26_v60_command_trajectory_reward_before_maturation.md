# v60 Command-Trajectory Reward Before Maturation

Date: 2026-06-26

## Decision

Proceed with v60 support changes before any 8M maturation run.

The v60 input remains `level3_reference_tracker_command_v3` at 56 dimensions.
The change is reward-side only: `ReferenceCommandReward` now uses the short
reference horizon as the command, rather than treating the task as pure current
point chasing.

## Rationale

The current v60 observation already contains the needed command information:

- self state;
- current / next / lookahead reference points;
- desired velocity, desired speed, and desired heading;
- generic command masks;
- last action and short history.

The previous clean reward was valid, but still too close to "minimize distance
to current point." For planner-like commands, the tracker must learn whether to
move through, brake/hold, move slowly through, or recover speed. That behavior
is better represented by trajectory metrics:

- cross-track error to `current -> next -> lookahead`;
- along-track speed error;
- reverse-speed penalty;
- progress along the reference horizon;
- brake/hold overshoot past the stop point.

## Guardrails

- Do not change `config/level3.toml`.
- Do not change the v60 observation layout.
- Do not add gate, aperture, obstacle, finish, race-progress, stage-progress,
  or target-gate transition reward to v60.
- Keep `ReferenceTrackerReward` / `LegacyTrackerReward` for old paths and
  `gate_aperture_reference` diagnostics.
- Do not treat tiny smoke as learning evidence.

## Implementation

Files changed:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`
- `.agents/skills/level3-tracker-loop/SKILL.md`
- `.agents/skills/level3-tracker-loop/references/tracker-ppo-training.md`

New v60 reward coefficients:

- `trajectory_cross_track_coef = 1.2`
- `trajectory_along_speed_coef = 0.7`
- `trajectory_reverse_speed_coef = 0.5`
- `trajectory_overshoot_coef = 1.4`

New diagnostics include:

- `tracker/command_position_error`
- `tracker/command_velocity_error`
- `tracker/trajectory_cross_track_error`
- `tracker/command_cross_track_error`
- `tracker/trajectory_along_m`
- `tracker/trajectory_along_speed`
- `tracker/moving_along_speed_error`
- `tracker/moving_reverse_speed`
- `tracker/brake_hold_overshoot`
- `tracker/command_progress`

## Validation

Commands run:

```bash
pixi run ruff check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py
pixi run ruff format --check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py
pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/scripts/test_level3_tracker_stage_gate.py -q
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py --config level3_tracker_free_space.toml --task reference_command_no_gate_reward --tracker-env-mode free_space --observation-layout auto --seed 26064 --total-timesteps 1024 --num-envs 4 --num-steps 64 --num-minibatches 4 --update-epochs 1 --checkpoint-interval 0 --model-path /tmp/v60_command_trajectory_reward_smoke.ckpt --jax-device gpu --cuda
```

Results:

- ruff check: passed.
- ruff format check: passed.
- focused pytest: `40 passed, 1 warning`.
- tiny trainer smoke: checkpoint saved at
  `/tmp/v60_command_trajectory_reward_smoke.ckpt`.
- checkpoint metadata:
  - task: `reference_command_no_gate_reward`;
  - observation layout: `level3_reference_tracker_command_v3`;
  - obs dim: `56`;
  - reward model: `reference_command_reward`;
  - all gate / obstacle / gate-cross coefficients: `0.0`;
  - new trajectory coefficients recorded.

## Next Action

Run a bounded W&B v60 smoke using the updated command-trajectory reward. If the
smoke is clean, proceed to an explicit bounded maturation run for
`reference_command_no_gate_reward` rather than judging learning from the smoke.
