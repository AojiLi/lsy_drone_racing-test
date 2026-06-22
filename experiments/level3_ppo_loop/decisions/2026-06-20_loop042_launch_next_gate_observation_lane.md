# Main-Agent Decision After loop042

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch:

`v6_next_gate_localobs_warmstart`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue loop042 unchanged.
- Do not run another soft-centerline reward-number nudge.
- Keep reward/PPO/controller parameters at the loop020 frontier values for the
  first v6 screen.
- Change only the local observation semantics for the second gate block:
  nearest non-target gate becomes race-order next gate.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m`

loop042 failed its rollback gates:

- Success rate: `0.05`
- Mean successful time: `4.96s`
- Crash rate: `0.95`
- Mean gates: `1.00`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

Additional diagnostics:

- loop042 action-scaling parity: clean.
- loop042 train/inference observation/event parity: clean.
- Remote `origin/main` checkpoint audit:
  `level3_localobs_safer_finetune_from_final_highcrashpenalty_final.ckpt`
  scored `0.10` success, `0.90` crash, `1.15` mean gates, smoother actions,
  but did not beat loop020.

## Main-Agent Rationale

The analyzer's automatic gate-acquisition parameter suggestion should not be
taken as-is because loop041 already tested a similar stronger acquisition
direction and regressed.

The useful signal after loop042 is narrower:

- v5 reward/controller variants repeatedly plateau at `0.10`-`0.15` success.
- Smoothing/safety can reduce saturation but does not create pass conversion.
- Parity checks are clean, so the issue is not an obvious train/inference
  mismatch.
- The v5 observation's nearest-other gate can be a Level3 distractor because
  it is not necessarily the next race gate.

Therefore the next falsifiable structural test is to keep the v5 local
observation dimensionality but replace nearest-other gate semantics with the
race-order next gate.

## Structural Lane

Name:

`v6_next_gate_localobs_warmstart`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-20_loop042_next_gate_observation_synthesis.md`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_next_gate_2obs_local_history_v6`
- Warm-start:
  v5-to-v6 allowed only when actor and critic first-layer input dimensions
  match exactly.
- Reward structure: `legacy_staged`
- PPO/network settings: loop020 frontier values.
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`

## Promotion And Rollback

Promote or mature if hard eval beats loop020 on at least one primary frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Reject or hold if:

- success stays `<=0.10`; or
- mean gates stay below `1.45`; or
- crash stays `>=0.95`; or
- W&B gate/pass conversion stays flat while PPO diagnostics are stable.

If this screen is promising but not target-meeting, continue the same hypothesis
toward 60M under the Level2 step-curve policy and evaluate intermediate
checkpoints. Do not assume final checkpoint is best.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v6_next_gate_localobs_warmstart \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop042_next_gate_observation_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop042_launch_next_gate_observation_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
