# V58 Semantic Planner-Reference Tracker Plan

## Why V58 Is Needed

V57A fixed the main planner-interface discontinuity:

```text
phase3 -> phase4 reference jump: 0.740m -> 0.280m
phase3 -> phase4 reference error: 0.783m -> 0.340m
phase3 -> phase4 action delta: 0.727 -> 0.491
```

But the Level3 smoke did not improve:

```text
gate0 pass: 2/20
contact: 20/20
near-plane phase4 actual gate-local X speed median: 0.521m/s
near-plane phase4 actual gate-local X speed p75: 0.694m/s
```

The planner now gives a smoother path, but the tracker still does not slow down
enough near the gate. This suggests the tracker may not understand the
semantics of each reference point.

## Core Hypothesis

V58 should not train a generic point tracker. It should train a planner-command
trajectory tracker:

```text
semantic reference trajectory -> PPO tracker -> roll / pitch / yaw / thrust
```

The planner must tell the tracker both:

```text
where to go
what this waypoint means
```

The most important part is not a label. The important part is the concrete
short-horizon command: future reference points, desired speed/velocity, and
desired heading. A waypoint label or mask is only an auxiliary hint. Without a
clear future horizon and speed/heading command, the tracker can treat every
point as a pass-through target and rush through brake/alignment points.

## Reference Interface

The deployed actor should eventually receive enough information to distinguish:

```text
reference_point
next_point
lookahead_point
desired_velocity
desired_speed
desired_heading
waypoint_type / stop_signal / brake_mask
```

Priority order:

```text
1. future reference points
2. desired speed / desired velocity
3. desired heading
4. auxiliary waypoint masks
```

Suggested waypoint semantics:

| Semantics | Intended behavior | Typical speed |
| --- | --- | --- |
| `through` | pass smoothly through the point | `0.6-1.0m/s` |
| `brake_or_hold` | slow down, hold/alignment-stabilize | `0.0-0.1m/s` |
| `slow_through` | cross slowly without stopping dead | `0.25-0.35m/s` |
| `recover` | restore speed gradually after constraint | increasing from slow |

Concrete command examples:

- `brake_or_hold`: current target is the alignment point, near-future points
  barely move, desired speed is about `0.05m/s`, and desired heading aligns
  with the gate.
- `slow_through`: current target is the aperture center, next/lookahead points
  continue through the gate, desired speed is about `0.30m/s`, and desired
  heading follows the gate normal.

## Training Curriculum

Start in tracker training environments, not full Level3 reward tuning.

Recommended v58 task families:

1. Single semantic waypoint:
   - `through`
   - `brake_or_hold`
   - `slow_through`
   - `recover`
2. Short semantic chains:
   - `through -> brake_or_hold`
   - `brake_or_hold -> slow_through`
   - `slow_through -> recover`
3. Planner-like gate-front chain:
   - far cruise point
   - pre-gate brake/align point
   - aperture slow-through point
   - post-gate recover point
4. Randomized variants:
   - starts, headings, speed targets, curvature, lateral offsets, and mild
     dynamics disturbances after nominal behavior works.

## Metrics

V58 should not be accepted by Level3 gate pass alone. It needs per-semantics
tracker metrics:

- position error by waypoint type;
- desired speed error by waypoint type;
- brake/hold terminal speed;
- dwell stability for brake/hold targets;
- slow-through segment speed;
- overshoot after brake/hold;
- action delta and action norm around semantic transitions;
- wrong-semantics failures:
  - rushing through a brake point;
  - stopping dead at a slow-through point;
  - recovering too early;
  - ignoring desired heading.

## Required Implementation Questions

Before launching long v58 training, answer these in a builder/checker-gated
packet:

1. Does the current actor observation already expose enough semantic intent?
2. If not, what is the smallest observation-layout extension?
3. How are waypoint types encoded?
   - one-hot type;
   - scalar stop/brake/slow-through masks;
   - desired speed / desired velocity may be necessary but not sufficient.
4. Which reward terms prevent the tracker from treating all points as
   pass-through?
5. Which evaluator metrics detect wrong waypoint semantics and wrong concrete
   command following?

## Guardrails

- Do not modify `config/level3.toml`.
- Do not use full-race progress reward as the main tracker-learning reward.
- Do not call v58 a Level3 success unless it later passes unchanged
  `config/level3.toml` smoke/hard eval.
- Use W&B for long training.
- Use milestone checkpoints and stage gates.
- If v58 changes observation layout, reward semantics, evaluator semantics, or
  trainer behavior, use builder/checker before training.

## Expected Outcome

The first v58 milestone is not full Level3 completion. The first milestone is:

```text
Given a planner-like semantic trajectory, the tracker slows for brake/hold
points, passes slow-through points at the commanded low speed, and recovers
smoothly afterward without large overshoot or action spikes.
```
