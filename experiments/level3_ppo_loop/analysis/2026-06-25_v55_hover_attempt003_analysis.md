# v55 Hover Attempt003 Analysis

Date: 2026-06-25

Stage: `hover`

Run: `v55_tracker_hover_airborne_error_curriculum_attempt003`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/710kgymu`

## Result

Attempt003 did not pass the hover gate. It fixed the late crash collapse seen
in attempt002, but it did not learn accurate hover tracking.

| Checkpoint | Success | Crash | Mean error | P90 error | Mean speed | Action delta |
|---|---:|---:|---:|---:|---:|---:|
| `250k` | `0%` | `100%` | `0.611m` | `1.554m` | `0.974m/s` | `0.0033` |
| `500k` | `0%` | `0%` | `1.572m` | `2.370m` | `0.451m/s` | `0.0015` |
| `750k` | `0%` | `0%` | `1.124m` | `1.609m` | `0.312m/s` | `0.0019` |
| `final` | `0%` | `0%` | `1.150m` | `1.397m` | `0.236m/s` | `0.0020` |

Best diagnostic checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_airborne_error_curriculum_attempt003_final.ckpt
```

It is not stage-qualified: `success_rate=0`, `mean_position_error_m=1.1500`,
`p90_position_error_m=1.3975`, and `mean_speed_mps=0.2361`.

## Diagnosis

The airborne/error curriculum made the policy safer by the final checkpoint,
but not more accurate. The deterministic policy stabilizes far from the target
instead of returning to the hover anchor.

W&B PPO diagnostics do not show primary PPO explosion:

```text
approx_kl ~= 0.004
clipfrac ~= 0.037
entropy ~= 0.788
explained_variance ~= 0
value_loss final ~= 844
```

The value function is not fitting the dense long-horizon return, and the policy
is learning survival/smoothness more readily than local hover control.

A read-only PD feasibility probe found that a simple hand-written hover PD
controller can solve the same free-space hover config, so the environment and
action semantics are solvable. PPO from scratch is not discovering the local
servo mapping quickly or reliably enough.

## Three-Review Synthesis

- `tracker_eval_metrics`: attempt003 is worse than attempt002's best at target
  tracking; final is safe but far from the target.
- `tracker_wandb_ppo`: KL/clip are modest, but value learning is essentially
  broken and reward scale/curriculum remain poor.
- `tracker_structure_research`: use a PD/supervised warmstart before another
  PPO chunk.

## Decision Input

Do not unlock `point_hold`.
Do not spend the 5M extension as-is.
Do not switch first to `256 x 128`.

Next action should be `v55_tracker_hover_pd_warmstart_attempt004`: behavior
clone a feasible hover PD teacher, evaluate the BC checkpoint, then PPO
fine-tune from that checkpoint only if the warmstart is checkpoint-backed and
finite.
