# v55 Tracker Stage Gates Established

Date: 2026-06-25

## Why This Exists

The free-space tracker environment should not be trained as one vague task.
Each tracker skill must have a clear completion gate. The loop may only start
the next stage after the current stage has checkpoint-backed evaluation metrics
and all required metrics pass.

Machine-readable gate spec:

```text
experiments/level3_ppo_loop/tracker_qualification_gates.json
```

Checker:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage <stage_id> \
  --metrics-json <stage_eval_metrics.json>
```

For stages after `hover`, add `--require-prerequisites` and pass a history JSON
that marks prior stages as passed.

## Stage Ladder

1. `hover`
   - Exam: can the PPO hold a point without drifting, falling, or shaking?
   - Key gates: high success rate, low crash rate, low position error, low
     speed, smooth actions.
2. `point_hold`
   - Exam: can it reach a target and stay there instead of flying through it?
   - Key gates: final error, terminal speed, overshoot, hold ratio.
3. `point_reach`
   - Exam: can it move from A to B reliably at low speed?
   - Key gates: reach success, final error, overshoot, time to target.
4. `brake_to_point`
   - Exam: can it slow down before the target?
   - Key gates: terminal speed and overshoot. This is critical for the later
     `0.7m-1.0m` observe/slowdown behavior.
5. `line_tracking`
   - Exam: can it follow a straight reference instead of just chasing the final
     point?
   - Key gates: cross-track error, speed error, smoothness.
6. `heading_tracking`
   - Exam: can it align the desired heading without unstable yaw/attitude
     behavior?
   - Key gates: heading error, yaw-rate bound, smoothness.
7. `multi_point_reference`
   - Exam: can it switch between short reference points smoothly?
   - Key gates: segment completion, position error, switch overshoot.
8. `l_shape_tracking`
   - Exam: can it turn a corner without overshooting badly?
   - Key gates: corner completion, cross-track error, corner overshoot.
9. `curve_tracking`
   - Exam: can it follow a smooth curved path?
   - Key gates: path completion, cross-track error, oscillation score.
10. `zigzag_or_lemniscate_tracking`
    - Exam: can it handle sharper references without becoming aggressive?
    - Key gates: path completion, cross-track error, action delta.
11. `gate_aperture_reference`
    - Exam: can it pass a controlled single-gate aperture and recover?
    - Key gates: valid aperture crossing, post-gate recovery, aperture yz
      error, post-gate speed.
12. `planner_integration_smoke`
    - Exam: does the planner+tracker path show real progress on unchanged
      `config/level3.toml`?
    - Key gates: clean `level3.toml` diff, finite actions, majority first-gate
      progress, at least one gate-0 pass, bounded early termination.

## Plain Chinese Summary

这套规则的意思是：

```text
不会悬停，就不能练追点。
不会追点并停住，就不能练直线。
不会直线和刹车，就不能练转弯。
不会转弯和连续点，就不能练单门。
不会单门，就不能接 Level3 planner 做长训练。
```

这样 loop 就不会因为某个 W&B reward 短期上涨而乱跳阶段。每一关都要有
checkpoint、有评估 JSON、有 gate checker 的 pass 结果。

## Current Status

The gate spec and checker are established. No tracker stage is marked passed by
this packet. The next real work is to train/evaluate `hover` in
`config/level3_tracker_free_space.toml`, produce stage metrics, and run the
checker for `hover`.
