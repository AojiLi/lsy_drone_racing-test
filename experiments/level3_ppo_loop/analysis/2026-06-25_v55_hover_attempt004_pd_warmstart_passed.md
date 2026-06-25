# v55 Hover Attempt004 PD Warmstart Analysis

Date: 2026-06-25

Stage: `hover`

Run: `v55_tracker_hover_pd_warmstart_attempt004`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/ohj3vobs`

## Result

Attempt004 passed the hover qualification gate after a PD behavior-cloning
warmstart followed by a 1M-step PPO fine-tune.

| Checkpoint | Success | Crash | Mean error | P90 error | Mean speed | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `BC` | `100%` | `0%` | `0.0595m` | `0.3033m` | `0.0779m/s` | `0.0009` | fail: p90 |
| `250k` | `0%` | `0%` | `0.2620m` | `0.3143m` | `0.1513m/s` | `0.0031` | fail |
| `500k` | `0%` | `0%` | `0.1889m` | `0.2093m` | `0.1210m/s` | `0.0051` | fail |
| `750k` | `0%` | `0%` | `0.1241m` | `0.1410m` | `0.1921m/s` | `0.0147` | fail |
| `final` | `100%` | `0%` | `0.0592m` | `0.0855m` | `0.0347m/s` | `0.0046` | pass |

Best checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_pd_warmstart_attempt004_final.ckpt
```

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_hover_pd_warmstart_attempt004_final_metrics.json
```

## Gate Check

The official hover gate checker passed:

```text
checkpoint_backed: true
all_finite: true
success_rate: 1.0 >= 0.95
crash_rate: 0.0 <= 0.02
mean_position_error_m: 0.05920039489865303 <= 0.12
p90_position_error_m: 0.08545919507741928 <= 0.2
mean_speed_mps: 0.03472756966948509 <= 0.15
mean_action_delta_l2: 0.004586467053741217 <= 0.22
```

Next stage unlocked:

```text
point_hold
```

## Interpretation

The PD warmstart solved the failure mode seen in attempts002/003. BC alone
already produced safe and accurate final hover, but its early acquisition p90
error was still too high. PPO fine-tuning initially disturbed the cloned policy
at 250k/500k, then recovered by the final checkpoint and reduced p90 error well
below the gate threshold.

This means the low-level tracker has now proven its first required ability:
stable hover around a fixed target. It does not yet prove point reaching,
braking, line tracking, curved tracking, or Level3 planner integration.

## Decision Input

Record `hover` as passed, set the current tracker stage to `point_hold`, and
start the next stage from the passing hover checkpoint unless a later decision
packet explicitly chooses a different initialization.
