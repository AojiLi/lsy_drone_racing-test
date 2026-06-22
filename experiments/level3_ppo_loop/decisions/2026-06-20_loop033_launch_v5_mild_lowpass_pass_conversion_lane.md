# Main-Agent Decision After loop033

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Named next lane:

`v5_mild_lowpass_pass_conversion_controller`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue
  `level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m`
  unchanged.
- Do not promote or mature loop033 toward 60M-90M.
- Use loop020 25M as the trusted parent/global-best checkpoint.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m`

Best loop033 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m/level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m_step_010000000.ckpt`
- Success rate: `0.05`
- Mean successful time: `7.24s`
- Crash rate: `0.95`
- Mean gates: `1.10`
- Command tilt over-limit fraction: `0.508806638074582`

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

- loop033 is better than loop032 but worse than loop020.
- It does not deserve continuation or maturation unchanged.
- The active rollback anchor should remain loop020 25M.

W&B/PPO diagnostics:

- loop033 changed the PPO pressure profile in the intended direction:
  - `approx_kl` tail mean rose to about `0.0061`;
  - `clipfrac` tail mean rose to about `0.0212`;
  - entropy dropped to about `4.03`;
  - hard-eval command tilt over-limit dropped to about `0.509`.
- The change did not convert into durable pass/finish behavior:
  - `passed_gate_rate` and `finished_rate` stayed weak/flat;
  - 15M and final checkpoints returned to `0.0` success.

Structure/research synthesis:

- Do not use the analyzer's generic reward-number recommendation directly.
- The same gate-acquisition reward rebalance was already tested in loop027 and
  regressed: `0.05` success, `0.8` mean gates, and command tilt over-limit
  about `0.826`.
- The next lane should directly test saturation control plus pass conversion,
  while keeping v5 observation and hard eval on the unchanged Level3 track.

## Rejected Next Moves

Rejected:

- continue `v5_ppo_pressure_entropy_saturation_guard`;
- mature loop033 to 60M-90M;
- restart no-wrapper curriculum from loop032;
- repeat the loop027 gate-acquisition reward rebalance;
- change Level3 track geometry or randomization.

## Next Lane

Name:

`v5_mild_lowpass_pass_conversion_controller`

Proposal:

`structural_v5_mild_lowpass_pass_conversion_controller_20m`

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
- `learning_rate=0.0003`
- `update_epochs=5`
- `num_minibatches=8`
- `ent_coef=0.02`
- `target_kl=0.03`
- `hidden_dim=256`
- `n_obs=2`

Controller/training-structure change:

- `action_lowpass_alpha=0.65`

Rationale:

- loop020 has the best pass conversion but high command saturation.
- loop025 showed that strong low-pass filtering (`0.35`) reduced saturation but
  was too restrictive.
- loop033 showed that lower entropy/update pressure reduced saturation but did
  not preserve pass conversion.
- A milder checkpointed low-pass (`0.65`) is the smallest controller lane that
  tests saturation control while preserving more action authority than loop025.

## Promotion And Rollback

Promote or mature only if a hard-eval checkpoint shows at least one:

- success rate above loop020: `>0.15`;
- mean gates above loop020: `>1.45`;
- same success with materially lower crash or command saturation.

Reject if:

- best success remains `<0.15`;
- crash stays `>=0.95`;
- mean gates stay below `1.45`;
- command tilt improves but pass/finish conversion does not improve;
- W&B gate/reward proxies rise without hard-eval progress.

## Required Command Shape

Dry-run first, then run exactly one train/evaluate chunk:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_mild_lowpass_pass_conversion_controller \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_033_structural_v5_ppo_pressure_entropy_saturation_guard_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_loop032_domain_gap_saturation_diagnosis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop033_launch_v5_mild_lowpass_pass_conversion_lane.md
```

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```
