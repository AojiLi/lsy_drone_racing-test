# Decision: Reject V47, Launch V48 Contact Conversion Reward Structure

Decision: launch_named_structural_lane

Trial resolved:
`level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m_analysis.md`

Subagent review packet:
`experiments/level3_ppo_loop/analysis/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m_subagent_reviews.md`

Next structural lane:
`v48_v5_contact_conversion_reward_structure_from_loop110_3m`

## Decision

Reject v47 as-is. Do not continue from loop117 final, and do not mature the
residual-frontier union retention hypothesis.

Launch exactly one bounded v48 screen. It must keep the final hard eval on
unchanged `config/level3.toml`, start from loop110/v39 3M, keep the deployed
v5 MLP Actor, disable teacher retention, and test the named contact/conversion
reward-structure change documented in:

`experiments/level3_ppo_loop/research/2026-06-23_level3_v48_contact_conversion_reward_structure_plan.md`

## Rationale

v47 proved the retention mechanism was active but did not improve hard eval.
The best checkpoint was 3M with:

- success rate: `20%`;
- mean gates: `1.58`;
- mean successful time: `7.064s`;
- crash rate: `80%`;
- timeout rate: `0%`.

The current global best remains loop107/v37 1M with `21%` success and `1.66`
mean gates. v47 also did not improve the W&B race metrics: passed-gate rate,
finished rate, and gate-stage signals stayed flat or declined while teacher KL,
teacher MSE, and teacher agreement improved. That rules out "retention not
active" as the main explanation.

The remaining failure pattern is contact-heavy and concentrated around gate 0
and gate 2. Therefore the next structural test should target gate conversion
and contact behavior directly rather than adding more teacher retention.

## Guardrails

- Do not edit `config/level3.toml` track geometry, gates, obstacles, or
  randomization.
- Do not add inference-time teacher logic, planner logic, rule controllers,
  safety shields, or ensembles.
- Do not start from loop117 final.
- Do not run `--max-iterations > 1`.
- After v48 completes, run the analyzer and exactly three subagent reviews
  before any next training chunk.

## Promotion / Rejection

Promote v48 only if it beats the current frontier or shows a credible contact
conversion improvement:

- success `>21%`; or
- success `>=21%` with mean gates above `1.66` and crash `<=79%`; or
- lower crash/tilt with no mean-gate loss.

Reject v48 if success stays `<=21%`, mean gates stay `<=1.66`, crash remains
near `79%-80%+`, or frame/contact pressure merely lowers gate acquisition.
