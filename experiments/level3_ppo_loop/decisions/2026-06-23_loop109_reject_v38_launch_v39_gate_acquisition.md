# Decision: Reject V38 and Launch V39 Gate Acquisition Screen

Decision: `launch_named_structural_lane`

Pending gate resolved by this packet:

- trial:
  `level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_analysis.md`
- subagent synthesis:
  `experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_subagent_reviews.md`

Approved next lane:

```text
v39_feedforward_gate_acquisition_reward_rebalance_loop101_final
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue plain v37/v37b.
- Do not continue v38 as-is.
- Do not start future training from loop109 checkpoints.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

Best loop109 / v38 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_step_001000000.ckpt`
- success: `18/100`
- mean gates: `1.64`
- crash rate: `82%`
- mean successful time: `6.844s`

Dense loop109 milestones:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 0.5M | 18% | 1.63 | 82% | 7.303s |
| 1M | 18% | 1.64 | 82% | 6.844s |
| 1.5M | 17% | 1.64 | 83% | 7.075s |
| final | 13% | 1.57 | 87% | 7.405s |

Reference checkpoints:

- loop107 1M: `21%` success, `1.66` mean gates, `79%` crash, `7.578s`;
- loop101 final: `20%` success, `1.69` mean gates, `80%` crash, `6.873s`.

loop109 did not beat either frontier on success, mean gates, or crash rate.
The faster successful time is on a smaller successful subset and is not a
promotion signal.

## Reviewer Synthesis

- Evaluator reviewer: reject v38; best checkpoint is worse than loop107 1M and
  loop101 final on the primary frontier metrics.
- W&B/PPO reviewer: retention was active and healthy, with sampled batch `512`,
  teacher KL falling to about `0.0096`, action MSE to about `0.00175`, and
  agreement rising to about `0.990`. PPO was conservative, not unstable.
- Structure reviewer: do not continue loop109 or v38 checkpoints. Return to a
  feed-forward frontier checkpoint and test a named gate-acquisition
  reward/training-number screen.

## Approved V39 Scope

`v39_feedforward_gate_acquisition_reward_rebalance_loop101_final`

- Student start:
  loop101 final feed-forward MLP checkpoint.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Policy:
  `mlp_2x_tanh`; no GRU, no retention, no privileged critic.
- Controller:
  end-to-end PPO Actor only.
- Training horizon:
  bounded `5M` screen with `1M` milestone checkpoints.
- Reward/training-number change:
  use the analyzer's gate-acquisition recommendation:
  - `gate_stage_coef=13`
  - `gate_axis_coef=24`
  - `gate_front_bonus=5`
  - `gate_bonus=200`
  - `gate_back_bonus=35`
  - `finish_bonus=175`
  - `time_penalty=0.02`

Everything else should remain at the loop052 remote nominal Level3 values for
the v5 feed-forward baseline.

## Promotion / Rejection Rule

Promote or mature v39 only if hard eval on `validation_unseen` beats the
frontier:

- success `> 21%`, or
- success at least `20%` with mean gates `> 1.69` and crash `<= 80%`, or
- a clear new validation success-seed expansion with no worsening in crash.

Reject v39 if it remains below `20%` success, mean gates stay below `1.69`, or
failure taxonomy remains contact-dominated around `80%+` crash.

## Next Command

After this packet is committed, dry-run then launch:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v39_feedforward_gate_acquisition_reward_rebalance_loop101_final \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop109_reject_v38_launch_v39_gate_acquisition.md
```
