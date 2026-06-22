# Level3 PPO Main-Agent Decision: level3_loop_002_gate_acquisition_safety

## Decision

Rollback the `gate_acquisition_safety` branch and run one fresh bounded
reward-only iteration from the global best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`

The next hypothesis is `front_alignment_completion_v1`: make the dense gate
axis/stage signal stronger, make the front/back gate events more valuable, add
a wrong-side penalty, and keep speed pressure lower until evaluator success is
nonzero. Add only moderate safety pressure so the policy cannot gain shaped
gate reward through extreme command tilt.

## Evidence

- Latest best evaluated checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_002_gate_acquisition_safety/level3_loop_002_gate_acquisition_safety_step_010000000.ckpt`
- Success rate: `0.0`
- Mean successful time: none
- Crash rate: `1.0`
- Timeout rate: `0.0`
- Mean gates: `0.8`
- Previous/global best mean gates: `0.85`
- Delta vs previous evaluated trial:
  `success_rate=0.0`, `crash_rate=0.0`, `timeout_rate=0.0`,
  `mean_gates=-0.05`
- W&B showed higher train reward, but `race/finished_rate` stayed at zero and
  gate-stage/gate-passage curves did not convert into evaluator success.

The second run improved some tilt extremes but failed its rollback condition:
`success_rate=0.0` and `mean_gates <= 0.85`. It should not be continued as-is.

## Subagent Consensus

- Evaluator reviewer: hard gate is not close; `0%` success, `100%` crash, and
  no measurable successful time.
- W&B reviewer: reward learning did not convert into task behavior; train
  reward improved while gate/finish curves stayed flat and command tilt stayed
  high.
- Tuning reviewer: stop this branch and rollback before choosing a fresh
  reward-only hypothesis.

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout,
  network/training structure, curriculum, or add reward channels.
- Keep disabled reward channels at zero: `progress_coef`, `near_gate_coef`,
  `gate_plane_bonus`, `missed_gate_penalty`, and
  `obstacle_clearance_coef`.

## Next Reward-Only Overrides

These overrides intentionally specify every active reward number so the run
does not inherit the failed second-branch reward balance.

```bash
--param gate_stage_coef=14
--param gate_axis_coef=28
--param gate_front_bonus=10
--param gate_bonus=220
--param gate_back_bonus=45
--param finish_bonus=190
--param wrong_side_penalty=8
--param crash_penalty=55
--param obstacle_coef=5.25
--param obstacle_margin=0.2
--param timeout_penalty=80
--param time_penalty=0.015
--param act_coef=0.015
--param d_act_xy_coef=0.08
--param d_act_th_coef=0.075
--param cmd_tilt_coef=0.9
--param rpy_coef=0.75
--param tilt_limit_deg=38
--param tilt_excess_coef=14
```

## Rollback / Stop Condition

Rollback this hypothesis if the next best evaluated checkpoint still has
`success_rate=0.0` and `mean_gates <= 0.85`, or if W&B again shows rising train
reward with flat `race/passed_gate_rate`, zero `race/finished_rate`, and worse
command-tilt/smoothness behavior.

If this third reward-only hypothesis also fails to improve evaluator mean gates
or success, pause the loop for human review before spending another 20M-step
iteration under the current no-structure-change constraint.
