# Level3 PPO Decision: Axis-Dominant Controlled Probe After Loop 006

## Objective

Train `config/level3_dr.toml` toward the evaluator gate:

- Success rate `>= 0.60`
- Mean successful race time `<= 7.0s`

This packet approves one Stage 1 active-reward-only screening chunk. It does
not approve PPO hyperparameter, algorithm, observation, network, curriculum,
training-structure, or new reward-channel changes.

## Local Evidence

Latest evaluated trial: `level3_loop_006_custom_safety_axis_recovery`.

- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_006_custom_safety_axis_recovery/level3_loop_006_custom_safety_axis_recovery_step_020000000.ckpt`
- `success_rate`: `0.0`
- `crash_rate`: `1.0`
- `mean_gates`: `0.70`
- `mean_time_s_success`: `null`
- `cmd_tilt_over_limit_frac`: `0.5880`
- `mean_smooth_penalty_per_step`: `0.0354`

Current global incumbent:

- `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- `success_rate`: `0.0`
- `crash_rate`: `1.0`
- `mean_gates`: `0.85`

006 successfully reduced command tilt and smoothness penalties, but that safety
pressure did not convert into gate traversal or finishes. W&B showed
`race/passed_gate_rate` flat, `race/finished_rate` effectively zero, and
`race/gate_stage` / `race/gate_axis_x` worsening.

## Subagent Consensus

Evaluator review:

- 006 did not improve hard evaluator metrics.
- Keep the global incumbent as the baseline final checkpoint.

W&B/PPO review:

- PPO diagnostics did not show update instability.
- Gate/finish conversion failed despite smoother control.

Reward-only tuning review:

- Reward-only exhaustion is not fully met because only five evaluated
  reward-only trials count: `001`, `002`, `004`, `005`, and `006`.
- `003` was `train_failed` and does not count.

Research/decision review:

- Run one final Stage 1 reward-only screening trial rather than holding.
- Use a distinct axis/stage-dominant gate-acquisition probe.

## Approved Hypothesis

Name: `custom_axis_dominant_controlled_probe`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Intent:

- Test whether the first-gate approach and centerline-axis signal is still
  underpowered.
- Avoid repeating 005's completion-heavy low-pressure setup.
- Avoid repeating 006's safety-heavy recovery setup.
- Avoid `auto_completion_backloaded`, which would overemphasize back/finish
  bonuses before any evaluator success exists.
- Keep moderate safety pressure so the axis probe does not simply recreate the
  aggressive 005 behavior.

Approved active reward parameters:

```text
gate_stage_coef=20.0
gate_axis_coef=40.0
gate_bonus=250.0
gate_front_bonus=8.0
gate_back_bonus=35.0
finish_bonus=200.0
wrong_side_penalty=8.0
crash_penalty=65.0
obstacle_coef=5.5
obstacle_margin=0.20
timeout_penalty=80.0
time_penalty=0.0
act_coef=0.016
d_act_th_coef=0.08
d_act_xy_coef=0.08
cmd_tilt_coef=0.85
rpy_coef=0.75
tilt_limit_deg=40.0
tilt_excess_coef=14.0
```

Disabled reward channels must stay at `0`:

```text
progress_coef=0
near_gate_coef=0
gate_plane_bonus=0
missed_gate_penalty=0
obstacle_clearance_coef=0
```

## Decision Rules After Next 30M Chunk

Continue reward-only tuning only if this chunk produces a concrete evaluator
improvement:

- `success_rate > 0.0`; or
- `mean_gates > 0.85`; or
- `crash_rate < 1.0` with W&B `race/passed_gate_rate` or
  `race/finished_rate` conversion.

If this chunk again has `success_rate == 0.0` and `mean_gates <= 0.85`, treat
Stage 1 reward-only screening as effectively exhausted and move to the formal
structural-escalation review packet. Do not directly modify structure.

## Structural Escalation Status

Structural escalation is not authorized by this packet.

If this final screening run fails to improve evaluator success or mean gates,
the next step is to spawn the full escalation audit set and write a detailed
escalation packet. That packet may discuss structural options, but this run
itself remains active reward-number tuning only.
