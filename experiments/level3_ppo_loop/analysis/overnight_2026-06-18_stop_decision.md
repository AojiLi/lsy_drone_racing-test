# Level3 PPO Overnight Stop Decision: 2026-06-18

## Decision

Stop / hold the overnight reward-only loop.

The target was not reached, and the latest branch did not produce a clear
reward-only improvement path. Do not launch another training iteration from the
`gate_acquisition_safety` branch without a new human-approved hypothesis.

## Target

- Success rate target: `>= 0.60`
- Mean successful time target: `<= 6.5s`

## Runs Completed

### Trial 001: `level3_loop_001_baseline`

- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_001_baseline`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Success rate: `0.0`
- Mean successful time: none
- Crash rate: `1.0`
- Timeout rate: `0.0`
- Mean gates: `0.85`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_001_baseline_analysis.md`

### Trial 002: `level3_loop_002_gate_acquisition_safety`

- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_002_gate_acquisition_safety`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_002_gate_acquisition_safety/level3_loop_002_gate_acquisition_safety_step_010000000.ckpt`
- Success rate: `0.0`
- Mean successful time: none
- Crash rate: `1.0`
- Timeout rate: `0.0`
- Mean gates: `0.80`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_002_gate_acquisition_safety_analysis.md`

## Why The Loop Stopped

The branch rollback condition from
`experiments/level3_ppo_loop/analysis/level3_loop_001_baseline_decision.md`
was met:

- Trial 002 still had `success_rate=0.0`.
- Trial 002 best `mean_gates=0.80`, which did not improve over the baseline
  best `mean_gates=0.85`.
- Trial 002 still had `crash_rate=1.0`.

W&B proxy metrics improved in trial 002, including training reward and small
changes in pass-rate/tilt proxies, but the evaluator hard metrics did not
improve. The hard gate is evaluator success and time, not W&B reward.

## Subagent Review

- Evaluator reviewer: suggested one more bounded reward-only iteration because
  the target is still far away, but did not provide a new concrete parameter
  hypothesis. It agreed that trial 002 should not replace the global best:
  hard outcomes stayed flat and mean gates slipped from `0.85` to `0.80`.
- W&B reviewer: hold; W&B curves are nicer but do not translate into evaluator
  success or gate-stage improvement.
- Reward-only tuning reviewer: stop/hold; the explicit rollback condition was
  hit.

Main-agent decision: hold. The loop contract requires a clear reward-only next
move before launching another iteration, and two of three reviewers supported
holding after the rollback condition was met.

## Current Incumbent

Keep the global best checkpoint recorded in `state.json`:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

It is still far from target, but it remains the best scored evaluated
checkpoint from the overnight run.

## Next Human Decision

The next useful step is not another automatic continuation of the same branch.
Choose a new hypothesis while preserving the reward-only boundary, or explicitly
approve changing the search space if reward-only tuning is no longer enough.
