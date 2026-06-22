# Level3 Decision: V5 Completion Safety Recovery After Loop 020

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_020_v5_completion_backloaded_from_loop019_15m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_020_v5_completion_backloaded_from_loop019_15m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_020_v5_completion_backloaded_from_loop019_15m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_020_v5_completion_backloaded_from_loop019_15m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Hard-eval success rate: `0.15`
- Mean successful time: `6.37s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.45`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop020 25M is the new global best by success, crash,
  and mean gates. It improved to `15%` success and `1.45` mean gates, but final
  regressed to `5%` success. Resume from the 25M checkpoint, not final. The
  reviewer prefers reward/training-number changes over unchanged maturation.
- `wandb_ppo_diagnostics`: PPO is not collapsed, but the hard-eval gain came
  with a sharp safety/tilt cost: command tilt over-limit rose to `0.58`,
  tilt-over-limit to `0.218`, mean max command tilt to about `71deg`, and action
  smoothness penalties roughly doubled. Preserve completion pressure but
  restore stronger safety/tilt terms.
- `structure_research_synthesis`: The completion-backloaded v5 lane is the
  strongest local branch and should not be abandoned. Unchanged maturation is
  defensible, but if safety is adjusted the Level3 track and v5 structure must
  remain unchanged.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Keep the v5 observation layout, PPO/training structure, and completion-
backloaded reward shape. Change only safety, tilt, and smoothness reward
numbers to reduce the high-command-tilt behavior that accompanied loop020's
improvement.

This is not a new observation lane, not a PPO hyperparameter change, and not a
track change.

## Rationale

- Loop020 proved the completion-backloaded structure is useful: success rose
  from `10%` to `15%`, mean gates rose from `1.15` to `1.45`, and crash fell
  from `90%` to `85%`.
- The same run showed a safety failure mode: the best checkpoint had high
  command saturation and actual tilt. The final checkpoint then regressed.
- A pure unchanged 60M continuation risks amplifying the same unstable control
  mode.
- The next test should preserve the completion incentive but raise the cost of
  high tilt and abrupt action changes.
- Boundary: do not modify Level3 track geometry or randomization. Final
  acceptance remains hard eval on `config/level3_dr.toml`.

## Approved Next Experiment

Name: `v5_completion_safety_recovery_from_loop020_25m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
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
crash_penalty=60.0
obstacle_coef=5.0
obstacle_margin=0.3
obstacle_clearance_coef=0.0
timeout_penalty=80.0
time_penalty=0.005
act_coef=0.018
d_act_th_coef=0.075
d_act_xy_coef=0.075
cmd_tilt_coef=1.05
rpy_coef=0.9
tilt_limit_deg=40.0
tilt_excess_coef=16.0
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
  --proposal-name v5_completion_safety_recovery_from_loop020_25m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_020_v5_completion_backloaded_from_loop019_15m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_completion_safety_recovery_after_loop020.md \
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
  --param crash_penalty=60.0 \
  --param obstacle_coef=5.0 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.005 \
  --param act_coef=0.018 \
  --param d_act_th_coef=0.075 \
  --param d_act_xy_coef=0.075 \
  --param cmd_tilt_coef=1.05 \
  --param rpy_coef=0.9 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=16.0
```

## Promotion And Rollback

- Promote if hard eval exceeds `15%` success, reduces crash below `85%`, or
  preserves `15%` success while reducing command tilt and actual tilt by a
  meaningful margin.
- If success drops below `10%` or mean gates below `1.15`, reject this safety
  recovery and return to a completion-focused hypothesis.
- If it ties `15%` success with better safety but no gate improvement, require
  a fresh 3-review decision before 60M maturation.
