# V53 Plan: Completion-First Hybrid Planner Controller

Date: 2026-06-25

## Objective

Build and evaluate a non-pure-PPO Level3 controller whose first goal is reliable
completion on unchanged `config/level3.toml`.

The user explicitly approved leaving the pure-PPO action path for this lane.
This lane is controller evidence, not PPO success, and must remain separate from
PPO training metrics.

## Target

Primary screen:

- hard eval config: unchanged `config/level3.toml`;
- success rate target: `>= 60%`;
- completion-first successful time: `15s-20s` is acceptable as an intermediate
  milestone, subject to the built-in 30s environment timeout;
- later optimization can push successful time toward the older `<= 7.0s` racing
  target.

## Why Change Direction

Recent pure PPO and planner-as-observation lanes plateau around the old frontier:

- global PPO best: `21%` success, `1.66` mean gates, `79%` crash;
- v51 planner-guidance observation: best `18%` success and `1.42` mean gates;
- v52 local MPPI tuning: `0%` success in smoke/dev, below the PPO frontier.

This says the immediate bottleneck is not a small reward number or hidden size.
The controller needs explicit phase logic: slow down, observe the gate/obstacle,
align in the gate frame, then cross.

## Structural Hypothesis

Use a slow-safe high-level controller with phases:

```text
takeoff/stabilize
-> cruise to pre-gate waypoint
-> sensing/slowdown inside local visibility distance
-> gate-frame align and obstacle-aware aperture selection
-> controlled crossing
-> post-gate recover and switch to next gate
```

Unlike v51, the planner may output actions directly in this lane. PPO is not the
only action source here.

## Preferred First Implementation

Implement a new controller file rather than mutating PPO inference:

```text
lsy_drone_racing/control/level3_hybrid_planner_controller.py
```

First version should be simple and debuggable:

- use `first_principles`-compatible attitude actions `[roll, pitch, yaw, thrust]`;
- use the actual observed/randomized gate and obstacle poses from the environment
  observation;
- choose a safe aperture point for each gate;
- cap cruise speed aggressively before the gate;
- use gate-frame local position to decide phase transitions;
- avoid static seed replay and any seed-specific hard-coded path;
- expose diagnostics for phase, target gate, aperture offset, and speed command.

MPPI can still be used later, but the immediate experiment should not be another
local MPPI cost-weight sweep.

## Evaluation Ladder

1. Finite-action smoke on seeds `101-105`.
2. Development eval on seeds `1-20`.
3. If smoke/dev shows nonzero success or clearly beats the PPO frontier on mean
   gates, run `validation_unseen 101-200`.
4. Promote if validation reaches `>= 60%` success, even if mean successful time
   is slower than 7s.

## Guardrails

- Do not edit `config/level3.toml` geometry, randomization, safety limits, seed
  split, or timeout.
- Do not record hybrid-controller success as PPO success.
- Do not generate PPO teacher data until a later decision explicitly approves it.
- Do not use static seed replay.
- Commit only small code/docs/state changes; keep generated CSVs/logs out of git
  unless explicitly requested.

## Next Action

Launch `v53_completion_first_hybrid_planner_controller` through the non-PPO
controller workflow. Start with implementation plus builder/checker verification,
then run smoke/dev evals before any full validation.
