# Main-Agent Decision After Loop058

Date: 2026-06-21

## Decision

`hold_for_more_analysis`

## Latest Trial

Trial:

`level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m`

Best loop058 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m_final.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.986666666666667s`
- Crash: `0.85`
- Mean gates: `1.20`
- Target met: `false`

Global best remains loop052 final:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Global-best metrics:

- Success: `0.20`
- Mean successful time: `6.975s`
- Crash: `0.80`
- Mean gates: `1.40`
- Target met: `false`

## Required Reviews

Review packet:

`experiments/level3_ppo_loop/analysis/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m_subagent_reviews.md`

`evaluator_metrics`:

- Loop058 final is best inside loop058, but it is worse than loop052 and worse
  than loop057 25M on gate progress.
- Recommendation: `launch_named_structural_lane`.
- Do not continue v8 with more steps.

`wandb_ppo_diagnostics`:

- W&B/PPO evidence shows plateau without conversion.
- Training reward trended down; pass, finish, and gate-plane rates stayed flat.
- PPO was calm, not explosively unstable.
- Recommendation: `hold_for_more_analysis`.

`structure_research_synthesis`:

- Loop058 failed the guarded v8 maturation audit.
- Seed-level gate comparison versus loop057 25M improved on `2/20` seeds,
  worsened on `5/20`, and stayed unchanged on `13/20`.
- Recommendation: `hold_for_more_analysis`.

## Main-Agent Rationale

Loop058 was not a failed short screen; it was the specific maturation audit that
was approved after loop057. It gave v8 the extra step budget requested by the
Level2 step-curve rule. The result did not improve success, crash rate, or mean
gates over the global best.

The v8 hypothesis is therefore rejected as a continuation lane:

- do not continue v8 toward 90M;
- do not restart v8 from loop057 25M again;
- do not make another small v8 observation append without a new packet;
- do not use the analyzer's generic gate-acquisition reward recommendation;
- do not silently change PPO numbers.

The correct fallback anchor is loop052 final.

## Approved Next Action

Hold for more analysis and build a new source-backed or local-evidence-backed
structural packet before any next training command.

The next packet must:

- name the structural lane explicitly;
- state what variable is being changed and what remains fixed;
- cite local evidence from loops 052-058 and relevant source evidence if the
  change is nontrivial;
- keep `config/level3_dr.toml` unchanged for hard eval;
- avoid v4/all-gates unless the user explicitly re-approves it;
- avoid v8 continuation;
- avoid silent reward-number or PPO-number nudges.

Likely analysis directions:

- controller/action parameterization and pass-conversion behavior;
- training-structure changes that directly address early-gate crash and pass
  conversion;
- a deeper architecture/controller lane rather than another small observation
  append.

## No Training Command Yet

No next train/evaluate chunk is approved by this packet.

Before any future training launch:

- write a new structural or tuning packet;
- dry-run the exact `scripts/level3_ppo_loop.py` command;
- use `--max-iterations 1`;
- use W&B under `ADR-PPO-Racing-Level3`;
- attach the loop058 analysis packet with `--analysis-packet`;
- attach the new approved decision/hypothesis packet with
  `--approved-hypothesis-packet`.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not edit `notebooks/train_level3_ppo.ipynb`.
- Do not accept training reward as the target gate.
- Final acceptance remains hard eval on `config/level3_dr.toml` with success
  `>=0.60` and mean successful time `<=7.0s`.
