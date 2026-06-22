# Level3 PPO Main-Agent Decision: level3_loop_001_baseline

## Decision

Run one next bounded iteration with reward-only `gate_acquisition_safety`
overrides.

## Evidence

- Best evaluated checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Success rate: `0.0`
- Mean successful time: none
- Crash rate: `1.0`
- Timeout rate: `0.0`
- Mean gates: `0.85`
- Mean max tilt: `47.36 deg`
- Worst tilt: `143.42 deg`
- Commanded tilt over limit fraction: `0.716`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_001_baseline`

The baseline is far from the hard gate. PPO diagnostics are stable enough to
treat this as a behavior/reward-balance failure rather than an optimizer
failure. The dominant failure is poor gate acquisition with severe crash/tilt
risk. Because no checkpoint has any successful episodes, speed tuning is not
appropriate yet. The next move should primarily emphasize gate acquisition, but
it should also add reward-only safety pressure because evaluator tilt/cmd-tilt
and crash evidence are severe.

## Subagent Consensus

- Evaluator reviewer: not close to target; final checkpoint is best only by
  mean gates, with `0%` success and `100%` crash. Gate acquisition should remain
  the branch, while watching tilt/cmd-tilt closely.
- W&B reviewer: PPO curves look stable; `finished_rate` is zero and
  `passed_gate_rate` remains flat/low, so the evidence points to failed gate
  acquisition rather than PPO instability.
- Tuning reviewer: run one next bounded reward-only gate-acquisition iteration.
- Main-agent dry-run: the loop's metric rule classifies this as
  `gate_acquisition_safety`, which is consistent with the evaluator tilt/crash
  evidence and remains inside the reward-only whitelist.

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout,
  network/training structure, curriculum, or add reward channels.
- Keep disabled reward channels at zero: `progress_coef`, `near_gate_coef`,
  `gate_plane_bonus`, `missed_gate_penalty`, and `obstacle_clearance_coef`.

## Next Reward-Only Overrides

```bash
--param gate_stage_coef=13
--param gate_axis_coef=24
--param gate_front_bonus=5
--param gate_bonus=200
--param gate_back_bonus=35
--param finish_bonus=175
--param time_penalty=0.02
--param crash_penalty=62.5
--param obstacle_coef=5.75
--param act_coef=0.01725
--param d_act_xy_coef=0.0784
--param d_act_th_coef=0.0784
--param cmd_tilt_coef=0.784
--param rpy_coef=0.77
--param tilt_limit_deg=38
```

## Rollback / Stop Condition

Abandon this branch if the next best evaluated checkpoint still has
`success_rate=0.0` and `mean_gates <= 0.85`, or if tilt/cmd-tilt worsens versus
baseline without any success-rate improvement.
