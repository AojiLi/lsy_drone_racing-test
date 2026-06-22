# Level3 Decision: V5 Remote-Scale Rebalance After Loop 018

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_018_v5_gate_acquisition_repair_mature_90m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_018_v5_gate_acquisition_repair_mature_90m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_018_v5_gate_acquisition_repair_mature_90m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_018_v5_gate_acquisition_repair_mature_90m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_018_v5_gate_acquisition_repair_mature_90m/level3_loop_018_v5_gate_acquisition_repair_mature_90m_step_030000000.ckpt`
- Hard-eval success rate: `0.10`
- Mean successful time: `5.25s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.15`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop018 is the new global best on hard eval:
  `10%` success, `1.15` mean gates, `5.25s` successful time, and `90%`
  crash. It improves over loop017, but later loop018 checkpoints regressed;
  final fell to `0%` success and `100%` crash. If continuing the v5 lane, use
  the 30M best checkpoint, not final.
- `wandb_ppo_diagnostics`: PPO does not look collapsed. KL, clip fraction,
  entropy, explained variance, and SPS are acceptable. The failure is
  behavioral conversion: gate and reward signals do not durably convert into
  clean traversal, crash reduction, or finished episodes. Do not silently tune
  PPO internals; change reward/training numbers instead.
- `structure_research_synthesis`: Keep the v5 local-obstacle observation lane.
  It is still the strongest local and remote-supported structural family.
  However, unchanged maturation is no longer justified because 60M, 85M, and
  final regressed. Move the aggressive local repair scale back toward the
  smoother remote v5 reward scale, starting from the loop018 30M checkpoint.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Keep the v5 observation structure and controller path unchanged, but rebalance
reward numbers toward the source-backed remote v5 recipe. This is not a new
observation lane, not a PPO hyperparameter change, and not a track change.

## Rationale

- Local hard eval improved from `5%` to `10%` success, so the v5 lane should
  not be discarded.
- The best checkpoint occurred at 30M while later checkpoints regressed to
  `0%` success. That argues against another unchanged long continuation.
- W&B shows stable PPO but weak conversion: flat passed/finished rates, flat or
  worse gate-axis/stage signals, rising tilt, and late reward decline.
- The stateirving reference packet supports the same v5 observation with a
  lower, smoother reward scale than the current local repair values.
- Boundary: do not modify Level3 track geometry or randomization. Final
  acceptance remains hard eval on `config/level3_dr.toml`.

## Approved Next Experiment

Name: `v5_remote_scale_rebalance_from_loop018_30m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_018_v5_gate_acquisition_repair_mature_90m/level3_loop_018_v5_gate_acquisition_repair_mature_90m_step_030000000.ckpt
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
gate_stage_coef=15.0
gate_axis_coef=15.0
near_gate_coef=0.0
gate_bonus=120.0
gate_front_bonus=4.0
gate_plane_bonus=0.0
gate_back_bonus=20.0
finish_bonus=160.0
missed_gate_penalty=0.0
wrong_side_penalty=6.0
crash_penalty=50.0
obstacle_coef=5.0
obstacle_margin=0.3
obstacle_clearance_coef=0.0
timeout_penalty=80.0
time_penalty=0.03
act_coef=0.03
d_act_th_coef=0.1
d_act_xy_coef=0.1
cmd_tilt_coef=1.0
rpy_coef=1.0
tilt_limit_deg=40.0
tilt_excess_coef=15.0
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
  --proposal-name v5_remote_scale_rebalance_from_loop018_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_018_v5_gate_acquisition_repair_mature_90m/level3_loop_018_v5_gate_acquisition_repair_mature_90m_step_030000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_018_v5_gate_acquisition_repair_mature_90m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_remote_scale_rebalance_after_loop018.md \
  --param progress_coef=0.0 \
  --param gate_stage_coef=15.0 \
  --param gate_axis_coef=15.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=120.0 \
  --param gate_front_bonus=4.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=20.0 \
  --param finish_bonus=160.0 \
  --param missed_gate_penalty=0.0 \
  --param wrong_side_penalty=6.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=5.0 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.03 \
  --param act_coef=0.03 \
  --param d_act_th_coef=0.1 \
  --param d_act_xy_coef=0.1 \
  --param cmd_tilt_coef=1.0 \
  --param rpy_coef=1.0 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=15.0
```

## Promotion And Rollback

- Promote this rebalance if hard eval exceeds `10%` success or reduces crash
  below `90%` while preserving at least `1.15` mean gates.
- If success drops to `0%` or mean gates falls below `0.90`, reject this
  rebalance and require a different reward/training-number hypothesis.
- If it ties `10%` success but improves crash or gates, run a 60M maturation
  from the best checkpoint before rejecting it.
