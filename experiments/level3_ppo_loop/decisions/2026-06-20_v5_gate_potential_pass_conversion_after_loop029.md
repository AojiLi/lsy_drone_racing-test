# Main-Agent Decision: Gate-Potential Pass Conversion After loop029

Date: 2026-06-20

## Decision

`launch_named_structural_lane`

Launch `v5_localobs_gate_potential_pass_conversion_30m` as a bounded 30M
screen from the loop028 25M checkpoint.

## Evidence

- Hard eval remains on immutable `config/level3_dr.toml`.
- Global best remains loop020 25M:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
- loop028 25M showed the best gate-potential evidence:
  - success rate: `0.15`
  - mean successful time: `6.046666666666667`
  - crash rate: `0.85`
  - mean gates: `1.15`
  - command tilt over-limit fraction: `0.3620782990064521`
- loop029 60M maturation failed:
  - best checkpoint: `30M`
  - success rate: `0.0`
  - crash rate: `1.0`
  - mean gates: `0.7`
  - final checkpoint mean gates: `0.05`
  - no evaluated checkpoint completed a race
- W&B conversion failed:
  - `race/finished_rate` stayed `0.0`
  - `race/passed_gate_rate` stayed effectively flat
  - `race/gate_stage` improved as a proxy, but hard-eval gate passage regressed

## Reviewer Synthesis

- `evaluator_metrics`: reject loop029 unchanged. All evaluated checkpoints had
  `0%` success and `100%` crash; mean gates decayed after 30M. Do not continue
  toward 90M.
- `wandb_ppo_diagnostics`: PPO did not show optimizer collapse. KL and clipfrac
  were small, entropy and explained variance were usable, and SPS was healthy.
  The issue is reward-to-evaluator conversion.
- `structure_research_synthesis`: the failure is primarily reward-structure
  conversion inside the gate-potential lane. The next move should be a named
  pass-conversion lane, not pure maturation.

Main-agent resolution: keep the v5 observation, controller, PPO settings, and
`gate_potential` reward structure fixed, but retune the active reward numbers
to reduce dense potential pressure and increase true gate-pass/finish pressure.
This tests whether loop028's nonzero-success checkpoint can convert approach
behavior into actual gate passage without returning to high-saturation reward
churn.

## Structural Lane

`v5_localobs_gate_potential_pass_conversion_30m`

Code support:

- `scripts/level3_ppo_loop.py`
  - adds built-in structural hypothesis
    `v5_localobs_gate_potential_pass_conversion_30m`
  - keeps observation layout
    `level3_target_gate_nearest_gate_2obs_local_history_v5`
  - keeps `reward_structure=gate_potential`
  - keeps PPO/training settings unchanged
  - uses a 30M screen with 5M checkpoint intervals

Reward-number changes versus loop029:

- lower dense potential pressure:
  - `gate_stage_coef=7.0`
  - `gate_axis_coef=10.0`
- stronger real pass/finish conversion:
  - `gate_bonus=260.0`
  - `finish_bonus=320.0`
- preserve safety/smoothness pressure:
  - `crash_penalty=60.0`
  - `obstacle_coef=5.0`
  - `cmd_tilt_coef=0.9`
  - `rpy_coef=0.7`
  - `tilt_excess_coef=13.0`

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v5_localobs_gate_potential_pass_conversion_30m \
  --proposal-name v5_gate_potential_pass_conversion_from_loop028_25m_30m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_028_structural_v5_localobs_gate_potential_30m/level3_loop_028_structural_v5_localobs_gate_potential_30m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_gate_potential_pass_conversion_after_loop029.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Stop Or Rollback Conditions

- Stop if hard eval reaches `success_rate >= 0.60` and
  `mean_successful_time <= 7.0s`.
- Reject this lane if the 30M screen has `0%` success, mean gates below
  loop028's `1.15`, or W&B pass/finish conversion remains flat.
- Promote/mature only if it beats loop028 on success or mean gates, or beats
  loop020's mean gates while preserving nonzero success.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
