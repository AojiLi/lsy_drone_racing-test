# v55 Tracker Training Environment Memory

Date: 2026-06-25

Purpose: durable project memory for the next Level3 tracker-training loop.

## Core Decision

For the low-level PPO reference tracker, the early training environment should
change. It should not start inside the full Level3 race environment with all
gates, obstacles, race termination, and gate-progress semantics active.

The bottom PPO's first skill is not "finish Level3." Its first skill is:

```text
given a reference point / reference velocity / desired heading,
fly there accurately, smoothly, and safely,
then slow down or hold without overshooting.
```

Therefore v55 should use a staged tracker-training environment:

```text
free-space tracker env
  -> gate-aperture mini env
  -> unchanged level3.toml planner-integration smoke
```

This is a training-environment change, not a competition-track change.
`config/level3.toml` remains the immutable final target.

## Why This Matters

Current v54 wraps the Level3 race env even for simple tracker tasks. That means
`hover` and `point` tasks still inherit Level3 gates, obstacles, track
structure, and race-env termination behavior. This is useful for final smoke,
but it is too noisy for teaching the bottom PPO the basic servo skill.

The likely current failure mode is not simply "bad over-gate reward." It is that
the bottom policy has not yet proven it can follow references with:

- low final position error;
- low cross-track error;
- controlled speed;
- low terminal speed near target;
- bounded overshoot;
- smooth actions;
- stable attitude.

Without that, an upper planner can generate good points and the PPO can still
crash, overshoot, or fail to slow down.

## Required v55 Environment Split

### 1. Free-Space Tracker Environment

Use this for early tracker tasks:

- `hover`
- `point_hold`
- `point_reach`
- `brake_to_point`
- `line_tracking`
- `heading_tracking`
- `multi_point_reference`
- `l_shape_tracking`
- `curve_tracking`
- `zigzag_or_lemniscate_tracking`

Design requirements:

- no gates;
- no obstacles;
- no Level3 gate-progress reward;
- no race finish condition;
- no gate collision or obstacle collision semantics;
- keep the same drone dynamics and attitude action interface;
- train on reference-following reward only;
- report tracker metrics, not Level3 success.

This is the "school field" where the PPO learns to follow a reference.

### 2. Gate-Aperture Mini Environment

Use this after free-space tracking is stable:

- `gate_aperture_reference`

Design requirements:

- one synthetic or controlled gate/aperture;
- start with no obstacle;
- later add one simple obstacle or clearance constraint if needed;
- reference sequence should be:

```text
pre-gate align point
-> aperture / safe crossing point
-> post-gate recovery point
```

Promotion requires valid plane crossing through the aperture plus post-gate
recovery, not just getting close to the gate.

### 3. Level3 Planner-Integration Smoke

Use this only after the tracker passes free-space and gate-aperture mini tasks.

Requirements:

- use unchanged `config/level3.toml`;
- use the upper planner to produce local references;
- use the PPO tracker as the only action source;
- evaluate seeds at least `101-120`;
- report first-gate progress, gate-0 pass count, early termination, finite
  observation/action checks, and `config/level3.toml` unchanged check.

This is an integration test, not the first tracker-learning exam.

## Acceptance Logic

Do not approve long planner-driven Level3 training until:

1. Free-space tracker tasks are checkpoint-backed and stable.
2. Braking tasks show low terminal speed and bounded overshoot.
3. Multi-point/L/curve/zigzag tasks show smooth action deltas.
4. Gate-aperture mini task shows valid crossing or clear phase completion.
5. Planner smoke on unchanged `config/level3.toml` has majority first-gate
   progress and at least one gate-0 pass.

If these are not true, write a hold packet instead of launching long training.

## Plain Chinese Summary

不要一开始就让底层 PPO 在完整 Level3 里学。完整 Level3 同时有门、障碍物、
随机赛道、过门逻辑和终止条件，对一个还不会稳定跟点的底层控制器太难。

正确顺序是：

```text
先在空场学会跟点、刹车、转弯
再在单门小环境里学会对准和穿过 aperture
最后才接上 planner 回到 unchanged level3.toml 做真实 smoke
```

这样做不等于修改比赛赛道。比赛目标仍然是 `config/level3.toml`，只是给底层
PPO 一个更干净的训练学校。
