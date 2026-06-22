# Main-Agent Decision: Hold After loop030 Gate-Potential Pass Conversion

Date: 2026-06-20

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Evidence

- Hard eval remains on immutable `config/level3_dr.toml`.
- Global best remains loop020 25M:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
- Best gate-potential checkpoint remains loop028 25M:
  - success rate: `0.15`
  - mean successful time: `6.046666666666667`
  - crash rate: `0.85`
  - mean gates: `1.15`
- loop030 best checkpoint was only 10M:
  - success rate: `0.05`
  - mean successful time: `6.02`
  - crash rate: `0.95`
  - mean gates: `1.1`
- loop030 degraded after 10M:
  - 15M/20M/25M/final all had `0.0` success
  - crash rate stayed `1.0`
  - mean gates stayed in `0.65-0.70`
  - command tilt over-limit rose from `0.46766241312440515` at 10M to
    `0.7606567925988125` at final

## Reviewer Synthesis

- `evaluator_metrics`: do not continue loop030 unchanged. The 10M success is
  real but non-durable; later checkpoints collapse into all-crash behavior with
  rising command tilt.
- `wandb_ppo_diagnostics`: training throughput is fine, PPO does not show a
  hardware/runtime blocker, but W&B gate-stage proxies still do not convert
  into passed gates or finishes. KL/clipfrac are very small, so another blind
  reward scale step risks collecting low-value evidence.
- `structure_research_synthesis`: hold before more training. The analyzer's
  suggested gate-acquisition parameters partly repeat legacy/front/back reward
  terms, but those front/back dense terms are inactive under
  `reward_structure=gate_potential`.

Main-agent resolution: do not launch another immediate gate-potential reward
number step. The next run needs a new source-backed hypothesis packet that
explains why it should beat loop020/loop028 and explicitly states whether it is:

- a return to `legacy_staged` reward numbers,
- a revised `gate_potential` formulation,
- an action/controller/training-structure lane,
- or a different named structural lane.

## Required Next Work

Before any next training command:

1. Write a source-backed research/synthesis packet under
   `experiments/level3_ppo_loop/research/`.
2. Name the next lane or explicit reward/training-number hypothesis.
3. Keep hard eval on `config/level3_dr.toml`.
4. Attach both:
   - `--analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m_analysis.md`
   - `--approved-hypothesis-packet <next main-agent decision packet>`

## Stop Or Rollback Conditions

- Stop if hard eval reaches `success_rate >= 0.60` and
  `mean_successful_time <= 7.0s`.
- Do not continue loop030 toward 60M unless a new packet explains why later
  collapse should not repeat.
- Do not repeat analyzer-suggested front/back dense reward changes inside
  `gate_potential` mode unless the code path is changed so those terms are
  actually active.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
