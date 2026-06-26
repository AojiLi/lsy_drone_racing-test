# v60 brake-ramp dense generator 30M analysis

Date: 2026-06-27

Run:

- W&B run id: `v60_brake_ramp_dense_generator_30m_20260626`
- W&B project: `ADR-PPO-Racing-Level3`
- Checkpoint directory: `lsy_drone_racing/control/checkpoints/v60_brake_ramp_dense_generator_30m`
- Final checkpoint: `lsy_drone_racing/control/checkpoints/v60_brake_ramp_dense_generator_30m/v60_brake_ramp_dense_generator_30m_final.ckpt`
- Stage evaluated: `reference_command_no_gate_reward`
- Fixed eval seeds: `101-120`
- Eval horizon: `500` steps

## Result

No evaluated checkpoint passed the v60 `reference_command_no_gate_reward` stage gate.

The run did learn useful reference tracking: brake/hold and slow-through position
errors improved strongly after 5M-15M. However, later checkpoints achieved that
accuracy with increasingly aggressive action changes and still failed command
semantics:

- `brake_hold_rush_count` stayed far above the required `<= 2`.
- `slow_through_stop_count` rose above the required `<= 2` after 8M.
- `success_rate` never reached the required `>= 0.8`; it was `0.45` at 1M/5M
  and `0.0` from 8M onward.
- Crash rate was `0.0` for all evaluated milestones, so this is not an action
  finite or immediate stability failure.

## Milestone Metrics

| ckpt | success | crash | brake pos | slow pos | brake speed | p90 brake speed | rush | slow speed | stop | action delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1M | 0.45 | 0.00 | 0.393 | 0.346 | 0.120 | 0.402 | 14.70 | 0.227 | 0.00 | 0.002 |
| 5M | 0.45 | 0.00 | 0.254 | 0.239 | 0.071 | 0.134 | 2.20 | 0.229 | 1.30 | 0.016 |
| 8M | 0.00 | 0.00 | 0.153 | 0.122 | 0.038 | 0.151 | 12.90 | 0.268 | 2.20 | 0.154 |
| 10M | 0.00 | 0.00 | 0.143 | 0.122 | 0.040 | 0.115 | 10.95 | 0.247 | 3.85 | 0.422 |
| 15M | 0.00 | 0.00 | 0.114 | 0.085 | 0.038 | 0.120 | 10.40 | 0.275 | 2.90 | 0.449 |
| 20M | 0.00 | 0.00 | 0.290 | 0.112 | 0.088 | 0.154 | 12.90 | 0.278 | 3.55 | 0.529 |
| 25M | 0.00 | 0.00 | 0.189 | 0.089 | 0.064 | 0.119 | 12.05 | 0.273 | 4.65 | 0.565 |
| 29M | 0.00 | 0.00 | 0.111 | 0.079 | 0.055 | 0.143 | 11.30 | 0.274 | 3.95 | 0.633 |
| final | 0.00 | 0.00 | 0.125 | 0.083 | 0.063 | 0.134 | 12.30 | 0.279 | 4.30 | 0.647 |

Stage thresholds:

- `success_rate >= 0.8`
- `crash_rate <= 0.08`
- `mean_brake_hold_position_error_m <= 0.2`
- `mean_slow_through_position_error_m <= 0.24`
- `mean_brake_hold_speed_mps <= 0.16`
- `p90_brake_hold_speed_mps <= 0.28`
- `mean_slow_through_speed_mps` in `[0.18, 0.42]`
- `brake_hold_rush_count <= 2`
- `slow_through_stop_count <= 2`

## W&B Summary

Only local summary metrics were available through the W&B API in this run; API
history returned empty. The local summary at about 29.98M steps was:

- `train/approx_kl`: `0.003866`
- `train/clipfrac`: `0.0410`
- `train/explained_variance`: `0.9663`
- `train/entropy`: `0.6869`
- `tracker/pos_error`: `0.1116`
- `tracker/command_position_error`: `0.1037`
- `tracker/trajectory_cross_track_error`: `0.0945`
- `tracker/desired_speed_error`: `0.0757`
- `tracker/action_delta_penalty`: `0.3387`
- `train/SPS`: `10000`

Training did not show an obvious PPO collapse in the summary. The offline stage
gate exposed a behavioral issue: the policy can reduce reference error, but it
does not satisfy the command-boundary semantics for stable braking and
slow-through behavior.

## Interpretation

This run is useful but should not be promoted to planner integration.

The clean command-only input is not the main blocker. The policy learned to
follow the dense reference trajectory better over time. The failure mode is that
accuracy is bought with high action changes and repeated near-target rush/stop
violations.

The best diagnostic checkpoint is `5M`: it is the closest to satisfying the
semantic counts while still relatively smooth. The best geometric tracking
checkpoints are `15M`, `29M`, and `final`, but they are too aggressive for the
low-level tracker role.

## Recommendation

Do not continue the same v60 30M training as-is.

Before another long run, create a v60b/v61 command-boundary-stability pass:

1. Keep the clean observation layout: self state, reference horizon, desired
   velocity/speed/heading, command masks, last action, and history.
2. Keep reward free of gate, obstacle, aperture, planner phase, and race
   progress terms.
3. Strengthen command-boundary behavior instead of general position chasing:
   brake/hold near-target speed stability, slow-through non-stop behavior,
   transition smoothness, and action delta around command changes.
4. Add W&B metrics for per-command action delta, rush/stop counts, and command
   transition windows so training curves reflect the stage gate.
5. Run a bounded maturation chunk and evaluate milestones again. Prefer
   8M-15M first, then extend only if rush/stop counts are trending down.

Planner integration smoke should remain held until a checkpoint passes
`reference_command_no_gate_reward` or a new explicit decision packet changes the
gate.
