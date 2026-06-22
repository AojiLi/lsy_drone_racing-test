# Main-Agent Decision After loop032

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Named next lane:

`v5_ppo_pressure_entropy_saturation_guard`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue
  `level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`
  unchanged.
- Do not run another no-wrapper curriculum chunk from loop020.
- Keep v5 local-obstacle observations and loop020 reward/action settings fixed
  for this screen.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_analysis.md`
- Diagnosis:
  `experiments/level3_ppo_loop/research/2026-06-20_loop032_domain_gap_saturation_diagnosis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`

Best loop032 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt`
- Success rate: `0.0`
- Mean successful time: `null`
- Crash rate: `1.0`
- Mean gates: `0.8`
- Command tilt over-limit fraction: `0.7672794535902253`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Command tilt over-limit fraction: `0.5800860395510893`

## Reviewer Synthesis

Evaluator metrics:

- Reject loop032 continuation.
- loop032 regressed from loop020 on success, crash rate, mean gates, and
  command saturation.
- The next screen should promote only if it beats the loop020 hard-eval
  frontier or matches success with materially lower crash/saturation.

W&B/PPO diagnostics:

- loop032 shows under-updating and reward-proxy drift:
  - `approx_kl` tail around `0.001133` versus `target_kl=0.03`
  - `clipfrac` tail around `0.000675`
  - tiny policy loss
  - high/rising entropy
  - W&B gate-stage proxy improves while true pass/finish conversion remains
    flat or worse
- A training-structure lane targeting lower entropy and stronger effective
  policy updates is justified.

Structure/research synthesis:

- Do not treat loop032 as a simple hard-eval domain-gap failure; it also failed
  under its own easier no-wrapper training config.
- v5 observation and action-scaling parity are clean, so the next run should
  not spend capacity on wiring fixes.
- Prefer a conservative PPO pressure/entropy lane before a broader
  value-clipping or reward-structure change.

## Next Lane

Name:

`v5_ppo_pressure_entropy_saturation_guard`

Proposal:

`structural_v5_ppo_pressure_entropy_saturation_guard_20m`

Training setup:

- Start from the loop020 global-best checkpoint selected from `state.json`.
- Train config: `level3_dr.toml`.
- Hard eval config: `level3_dr.toml`.
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Train for `20_000_000` steps with `5_000_000` checkpoint interval.
- Use W&B project `ADR-PPO-Racing-Level3`.

Keep fixed from loop020:

- `reward_structure=legacy_staged`
- loop020 completion-backloaded reward numbers
- `action_rp_limit_deg=90.0`
- `action_lowpass_alpha=1.0`
- `hidden_dim=256`
- `n_obs=2`
- `num_minibatches=8`

Training-structure changes:

- `learning_rate=0.0004`
- `update_epochs=6`
- `ent_coef=0.01`
- `target_kl=0.04`

Rationale:

- Increase effective PPO movement while keeping the lane narrow.
- Reduce entropy pressure that may be contributing to saturated, non-converting
  command behavior.
- Keep reward and observation constant so the hard-eval result is attributable
  mainly to PPO update pressure and entropy.

## Promotion And Rollback

Promote or mature only if a hard-eval checkpoint shows at least one:

- success rate above loop020: `>0.15`;
- mean gates above loop020: `>1.45`;
- same success with materially lower crash or command saturation.

Reject if:

- best success remains `<=0.05`;
- mean gates stay below `1.15`;
- crash remains `1.0`;
- command tilt over-limit exceeds `0.65` without evaluator improvement;
- W&B pass/finish conversion stays flat despite proxy reward movement;
- KL/clip fraction spike without hard-eval gain.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_ppo_pressure_entropy_saturation_guard \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop032_domain_gap_saturation_diagnosis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop032_launch_v5_ppo_update_pressure_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
