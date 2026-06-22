# Loop058 Subagent Reviews

Date: 2026-06-21

Trial:

`level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m`

Scope:

- Hard eval target remains unchanged: `config/level3_dr.toml`.
- Level3 track geometry and randomization were not modified.
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m`

## evaluator_metrics

Best loop058 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m/level3_loop_058_v8_gate_corridor_obstacle_relative_maturation_from_loop057_25m_60m_final.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.986666666666667s`
- Crash: `0.85`
- Timeout: `0.00`
- Mean gates: `1.20`

Comparison:

- Loop052 global best remains stronger: success `0.20`, crash `0.80`,
  mean gates `1.40`, mean successful time `6.975s`.
- Loop057 25M, the checkpoint matured by loop058, was also stronger on gates
  and time: success `0.15`, crash `0.85`, mean gates `1.40`,
  mean successful time `6.153333333333333s`.

Recommendation:

`launch_named_structural_lane`

Rationale:

The one guarded v8 maturation was justified by loop057, but loop058 did not
improve success or gate progress. Do not continue v8 with more steps.

## wandb_ppo_diagnostics

Key finding:

`hold_plateau_no_conversion`

Evidence:

- Hard eval did not improve: final stayed at success `0.15`, crash `0.85`,
  mean gates `1.20`.
- Milestones did not beat loop052 or loop057: 30M/45M/50M were `0.05`
  success, 55M was `0.10`, final was `0.15`.
- W&B training reward moved the wrong way: `train/total_reward` and
  `train/reward` trended down.
- `passed_gate_rate`, `finished_rate`, `gate_stage`, and
  `gate_plane_cross_rate` stayed flat.
- PPO was calm rather than obviously unstable: tiny `approx_kl`, near-zero
  `clipfrac`, rising entropy, acceptable value diagnostics.
- SPS improved, so throughput is not the blocker.

Recommendation:

`hold_for_more_analysis`

Rationale:

Do not continue v8 from W&B/PPO evidence. Do not make silent PPO-number changes.

## structure_research_synthesis

Key finding:

Reject v8 as a continuation lane. Loop058 was the guarded 60M maturation audit,
and it failed the rollback criteria.

Evidence:

- Loop052 global best remains stronger: success `0.20`, crash `0.80`,
  mean gates `1.40`.
- Loop058 final: success `0.15`, crash `0.85`, mean gates `1.20`,
  mean successful time `6.986666666666667s`.
- Seed-level gate comparison versus loop057 25M:
  - improved on `2 / 20` seeds;
  - worsened on `5 / 20` seeds;
  - unchanged on `13 / 20` seeds.
- W&B conversion stayed flat or down.
- Recent local lanes already tested nominal maturation, gate pressure,
  PPO-pressure, light soft-centerline/plane shaping, and v6/v7/v8 observation
  variants.

Recommendation:

`hold_for_more_analysis`

Rationale:

The next chunk should wait for a new source-backed or local-evidence-backed
structural packet. It should not be another reward-number nudge, PPO-number
nudge, small observation append, or v8 continuation.

## Main-Agent Synthesis Input

Two reviewers recommend `hold_for_more_analysis`; one recommends
`launch_named_structural_lane`, but also agrees v8 must not continue. The
shared conclusion is:

- stop v8 maturation;
- keep loop052 final as the fallback/global-best anchor;
- do not launch another training chunk until a new named structural packet is
  written and approved by the main agent;
- keep hard eval fixed to `config/level3_dr.toml`.
