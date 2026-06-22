# Level3 Decision: Mature Loop020 Best After Loop025

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m`
- Best loop025 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m_step_020000000.ckpt`
- Loop025 hard-eval success rate: `0.10`
- Loop025 mean successful time: `5.40s`
- Loop025 crash rate: `0.90`
- Loop025 mean gates: `1.10`
- Target met: no

## Global Best Comparison

Global best remains loop020 25M:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Loop020 metrics:

- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

Loop025 improved smoothness and command tilt, but regressed the hard-eval
frontier:

- Success rate delta: `-0.05`
- Crash rate delta: `+0.05`
- Mean gates delta: `-0.35`
- Mean successful time delta among successes: `-0.966666666666667s`

## Subagent Findings

- `evaluator_metrics`: loop025 should not replace loop020. It has non-zero
  success and good time, so the evaluator-only view permits weak maturation
  from its 20M checkpoint, but this is not a promotion.
- `wandb_ppo_diagnostics`: PPO is stable. Low-pass filtering mechanically
  reduced action volatility, but W&B gate-passage and finish signals did not
  convert. Recommendation: change reward or training numbers rather than
  continue lowpass unchanged.
- `structure_research_synthesis`: reject lowpass as a performance lane and stop
  action-dynamics ablations. The cleanest next move is a training-horizon
  maturation of the actual global best loop020 25M with the loop020 reward
  family and no lowpass/envelope structural change.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Reject `v5_localobs_action_lowpass_90deg` as the next performance lane. Do not
launch more action-envelope or action-lowpass sweeps now. The next experiment
is a training-horizon maturation of the current global best loop020 25M.

This is a training-number/horizon change, not a new observation, controller,
track, or reward-structure change:

- Keep `config/level3_dr.toml` immutable and as the only hard-eval target.
- Keep v5 observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Keep PPO/network settings from loop020.
- Keep loop020 completion-backloaded reward numbers.
- Disable the loop025 lowpass structural change by setting
  `action_lowpass_alpha=1.0`.
- Keep full roll/pitch command authority with `action_rp_limit_deg=90.0`.
- Start from the loop020 25M global-best checkpoint.
- Run a 60M maturation chunk with 5M checkpoint interval and milestone hard
  eval.

## Rationale

- The Level2 step-curve packet says 30M can be insufficient and promising
  branches should be matured toward 60M-90M before rejection.
- The strongest current local branch is loop020, not loop025. It already has
  non-zero success, better mean gates, and lower crash rate than the action
  dynamics ablations.
- Loop025 shows that smoothing commands can reduce volatility, but local hard
  eval says that was not the limiting factor for success.
- W&B/PPO diagnostics do not justify optimizer, network, or PPO hyperparameter
  changes.

## Approved Next Experiment

Name: `v5_loop020_completion_backloaded_maturation_60m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Train/eval chunk:

```text
60M steps, 5M checkpoint interval, milestone hard eval on config/level3_dr.toml
```

Parameter intent:

```text
Use loop020 reward/training numbers.
action_rp_limit_deg=90.0
action_lowpass_alpha=1.0
```

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 60000000 \
  --checkpoint-interval 5000000 \
  --allow-step-curve-maturation \
  --proposal-name v5_loop020_completion_backloaded_maturation_60m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_025_v5_action_lowpass_90deg_from_loop020_25m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_loop020_maturation_after_loop025.md \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param gate_stage_coef=9.0 \
  --param gate_axis_coef=22.0 \
  --param gate_bonus=180.0 \
  --param gate_front_bonus=22.0 \
  --param gate_back_bonus=95.0 \
  --param finish_bonus=300.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
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

- Promote if any checkpoint beats loop020's `15%` success, `1.45` mean gates,
  or `85%` crash rate.
- Mature toward 90M only if 60M improves success, mean gates, or crash rate.
- Reject this maturation path if it stays below loop020 on both success and
  mean gates.
- If rejected, prefer the analyzer's explicit gate-acquisition reward rebalance
  from loop020 over more action-dynamics ablations.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk after this experiment without a new post-run
  analysis and 3-review decision.
