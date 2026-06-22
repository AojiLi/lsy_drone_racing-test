# Main-Agent Decision After loop041

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch:

`v5_soft_centerline_saturation_guard_pass_conversion`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue loop041 unchanged.
- Do not run another pure soft-centerline reward-number nudge.
- Keep v5 local-obstacle observation layout.
- Keep PPO/network settings.
- Keep reward structure: `soft_centerline_followthrough`.
- Keep full 90-degree action authority.
- Add mild action low-pass: `action_lowpass_alpha=0.65`.
- Start from the current global best loop020 checkpoint.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m`

Best loop041 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m/level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m_final.ckpt`
- Success rate: `0.05`
- Mean successful time: `4.6s`
- Crash rate: `0.95`
- Timeout rate: `0.00`
- Mean gates: `0.85`
- Mean action delta: `0.6610376674044506`
- Commanded tilt over-limit fraction: `0.7464038983326822`

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
- loop041 regressed from loop040 and loop020.
- Hard eval rejects more unchanged maturation.

W&B/PPO diagnostics:

- Recommended `hold_for_more_analysis`.
- PPO was numerically stable, but training signals did not convert.
- `finished_rate` stayed zero, `passed_gate_rate` fell, center-hit nearly
  vanished, and wrong-side/frame-pressure remained high.

Structure/research synthesis:

- Recommended `launch_named_structural_lane`.
- loop041 hit the rollback conditions from the loop040 decision.
- Reward pressure increased action aggression instead of pass conversion.
- Proposed adding a mild saturation guard while keeping soft-centerline reward.

## Main-Agent Rationale

The main decision is to launch a named structural lane.

Reasons:

- loop041 made the reward-number direction worse, so another numeric nudge is
  not justified without a new mechanism.
- loop040 showed the soft-centerline reward structure can recover some
  conversion, so abandoning it immediately is premature.
- The remaining failure signal is action saturation/aggression:
  command tilt over-limit rose to `0.746`, mean action delta rose to `0.661`,
  and crash stayed at `0.95`.
- Prior low-pass screens showed saturation can be reduced, but they used older
  reward structures. This test combines mild low-pass with the current
  soft-centerline reward.

## Structural Lane

Name:

`v5_soft_centerline_saturation_guard_pass_conversion`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-20_loop041_soft_centerline_saturation_guard_synthesis.md`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `soft_centerline_followthrough`
- Action authority: `action_rp_limit_deg=90.0`
- Action low-pass: `action_lowpass_alpha=0.65`
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`

Reward numbers:

- Restore loop040's original soft-centerline numbers.
- Do not use loop041's stronger gate-acquisition retune.

## Promotion And Rollback

Promote or mature only if hard eval beats loop020 on at least one primary
frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject or hold if:

- success stays `<=0.10`; or
- mean gates stay below `1.45`; or
- crash stays `>=0.95`; or
- pass/center-hit metrics stay flat while wrong-side/frame pressure remains
  high.

If this lane fails, hold for deeper observation/controller redesign rather than
launching another automatic soft-centerline reward-number nudge.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_soft_centerline_saturation_guard_pass_conversion \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_041_v5_soft_centerline_gate_acquisition_retune_from_loop040_5m_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop041_soft_centerline_saturation_guard_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop041_launch_soft_centerline_saturation_guard_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
