# V53 Plan: Completion-First Trajectory Planner + PPO Tracker

Date: 2026-06-25

## Objective

Build and evaluate a non-pure-PPO Level3 controller whose first goal is reliable
completion on unchanged `config/level3.toml`.

The user explicitly approved leaving the pure-PPO action path for this lane.
This lane is controller evidence, not PPO success, and must remain separate from
PPO training metrics.

The refined architecture is:

```text
observed/nominal gates and obstacles
-> upper planner or MPPI/geometric local planner
-> short reference trajectory: target_pos, target_vel, desired_speed, phase
-> virtual local-gate observation adapter
-> Level2 PPO trajectory tracker
-> [roll, pitch, yaw, thrust]
```

The upper planner should think about route and timing. The tracker should think
about flying the drone body.

## Selected Tracker

Use the stable Level2 PPO checkpoint as the first tracker:

```text
lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever/level2_DR_latencyobs_middlemanuever_final.ckpt
```

Observed checkpoint properties:

- observation layout: `obstacle_heading_xy_v1`;
- hidden dim: `256`;
- actor input dim: `103`;
- action dim: `4`;
- action output semantics: `[roll, pitch, yaw, thrust]`.

This checkpoint already has strong Level2 flight/body-control behavior. It
should not be treated as a complete Level3 planner. Instead, the v53 controller
should synthesize a Level2-style virtual local gate from the planner reference
so the Level2 policy can act as a short-horizon tracker.

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

Use a slow-safe high-level planner with phases:

```text
takeoff/stabilize
-> cruise to pre-gate waypoint
-> sensing/slowdown inside local visibility distance
-> generate/replan local reference trajectory
-> gate-frame align and obstacle-aware aperture selection
-> controlled crossing
-> post-gate recover and switch to next gate
```

The key Level3 detail is `sensor_range = 0.7`. Far away, gates and obstacles may
only be nominal. Near the gate, the controller should slow down, let true local
geometry enter observation, and then replan the next local trajectory.

Unlike v51, this lane is not limited to planner-as-observation. The planner may
drive the deployed controller through reference trajectories, and direct
non-PPO action output is allowed for tracker baselines. The preferred main path
is not MPPI directly outputting every action; it is upper planner -> trajectory
reference -> PPO/low-level tracker.

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
- maintain a reference trajectory queue for the next `1s-2s`;
- expose tracker inputs such as reference position error, reference velocity
  error, active phase, desired speed, gate-frame local position, and aperture
  offset;
- cap cruise speed aggressively before the gate;
- slow down when entering the `0.7m-1.0m` local visibility band, then replan;
- use gate-frame local position to decide phase transitions;
- avoid static seed replay and any seed-specific hard-coded path;
- expose diagnostics for phase, target gate, aperture offset, and speed command.

MPPI can be used as the upper planner if useful. The immediate experiment should
not be another local MPPI cost-weight sweep; it should test whether trajectory
factorization makes the task easier.

If the Level2 PPO tracker cannot directly track the synthetic virtual gate
without retraining, use a minimal deterministic tracker as a control sanity
baseline, then open a follow-up PPO-tracker imitation/fine-tuning packet only
after the planner/tracker interface has useful smoke/dev evidence.

## Virtual Gate Adapter

The adapter should map each planner reference into the kind of local task the
Level2 PPO understands:

- reference point -> synthetic active gate center;
- desired heading -> synthetic gate yaw/normal;
- reference velocity and desired speed -> tracker history/velocity context;
- obstacle-aware aperture -> local synthetic gate offset;
- real Level3 obstacles -> preserve nearest obstacle terms when available.

The adapter must be generic and recomputed online. Do not use static
seed-specific routes.

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
controller workflow. Implement the planner trajectory interface, the virtual
Level2-gate adapter, and the Level2 PPO tracker wrapper. Start with
builder/checker verification, then run smoke/dev evals before any full
validation.
