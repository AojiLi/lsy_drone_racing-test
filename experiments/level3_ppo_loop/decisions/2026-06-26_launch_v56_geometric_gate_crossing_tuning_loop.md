# v56 Decision: Launch Geometric Gate-Crossing Tuning Loop

## Decision

Launch:

```text
v56_geometric_gate_crossing_tuning_loop
```

Use the new repo skill:

```text
.agents/skills/level3-geometric-planner-loop/SKILL.md
```

This loop is planner-only. Do not train PPO, change the tracker checkpoint,
change reward, add MPPI, or modify `config/level3.toml`.

Core semantic guard:

```text
Do not optimize by making the planner skip or reinterpret environment gate-pass
semantics. Only an environment target_gate transition counts as a real gate
pass for planner control flow.
```

Custom pass checkers may be used for diagnostics only. They must not trigger
recover, next-gate logic, or any deployed planner state transition.

## Baseline

The v55 500-step trace diagnostic used:

```text
config: config/level3.toml
planner: GeometricSlowGatePlanner
tracker checkpoint: lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
seeds: 101-120
level3 steps: 500
```

Observed:

```text
first-gate progress = 20/20
gate0 pass = 3/20
contact = 15/20
max_steps = 5/20
all_finite = true
config/level3.toml unchanged = true
```

Successful gate0 passes had near-plane Y/Z error around `0.10m-0.19m`; failed
plane-crossing seeds were commonly `0.5m+` off aperture. This makes the next
problem a gate-front planner policy problem, not a PPO training problem.

## V56 Target

Before promoting to multi-gate planner smoke, reach:

```text
first-gate progress = 20/20
gate0 pass >= 10/20
contact <= 8/20
early termination <= 6/20
all_finite = true
config/level3.toml unchanged
```

## Task Order

1. Align stabilization:
   require low aperture Y/Z error and explicitly measured modest gate-local X
   speed before cross.
2. Cross slowdown:
   reduce cross desired speed and smooth the cross reference.
3. Near-plane backout:
   if near gate plane but far off aperture, go back to pre-gate align instead
   of forcing a crossing.
4. Recover after real gate switch:
   do not enter recover based only on local X. In the same `target_gate`, recover
   is forbidden; if local X is past the plane but the environment did not switch
   gates, continue slow cross/hold or back out to pre-gate align.
5. Formal 500-step smoke gate:
   rerun fixed seeds `101-120` and classify trace failures.

## Required Loop Outputs

Every v56 iteration must write:

- an analysis packet under `experiments/level3_ppo_loop/analysis/`;
- a decision packet under `experiments/level3_ppo_loop/decisions/`;
- a plain Chinese note under `drone_notes/level3_loops/`;
- a state update in `experiments/level3_ppo_loop/state.json`.

Every v56 iteration may change only one planner strategy knob unless its
decision packet explicitly explains why two changes cannot be separated.

Commit and push intended small files. Keep large trace/metrics JSONs ignored
unless the user explicitly asks to commit them.

## Promotion Rule

If the v56 target passes, write a promotion decision for:

```text
multi-gate planner smoke
```

The next smoke should measure whether `max_gate_index >= 2` increases. It still
does not approve PPO long training by itself.
