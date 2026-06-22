# Main-Agent Decision After loop042

Date: 2026-06-20

## Decision

`hold_for_more_analysis`

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue loop042 unchanged.
- Do not run another automatic soft-centerline reward-number nudge.
- Do not take the analyzer's gate-acquisition parameter suggestion as-is,
  because loop041 already tested a similar direction and regressed.
- Require a new source/local-evidence packet before launching another named
  observation/controller/reward-structure lane.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m`

Best loop042 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m/level3_loop_042_structural_v5_soft_centerline_saturation_guard_pass_conversion_20m_final.ckpt`
- Success rate: `0.05`
- Mean successful time: `4.96s`
- Crash rate: `0.95`
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
- loop042 failed its own rollback gates:
  success `<=0.10`, mean gates `<1.45`, crash `>=0.95`.
- The single faster successful episode is not enough evidence.

W&B/PPO diagnostics:

- Recommended `hold_for_more_analysis`.
- `action_lowpass_alpha=0.65` reduced command saturation:
  command tilt over-limit improved from loop041 `0.746` to loop042 `0.457`.
- Smoothness improved, but pass conversion did not:
  `passed_gate_rate` and `gate_pass_hit_rate` degraded over the run, center-hit
  stayed tiny, and `finished_rate` remained effectively zero.
- PPO numerics were stable, so the blocker is not obvious optimizer failure.

Structure/research synthesis:

- Recommended `hold_for_more_analysis`.
- Do not continue this hypothesis.
- Do not run another soft-centerline number tweak.
- Next useful work is a deeper observation/controller redesign packet with one
  falsifiable named lane.

## Main-Agent Rationale

The active loop has now tested three adjacent ideas:

- loop040: soft-centerline reward restored some non-zero success but did not
  beat loop020 and degraded after 5M.
- loop041: stronger soft-centerline gate-acquisition numbers worsened hard eval
  and increased command aggression.
- loop042: mild low-pass reduced command saturation but did not restore pass
  conversion or beat loop020.

This is enough evidence to stop automatic train/evaluate chunks for this lane.
The next step should be analysis and design, not another unreviewed 20M chunk.

## Hold Condition

Do not launch another Level3 training chunk until there is a new packet under
`experiments/level3_ppo_loop/research/` or
`experiments/level3_ppo_loop/decisions/` that names one specific next structural
lane and includes:

- the hypothesis being tested;
- the code/config knobs it changes;
- why loop040-loop042 evidence supports it;
- why it is not just another soft-centerline reward-number nudge;
- the initial checkpoint choice;
- hard-eval promotion gates versus loop020;
- rollback criteria.

The next lane may consider observation/controller/reward-structure redesign,
but must keep `config/level3_dr.toml` as the immutable hard-eval target.

## No Next Training Command

No next train/evaluate command is approved by this packet.
