# v55 Tracker Autonomous 12-Stage Loop Support

Date: 2026-06-25

## System Assessment

The Codex goal-loop design can supervise a long tracker curriculum, run
commands, inspect W&B, spawn subagents, make code/config changes, and retry.
However, before this packet the repository was missing one critical loop
component:

```text
trained checkpoint -> stage metrics JSON -> stage gate checker
```

The gate checker already existed, but the repository did not yet have a stable
stage evaluator that could generate all gate metrics for the 12-stage tracker
ladder. Without that evaluator, a `/goal` would have to improvise metrics during
the run, which is too fragile for unattended overnight iteration.

## Implemented Support

Added:

```text
scripts/evaluate_level3_tracker_stage.py
```

This evaluator:

- loads a tracker checkpoint;
- selects the stage definition from
  `experiments/level3_ppo_loop/tracker_qualification_gates.json`;
- runs the matching tracker task/config;
- emits a metrics JSON consumable by
  `scripts/check_level3_tracker_stage_gate.py`;
- supports the final `planner_integration_smoke` by aggregating first-gate
  progress, gate-0 pass count, early termination, and finite-action checks.

Also fixed `gate_aperture_reference` phase routing in
`lsy_drone_racing/control/level3_reference_tracker.py`; it now uses the
single-gate aperture phase logic instead of falling through to the Level3 phase
logic.

Updated:

```text
.agents/skills/level3-tracker-loop/SKILL.md
```

The skill now records the autonomous 12-stage protocol:

```text
train current stage
-> evaluate current stage
-> check current stage gate
-> pass unlocks next stage
-> fail triggers 3 analysis subagents and main-agent decision
-> retry same stage after the smallest justified change
```

## Failure Loop

On a failed stage gate, the loop should spawn exactly three subagents:

1. `tracker_eval_metrics`
   - inspect stage metrics, failed gates, episode rows, crash patterns,
     overshoot, terminal speed, and action smoothness.
2. `tracker_wandb_ppo`
   - inspect W&B training curves, reward components, entropy, clip fraction,
     value loss, and undertraining/instability signs.
3. `tracker_structure_research`
   - decide whether the next retry should change training duration, reward
     numbers, curriculum difficulty, observation features, PPO hyperparameters,
     or code/config semantics.

The main agent writes the decision packet and owns the retry decision. If code
or training semantics change, builder/checker is required before more training.

## Validation

Passed:

```bash
pixi run -e tests ruff check \
  scripts/evaluate_level3_tracker_stage.py \
  tests/unit/scripts/test_level3_tracker_stage_evaluator.py \
  lsy_drone_racing/control/level3_reference_tracker.py \
  tests/unit/control/test_level3_reference_tracker_env.py
```

```bash
pixi run -e tests python -m pytest \
  tests/unit/scripts/test_level3_tracker_stage_evaluator.py \
  tests/unit/control/test_level3_reference_tracker_env.py \
  tests/unit/scripts/test_level3_tracker_stage_gate.py -q
```

Result: `12 passed`.

Smoke:

- saved an untrained tracker checkpoint under `/tmp`;
- evaluated `hover` for one short episode with
  `scripts/evaluate_level3_tracker_stage.py`;
- fed the metrics JSON to `scripts/check_level3_tracker_stage_gate.py`;
- gate checker correctly failed with exit code `2`.

## Current Operational Status

The system is now ready for a Codex-supervised `/goal` that attempts the full
12-stage tracker ladder. It still cannot guarantee that the model will reach
every metric, because that depends on training dynamics and GPU time. But the
loop now has the required mechanical pieces to train, evaluate, reject/accept,
analyze failures, make justified changes, and retry without skipping stages.

Current unlocked stage remains:

```text
hover
```

No stage is marked passed by this packet.
