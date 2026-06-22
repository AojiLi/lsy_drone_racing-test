# Main-Agent Decision After loop038

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch:

`v5_direct_aperture_crossing_pass_conversion`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not promote loop038 as global best.
- Do not continue loop038 unchanged.
- Keep v5 local-obstacle observation layout fixed.
- Keep PPO/network/controller/action authority fixed.
- Change only the reward structure to `direct_aperture` plus its named reward
  numbers.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m`

Best loop038 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m/level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m_step_015000000.ckpt`
- Success rate: `0.05`
- Mean successful time: `6.14s`
- Crash rate: `0.95`
- Timeout rate: `0.00`
- Mean gates: `1.10`

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
- loop038 best was only `0.05` success and `1.10` mean gates.
- loop038 did not beat loop020's `0.15` success and `1.45` mean gates.
- The successful loop038 episode was fast (`6.14s`), but only one of 20 seeds
  succeeded.

W&B/PPO diagnostics:

- Recommended `change_reward_or_training_numbers`.
- PPO did not blow up: `approx_kl` tail about `0.00416`, `clipfrac` tail about
  `0.00293`, explained variance tail about `0.771`.
- Training signals did not convert: `passed_gate_rate` tail about `0.00360`,
  `finished_rate` tail `0.0`, and `wrong_side_gate_rate` rose.
- Gate event reward components trended down and final hard eval regressed to
  `0.00` success.

Structure/research synthesis:

- Recommended `launch_named_structural_lane`.
- The loop038 reward-number recovery recovered slightly from loop037 but did
  not beat its rollback anchor loop020.
- The next lane should directly reward correct, centered aperture crossing and
  stage-valid gate pass rather than keep tuning front/back/gate bonus numbers.

## Main-Agent Rationale

The main decision is to launch a named structural lane.

Reason:

- loop037 showed that decoupled frame-clearance maturation does not convert.
- loop038 showed that a small rollback reward-number retune still underperforms
  loop020.
- The problem is now more likely reward-structure targeting than insufficient
  training length or PPO instability.
- The next lane changes only one structural axis: reward structure.

## Structural Lane

Name:

`v5_direct_aperture_crossing_pass_conversion`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-20_loop038_direct_aperture_synthesis.md`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `direct_aperture`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- PPO/network/controller/action authority unchanged from loop020-style v5
  screens.

## Promotion And Rollback

Promote or mature only if hard eval beats loop020 on at least one primary
frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject or retune if:

- success remains `0.00`; or
- mean gates stay below `1.00`; or
- W&B `gate_plane_center_hit_rate`, `gate_pass_hit_rate`, and
  `passed_gate_rate` stay flat/down while wrong-side/frame pressure rises.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_direct_aperture_crossing_pass_conversion \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_038_v5_loop020_event_backload_wrongside_recovery_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop038_direct_aperture_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop038_launch_direct_aperture_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
