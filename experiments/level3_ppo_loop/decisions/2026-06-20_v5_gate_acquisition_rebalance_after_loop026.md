# Level3 Decision: Gate Acquisition Rebalance After Loop026

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_026_v5_loop020_completion_backloaded_maturation_60m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m`
- Best loop026 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_step_030000000.ckpt`
- Loop026 hard-eval success rate: `0.00`
- Loop026 mean successful time: `None`
- Loop026 crash rate: `1.00`
- Loop026 mean gates: `0.05`
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

Loop026 regressed the frontier:

- Success rate delta: `-0.15`
- Crash rate delta: `+0.15`
- Mean gates delta: `-1.40`
- Mean successful time: no loop026 successes

## Subagent Findings

- `evaluator_metrics`: reject loop026 and do not mature the same training
  horizon hypothesis to 90M. All evaluated checkpoints had `0%` success and
  `100%` crash, and command tilt saturated.
- `wandb_ppo_diagnostics`: reject pure maturation. PPO did not show classic
  optimizer instability, but reward conversion failed, gate/finish signals went
  to zero, and command tilt saturated.
- `structure_research_synthesis`: stop pure horizon extension. The next
  bounded hypothesis should rebalance gate-acquisition reward numbers from the
  loop020 25M global-best checkpoint, with no observation/controller/PPO/track
  change.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Reject `v5_loop020_completion_backloaded_maturation_60m`. Do not continue this
same horizon-only path to 90M.

Launch a bounded 30M reward-number screen:

`v5_loop020_gate_acquisition_rebalance_from_loop020_30m`

This is not a new structural lane:

- Keep `config/level3_dr.toml` immutable and as the only hard-eval target.
- Keep v5 observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Keep PPO/network settings unchanged.
- Keep full action authority and no lowpass:
  `action_rp_limit_deg=90.0`, `action_lowpass_alpha=1.0`.
- Start from loop020 25M global best.
- Change only active reward/training numbers listed below.

## Rationale

- More training alone was tested and failed: 60M produced `0%` success and
  `0.05` mean gates.
- W&B shows gate/finish reward conversion collapsed during long maturation.
- The loop025 lowpass lane improved smoothness but did not improve hard eval.
- The remote stateirving packet still supports the v5 local-obstacle family,
  but local hard eval says the next lever should be reward-number balance for
  gate acquisition, not more blind horizon or action-dynamics ablation.

## Approved Next Experiment

Name: `v5_loop020_gate_acquisition_rebalance_from_loop020_30m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Train/eval chunk:

```text
30M steps, 5M checkpoint interval, milestone hard eval on config/level3_dr.toml
```

Reward/training parameters:

```text
action_rp_limit_deg=90.0
action_lowpass_alpha=1.0
gate_stage_coef=13.0
gate_axis_coef=24.0
gate_front_bonus=5.0
gate_bonus=200.0
gate_back_bonus=35.0
finish_bonus=175.0
wrong_side_penalty=14.0
crash_penalty=50.0
obstacle_coef=4.5
obstacle_margin=0.3
timeout_penalty=80.0
time_penalty=0.02
act_coef=0.012
d_act_th_coef=0.055
d_act_xy_coef=0.055
cmd_tilt_coef=0.75
rpy_coef=0.65
tilt_limit_deg=42.0
tilt_excess_coef=10.0
```

The command explicitly pins loop020-compatible safety and smoothness values so
the trial tests the gate-acquisition rebalance, not an automatic post-loop026
safety retune.

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --proposal-name v5_loop020_gate_acquisition_rebalance_from_loop020_30m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_gate_acquisition_rebalance_after_loop026.md \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param gate_stage_coef=13.0 \
  --param gate_axis_coef=24.0 \
  --param gate_front_bonus=5.0 \
  --param gate_bonus=200.0 \
  --param gate_back_bonus=35.0 \
  --param finish_bonus=175.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=50.0 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.02 \
  --param act_coef=0.012 \
  --param d_act_th_coef=0.055 \
  --param d_act_xy_coef=0.055 \
  --param cmd_tilt_coef=0.75 \
  --param rpy_coef=0.65 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=10.0
```

## Promotion And Rollback

- Promote if hard eval beats loop020's `15%` success, `1.45` mean gates, or
  `85%` crash rate.
- Mature toward 60M only if it has non-zero success with improved mean gates or
  lower crash than loop026 and does not collapse command tilt.
- Reject if success is `0%`, mean gates remain below `1.0`, or command tilt
  saturation repeats.
- If rejected, hold for broader reward-structure/controller review instead of
  launching another automatic reward move.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk after this experiment without a new post-run
  analysis and 3-review decision.
