# Main-Agent Decision After loop039

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch:

`v5_soft_centerline_followthrough_pass_conversion`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not promote loop039 as global best.
- Do not continue direct-aperture unchanged.
- Keep v5 local-obstacle observation layout fixed.
- Keep PPO/network/controller/action authority fixed.
- Change only the reward structure to `soft_centerline_followthrough` plus its
  named reward numbers.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m`

Best loop039 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m/level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m_step_015000000.ckpt`
- Success rate: `0.00`
- Mean successful time: `None`
- Crash rate: `1.00`
- Timeout rate: `0.00`
- Mean gates: `1.00`

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

- Recommended `hold_for_more_analysis`.
- loop039 had `0.00` success at every checkpoint.
- loop039 did not beat loop020 on success, crash, or mean gates.
- hard eval alone only proves not to continue/promote direct-aperture.

W&B/PPO diagnostics:

- Recommended `change_reward_or_training_numbers`.
- Direct-aperture did not improve conversion:
  `gate_plane_center_hit_rate` tail about `0.000031`,
  `gate_pass_hit_rate` tail about `0.000122`, and
  `passed_gate_rate` tail about `0.000275`.
- `wrong_side_gate_rate` and `gate_frame_pressure` rose.
- Positive pass/event rewards collapsed while value loss rose sharply.

Structure/research synthesis:

- Recommended `launch_named_structural_lane`.
- Direct-aperture was too sparse and too punitive for this checkpoint family.
- Next lane should be smoother: preserve loop020-style pass/followthrough
  reward while adding softer centerline and plane-crossing feedback.

## Main-Agent Rationale

The main decision is to launch a named structural lane.

Reasons:

- Direct-aperture hit explicit rollback conditions: no success, no improvement
  over loop020, pass/center hit rates flat/down, wrong-side/frame pressure up.
- More training is not justified because there is no non-zero success and no
  mean-gate improvement versus loop020.
- A pure numeric edit inside direct-aperture would still depend on the same
  sparse event definition that collapsed pass rewards.
- The next lane changes only one structural axis: reward structure.

## Structural Lane

Name:

`v5_soft_centerline_followthrough_pass_conversion`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-20_loop039_soft_centerline_followthrough_synthesis.md`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `soft_centerline_followthrough`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- PPO/network/controller/action authority unchanged.

## Promotion And Rollback

Promote or mature only if hard eval beats loop020 on at least one primary
frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject or retune if:

- success remains `0.00`; or
- mean gates stay below `1.00`; or
- W&B `passed_gate_rate`, `gate_pass_hit_rate`, and
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
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_039_structural_v5_direct_aperture_crossing_pass_conversion_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop039_soft_centerline_followthrough_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop039_launch_soft_centerline_followthrough_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
