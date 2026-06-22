# Main-Agent Decision After Loop056

Date: 2026-06-21

## Decision

`hold_for_more_analysis`

## Latest Trial

Trial:

`level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m`

Best loop056 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m/level3_loop_056_v5_loop052_remote_nominal_soft_centerline_light_plane_20m_step_005000000.ckpt`

Metrics:

- Success: `0.15`
- Mean successful time: `6.96s`
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

## Subagent Review Synthesis

`evaluator_metrics`:

- Do not continue loop056.
- Best loop056 checkpoint did not beat loop052.
- If another run is later approved, restart from loop052 final, not loop056.

`wandb_ppo_diagnostics`:

- Abandon the soft-centerline light-plane lane.
- PPO was stable but under-moving; KL and clip fraction were near zero.
- Plane/centerline shaping improved cosmetic distance metrics but did not
  convert into passed-gate, finish, or hard-eval progress.

`structure_research_synthesis`:

- Hold before more training.
- The analyzer's suggested gate-pressure command overlaps with prior failed
  evidence.
- A new source-backed structural hypothesis is required before further
  training.

## Main-Agent Rationale

Loop056 failed its own promotion criteria and matched the rollback shape:

- success stayed below loop052;
- crash stayed worse than loop052;
- W&B `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` stayed
  flat;
- final checkpoint regressed in success.

The analyzer suggested aggressive gate-acquisition numbers, but those numbers
match the already-failed loop051 direction. Loop054 also tested a milder
gate-pressure move from loop052 and failed to beat loop052.

Therefore the loop should not launch another train/eval chunk now. The correct
next action is analysis-only: define a new, non-redundant structural hypothesis
for early-gate survival and pass conversion.

## Required Next Work Before Training

Before any next training command:

1. Keep `config/level3_dr.toml` unchanged.
2. Treat loop052 final as the current fallback checkpoint.
3. Use the taxonomy/episode synthesis packet:
   `experiments/level3_ppo_loop/diagnostics/2026-06-21_loop056_vs_loop052_taxonomy_episode_synthesis.md`
4. Produce a new source-backed structural or training-structure packet that
   explains why the next hypothesis is not a repeat of loop051, loop054,
   loop055, loop056, or older high-scale frame/direct/soft-centerline lanes.
5. Only then attach this decision packet and the new research packet to a dry
   run.

## No Training Command Approved

No next training command is approved by this packet.

