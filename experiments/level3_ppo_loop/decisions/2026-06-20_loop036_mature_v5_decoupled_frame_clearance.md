# Main-Agent Decision After loop036

Date: 2026-06-20

## Decision

`continue_same_hypothesis`

Continue and mature:

`v5_decoupled_frame_clearance_low_pressure_reward`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not promote loop036 as the global best.
- Do not change observation layout, controller, PPO settings, reward
  structure, or reward numbers in the next chunk.
- Continue from loop036 final checkpoint, not from loop020.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m`

Best loop036 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_final.ckpt`
- Success rate: `0.10`
- Mean successful time: `5.63s`
- Crash rate: `0.85`
- Timeout rate: `0.05`
- Mean gates: `1.40`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Recommended `continue_same_hypothesis`.
- loop036 does not meet the target, but recovered meaningful hard-eval signal:
  `0.10` success, `1.40` mean gates, and `0.85` crash.
- It is worse than loop020, but clearly stronger than loop035.

W&B/PPO diagnostics:

- Recommended `change_reward_or_training_numbers`.
- Reason: W&B still shows weak pass conversion:
  - `race/passed_gate_rate` tail mean about `0.000488`;
  - `race/finished_rate` stayed `0.0`;
  - `race/wrong_side_gate_rate` rose;
  - `reward_components/gate_frame_pressure` tail mean about `-3.38`;
  - `reward_components/gate_plane` tail mean about `0.000824`.
- PPO did not show a classic blow-up, but useful policy movement remains weak.

Structure/research synthesis:

- Recommended `continue_same_hypothesis`.
- loop036 fixed the loop035 failure mode by reducing frame-pressure scale from
  about `-50.78` to about `-3.38`.
- The branch has non-zero hard-eval success and meaningful gate progress, so
  it qualifies for step-curve maturation before rejection.

## Main-Agent Rationale

The main decision is to mature the same hypothesis once before numeric retune.

Reasons:

- The standing Level2 step-curve rule says not to reject a branch with non-zero
  hard-eval success or meaningful gate progress at screening length.
- loop036 is not globally best, but it is competitive with loop020 on crash and
  mean gates while faster on successful episodes.
- The final checkpoint is the best checkpoint inside loop036, which suggests
  the branch did not simply collapse with more training.
- The W&B warning is real, but it is better used as a maturation reject/retune
  criterion after one longer same-hypothesis chunk.

## Next Chunk

Run one bounded maturation chunk:

- Proposal name:
  `v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m`
- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_final.ckpt`
- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Train timesteps: `40_000_000`
- Checkpoint interval: `5_000_000`
- Keep latest params from loop036.
- Use `--structural-hypothesis v5_decoupled_frame_clearance_low_pressure_reward`
  and `--allow-repeat-params` so the orchestrator records the same named lane
  while intentionally keeping parameters unchanged.

This is intended to create an approximate 60M-style evidence point for the
same branch.

## Promotion And Rollback

Promote only if hard eval beats loop020 on at least one primary frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with materially lower crash/timeout or better time.

Reject or retune if:

- success remains `<=0.15` and mean gates remain `<=1.45`;
- success drops to `<=0.05`;
- crash remains `>=0.95`;
- W&B `wrong_side_gate_rate` and `gate_frame_pressure` keep rising while
  pass/finish conversion stays flat;
- command saturation worsens without evaluator conversion.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 40000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_decoupled_frame_clearance_low_pressure_reward \
  --allow-repeat-params \
  --allow-step-curve-maturation \
  --override-state-hold \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_final.ckpt \
  --proposal-name v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop035_launch_v5_decoupled_frame_clearance_lane.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop036_mature_v5_decoupled_frame_clearance.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
