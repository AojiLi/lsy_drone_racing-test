# Level3 Decision: V5 Completion-Backloaded Reward After Loop 019

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_step_015000000.ckpt`
- Hard-eval success rate: `0.10`
- Mean successful time: `5.79s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.15`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop019 ties loop018 on success, crash, and mean gates,
  but it is slower and does not displace the global best. Evaluator evidence
  alone does not justify more automatic reward moves.
- `wandb_ppo_diagnostics`: PPO is stable, but W&B reward gains do not convert
  into hard-eval progress. Passed-gate, finished, crashed, gate-stage,
  centerline, and tilt metrics are flat, while gate-axis worsens. The next move
  should be a new explicit reward/training-number hypothesis rather than
  unchanged maturation.
- `structure_research_synthesis`: The v5 local-obstacle observation and remote
  reward family remain the strongest source-backed structural direction. A
  bounded 60M continuation is defensible only if the same hypothesis is kept,
  but the guardrail should reject it if it does not beat `10%` success,
  `1.15` mean gates, or `90%` crash.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Keep the v5 observation layout and PPO/training structure unchanged, but switch
to a completion-backloaded reward-number hypothesis. This hypothesis tests
whether the current policy is collecting partial gate reward without enough
pressure to complete clean gate traversal.

This is not a new observation lane, not a PPO hyperparameter change, and not a
track change.

## Rationale

- Loop019 preserved `10%` success and cleaner control, but did not improve over
  loop018 on success, crash, or mean gates.
- The analyzer diagnosed `hold_plateau_no_conversion`: no hard-eval
  improvement and no W&B gate/finish conversion.
- Continuing the same remote-scale hypothesis unchanged risks spending another
  long chunk on a plateau.
- A completion-backloaded reward tests a specific failure mode: partial shaped
  reward is too easy relative to full gate traversal and finish reward.
- Boundary: do not modify Level3 track geometry or randomization. Final
  acceptance remains hard eval on `config/level3_dr.toml`.

## Approved Next Experiment

Name: `v5_completion_backloaded_from_loop019_15m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_step_015000000.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Train/eval chunk:

```text
30M steps, 5M checkpoint interval, milestone hard eval on config/level3_dr.toml
```

Approved reward numbers:

```text
progress_coef=0.0
gate_stage_coef=9.0
gate_axis_coef=22.0
near_gate_coef=0.0
gate_bonus=180.0
gate_front_bonus=22.0
gate_plane_bonus=0.0
gate_back_bonus=95.0
finish_bonus=300.0
missed_gate_penalty=0.0
wrong_side_penalty=14.0
crash_penalty=50.0
obstacle_coef=4.5
obstacle_margin=0.3
obstacle_clearance_coef=0.0
timeout_penalty=80.0
time_penalty=0.005
act_coef=0.012
d_act_th_coef=0.055
d_act_xy_coef=0.055
cmd_tilt_coef=0.75
rpy_coef=0.65
tilt_limit_deg=42.0
tilt_excess_coef=10.0
```

PPO/training-structure numbers stay unchanged:

```text
learning_rate=0.0003
gamma=0.99
gae_lambda=0.95
update_epochs=5
num_minibatches=8
ent_coef=0.02
target_kl=0.03
hidden_dim=256
n_obs=2
```

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_completion_backloaded_from_loop019_15m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_step_015000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_completion_backloaded_after_loop019.md \
  --param progress_coef=0.0 \
  --param gate_stage_coef=9.0 \
  --param gate_axis_coef=22.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=180.0 \
  --param gate_front_bonus=22.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=95.0 \
  --param finish_bonus=300.0 \
  --param missed_gate_penalty=0.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.005 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=10.0
```

## Promotion And Rollback

- Promote if hard eval exceeds `10%` success, reduces crash below `90%`, or
  raises mean gates above `1.15` while preserving non-zero success.
- If it only ties `10%` success but has cleaner control and no crash
  regression, require a fresh 3-review decision before any 60M maturation.
- Reject if best hard eval is `0%` success or mean gates below `1.0`.
