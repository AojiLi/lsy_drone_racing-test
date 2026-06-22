# Main-Agent Decision After loop040

Date: 2026-06-20

## Decision

`change_reward_or_training_numbers`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not launch a new structural lane yet.
- Keep v5 local-obstacle observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Keep reward structure: `soft_centerline_followthrough`.
- Keep PPO/network/controller/action authority fixed.
- Start from the best loop040 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_step_005000000.ckpt`.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m`

Best loop040 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_step_005000000.ckpt`
- Success rate: `0.10`
- Mean successful time: `5.390000000000001s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.15`

Later loop040 checkpoints regressed:

- 10M: `0.05` success, `0.95` crash, `0.80` mean gates.
- 15M: `0.00` success, `1.00` crash, `0.80` mean gates.
- Final: `0.05` success, `0.95` crash, `1.10` mean gates.

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Recommended `change_reward_or_training_numbers`.
- loop040 restored non-zero success, but did not beat loop020.
- The best evidence is the 5M checkpoint; longer continuation degraded.

W&B/PPO diagnostics:

- Recommended `change_reward_or_training_numbers`.
- PPO was stable enough: low KL/clipfrac, healthy SPS, and improving explained
  variance.
- W&B showed some approach learning, but weak conversion:
  `passed_gate_rate` stayed flat, `finished_rate` stayed zero, and
  `gate_plane_center_hit_rate` stayed near zero.
- Wrong-side/frame-pressure and crash signals remained too high.

Structure/research synthesis:

- Recommended `change_reward_or_training_numbers`.
- `soft_centerline_followthrough` is not exhausted because it recovered
  non-zero success after direct-aperture failed.
- Do not launch a new structure yet; retune this lane's numbers.

## Main-Agent Rationale

The next move is a bounded retune inside the existing soft-centerline lane.

Reasons:

- The lane produced useful signal: `0.10` success and fast successful episodes.
- It did not beat the global best, so it should not be promoted.
- Continuing unchanged is not justified because 10M/15M/final regressed.
- The failure pattern looks like reward balance drift, not PPO instability:
  approach geometry improves, but centered pass conversion does not.

## Next Trial

Proposal name:

`v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_step_005000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `soft_centerline_followthrough`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`

Parameter changes from loop040:

- `gate_stage_coef`: `10.0 -> 13.0`
- `gate_axis_coef`: `22.0 -> 24.0`
- `gate_front_bonus`: `8.0 -> 5.0`
- `gate_bonus`: `190.0 -> 200.0`
- `gate_back_bonus`: `85.0 -> 35.0`
- `finish_bonus`: `280.0 -> 175.0`
- `missed_gate_penalty`: `6.0 -> 4.0`
- `gate_frame_pressure_coef`: `0.5 -> 0.3`
- `crash_penalty`: `50.0 -> 55.0`
- `obstacle_coef`: `4.5 -> 5.0`
- `time_penalty`: `0.005 -> 0.01`

Intent:

- Strengthen dense gate acquisition.
- Keep front-gate contact small.
- Reduce over-weighted back/finish pressure that appears to degrade later
  checkpoints.
- Keep missed-plane and frame-pressure penalties light.
- Add modest time pressure without optimizing speed before success.
- Slightly restore safety pressure toward the loop020 scale.

## Promotion And Rollback

Promote or mature only if hard eval beats loop020 on at least one primary
frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Mature the same hypothesis toward 60M only if the next run has:

- non-zero hard-eval success and no worse mean gates than loop040; or
- mean gates above `1.45`; or
- W&B pass/center-hit signals improving without higher crash/frame pressure.

Reject or retune again if:

- success remains `<=0.10` and mean gates stay below `1.45`; or
- later checkpoints again degrade after the first 5M checkpoint; or
- `passed_gate_rate`, `gate_pass_hit_rate`, or
  `gate_plane_center_hit_rate` stay flat/down while wrong-side/frame pressure
  rises.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_soft_centerline_followthrough_pass_conversion \
  --proposal-name v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_step_005000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_040_structural_v5_soft_centerline_followthrough_pass_conversion_20m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop040_soft_centerline_reward_number_retune.md \
  --param reward_structure=soft_centerline_followthrough \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param missed_gate_penalty=4 \
  --param gate_frame_pressure_coef=0.3 \
  --param crash_penalty=55 \
  --param obstacle_coef=5 \
  --param time_penalty=0.01
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
