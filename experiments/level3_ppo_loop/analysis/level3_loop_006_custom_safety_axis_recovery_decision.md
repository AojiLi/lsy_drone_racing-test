# Level3 PPO Main-Agent Decision: level3_loop_006_custom_safety_axis_recovery

## Decision

Hold this hypothesis. Do not continue `custom_safety_axis_recovery` automatically.

The run improved safety and smoothness proxies, but it did not improve the hard
evaluator gate or the main gate-progress proxy. Keep the global incumbent as:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

## Objective

- Config: `config/level3_dr.toml`
- Success target: `>= 0.60`
- Mean successful time target: `<= 7.0s`
- Current tuning stage: Stage 1 active reward numbers only

## Evaluator Evidence

006 best evaluated checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_006_custom_safety_axis_recovery/level3_loop_006_custom_safety_axis_recovery_step_020000000.ckpt
```

Metrics:

- `success_rate`: `0.0`
- `mean_time_s_success`: `null`
- `crash_rate`: `1.0`
- `timeout_rate`: `0.0`
- `mean_gates`: `0.70`
- `score`: `-72.2`
- `cmd_tilt_over_limit_frac`: `0.5880`
- `mean_smooth_penalty_per_step`: `0.0354`

Global incumbent:

- checkpoint: `level3_loop_001_baseline:final`
- `success_rate`: `0.0`
- `crash_rate`: `1.0`
- `mean_gates`: `0.85`
- `score`: `-71.6`

006 is safer than 005 and the baseline on several control proxies, but it is
not a better race policy by the evaluator gate.

## W&B Evidence

W&B run:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_006_custom_safety_axis_recovery
```

Key sampled tail evidence:

- `race/passed_gate_rate`: last `0.010162`, tail mean `0.009598`, trend `flat`
- `race/finished_rate`: last `0.0`, tail mean `0.000031`, trend `flat`
- `race/gate_stage`: last `0.166168`, tail mean `0.179596`, trend `down`
- `race/gate_axis_x`: last `-0.991387`, tail mean `-1.001735`, trend `down`
- `losses/approx_kl`: last `0.000089`, tail mean `0.002047`, trend `flat`
- `losses/clipfrac`: last `0.0`, tail mean `0.003366`, trend `flat`

PPO diagnostics do not show an update explosion. The failure is behavioral:
better control pressure did not convert into gate traversal or finishes.

## Subagent Consensus

Evaluator subagent:

- 006 did not improve hard evaluator metrics.
- Keep the global best as `level3_loop_001_baseline_final.ckpt`.
- Do not continue this hypothesis automatically.

W&B/PPO subagent:

- No W&B conversion into gate/finish behavior.
- PPO diagnostics look stable enough; do not tune PPO hyperparameters.
- Safety/smoothness improved, but did not buy evaluator progress.

Reward-only tuning subagent:

- Reward-only exhaustion is not fully met.
- Countable evaluated reward-only trials: `001`, `002`, `004`, `005`, `006`.
- `003` was `train_failed` and should not count.
- The missing exhaustion gate is the minimum `6` evaluated reward-only trials.
- No next automatic `--param` run recommended without a fresh Stage 1 decision
  packet.

## Structural Escalation Status

Structural escalation is not yet authorized.

Evidence status:

- Evaluated reward-only trials: `5` / required `6`
- Distinct active-reward hypotheses: at least `4` / required `4`
- Evaluated reward-only timesteps: about `180M` / required `120M`
- Consecutive no-improvement evaluated trials: at least `4` / required `4`
- Target success: not met
- W&B conversion: not present in 006

The next action must be one of:

1. Hold for human review; or
2. Run one final Stage 1 active-reward-only screening chunk from the global
   incumbent using a fresh approved decision packet.

Do not change PPO hyperparameters, algorithm, observation layout, network
structure, training structure, curriculum, or add reward channels.
