# Main-Agent Decision: Mature v5 Gate-Potential After loop028

Date: 2026-06-20

## Decision

`continue_same_hypothesis`

Continue the `v5_localobs_gate_potential_30m` structural lane from the loop028
25M checkpoint to a 60M maturation chunk.

## Evidence

- Hard eval remains on immutable `config/level3_dr.toml`.
- loop028 best checkpoint:
  - checkpoint:
    `lsy_drone_racing/control/checkpoints/level3_loop_028_structural_v5_localobs_gate_potential_30m/level3_loop_028_structural_v5_localobs_gate_potential_30m_step_025000000.ckpt`
  - success rate: `0.15`
  - mean successful time: `6.046666666666667`
  - crash rate: `0.85`
  - mean gates: `1.15`
  - command tilt over-limit fraction: `0.3620782990064521`
- Global best loop020 remains best overall:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
  - command tilt over-limit fraction: `0.5800860395510893`

loop028 should not replace loop020 because its mean gates are lower, but it
ties success/crash, is faster on successful episodes, and materially reduces
command saturation and tilt.

## Reviewer Synthesis

- `evaluator_metrics`: continue same hypothesis to 60M from loop028 25M.
  loop028 ties loop020 success/crash and improves time, but needs more gate
  progress before promotion.
- `structure_research_synthesis`: continue gate-potential unchanged to 60M.
  The lane is not target-ready, but it gives a cleaner/smaller-command policy
  and should be matured according to the 30M screening rule.
- `wandb_ppo_diagnostics`: PPO health was acceptable and saturation improved,
  but W&B did not yet show a gate-conversion breakthrough. It recommended
  reward-number retuning inside the gate-potential structure.

Main-agent resolution: continue unchanged first. The Level2 step-curve policy
and Level3 loop skill say non-zero-success 30M screens should mature toward
60M before rejection. Tuning reward numbers now would confound whether the
gate-potential structure needs more horizon.

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
  --proposal-name v5_gate_potential_from_loop028_25m_maturation_60m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_028_structural_v5_localobs_gate_potential_30m/level3_loop_028_structural_v5_localobs_gate_potential_30m_step_025000000.ckpt \
  --train-timesteps 60000000 \
  --checkpoint-interval 5000000 \
  --allow-step-curve-maturation \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_028_structural_v5_localobs_gate_potential_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_gate_potential_maturation_after_loop028.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Stop Or Rollback Conditions

- Stop if hard eval reaches `success_rate >= 0.60` and
  `mean_successful_time <= 7.0s`.
- Promote only if the matured branch beats loop020 on success or mean gates.
- If 60M does not improve success or mean gates, reject unchanged
  gate-potential maturation and use the W&B reviewer recommendation: retune
  gate-potential reward numbers toward real gate pass/finish conversion while
  preserving the lower command-saturation profile.
- Do not modify Level3 track geometry or randomization.
