# Main-Agent Decision After loop043

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch:

`v7_explicit_phase_progress_localobs`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v6 unchanged.
- Do not apply the analyzer's generic gate-acquisition reward-number retune.
- Keep loop020 reward/PPO/controller values for the first v7 screen.
- Add explicit phase/progress observation features with zero-padded warm-start.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m`

Best loop043 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m_step_020000000.ckpt`
- Success rate: `0.10`
- Mean successful time: `5.220000000000001s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.00`

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
- Reason: loop043 has non-zero success and successful episodes are under
  `7s`.

W&B/PPO diagnostics:

- Recommended `launch_named_structural_lane`.
- Reason: PPO was stable, but pass/finish conversion stayed flat,
  `finished_rate` stayed zero, reward components worsened, and command tilt
  saturation rose.

Structure/research synthesis:

- Recommended `launch_named_structural_lane`.
- Reason: v6 triggered rollback criteria: success stayed `<=0.10`, mean gates
  stayed below `1.45`, and the checkpoint curve did not improve.

## Main-Agent Rationale

The main decision is to launch a new named structural lane, not continue v6.

Reasons:

- loop043 did not beat loop020 on success, mean gates, crash, or score.
- The best v6 checkpoint remained at `0.10` success and `1.00` mean gates.
- v6 command saturation worsened: command tilt over-limit reached `0.77` at
  the best checkpoint and `0.81` at final.
- W&B showed approach signals without pass/finish conversion.
- The v6 packet's rollback rules were triggered.

The next structural hypothesis should add explicit phase/progress information,
while preserving loop020's 68-dimensional v5 behavior as much as possible.

## Structural Lane

Name:

`v7_explicit_phase_progress_localobs`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-20_loop043_phase_progress_observation_synthesis.md`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_phase_progress_2obs_local_history_v7`
- Added features:
  `target_progress`, current gate-frame `x`, `y`, and `z`.
- Warm-start:
  v5-to-v7 allowed only by appending zero-padded first-layer input weights.
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
- mean gates stay near `1.0`; or
- crash stays `>=0.90`; or
- W&B pass/finish conversion stays flat; or
- command tilt saturation keeps rising.

If v7 fails, hold for a broader controller/training-structure review rather
than continuing local observation variants.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --allow-repeat-params \
  --structural-hypothesis v7_explicit_phase_progress_localobs \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_043_structural_v6_next_gate_localobs_warmstart_from_loop020_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop043_phase_progress_observation_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop043_launch_phase_progress_observation_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
