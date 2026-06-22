# Main-Agent Decision: v5 Gate-Potential Lane After loop027

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch `v5_localobs_gate_potential_30m` as the next bounded screening lane.

## Evidence

- Hard eval remains on immutable `config/level3_dr.toml`.
- Global best is still loop020 25M:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
- loop027 did not promote:
  - best checkpoint: `final`
  - success rate: `0.05`
  - mean successful time: `4.6`
  - crash rate: `0.95`
  - mean gates: `0.8`
- loop027 regressed against loop020 despite starting from loop020:
  - lower success
  - higher crash
  - lower mean gates
  - command tilt over-limit increased to `0.8259534779373124`

## Reviewer Synthesis

- `evaluator_metrics`: do not promote loop027 and do not continue it unchanged
  to 60M; it is worse than loop020 on success, crash, and mean gates.
- `wandb_ppo_diagnostics`: PPO did not obviously explode; KL and clipfrac were
  low, explained variance was acceptable, and SPS was healthy. The failure is
  more likely behavioral/reward misalignment. Command tilt saturation remained
  high and did not buy gate passage.
- `structure_research_synthesis`: abandon loop027's coefficient rebalance. The
  next move should be a named structural lane focused on reward-structure or
  controller failure, not blind reward-number churn.

## Structural Hypothesis

`v5_localobs_gate_potential_30m`

Replace the overlapping dense gate rewards with a gate-coordinate
potential-based shaping term:

`r_shape = gamma * phi(s') - phi(s)`

where `phi` penalizes current-stage gate-axis error and gate-centerline error
in the gate coordinate frame.

Keep separate terms for:

- correct gate pass reward
- finish reward
- crash penalty
- obstacle penalty
- time penalty
- action/smoothness/tilt penalties

Drop dense front/back/plane/near/progress reward in this lane by setting those
components to zero under `reward_structure=gate_potential`.

## Implementation Packet

Code support added:

- `lsy_drone_racing/control/train_CleanRL_ppo_level3.py`
  - adds `reward_structure=gate_potential`
  - implements gate-coordinate potential shaping
  - preserves `legacy_staged` behavior as default
- `scripts/level3_ppo_loop.py`
  - adds structural hypothesis `v5_localobs_gate_potential_30m`
  - keeps final hard eval on `level3_dr.toml`

Debug verification:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  --config=level3_dr.toml \
  --train=False \
  --eval=0 \
  --debug_steps=2 \
  --num_envs=4 \
  --jax_device=gpu \
  --observation_layout=level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --reward_structure=gate_potential
```

Result: passed reset/step, emitted 68-dim v5 observations and finite
`gate_stage_progress` potential reward components.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_localobs_gate_potential_30m \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_gate_potential_after_loop027.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Stop Or Rollback Conditions

- Stop if hard eval reaches `success_rate >= 0.60` and
  `mean_successful_time <= 7.0s`.
- Reject this lane if the 30M screen does not improve over loop020 on success
  or mean gates and still shows severe command saturation.
- Do not modify Level3 track geometry or randomization.
