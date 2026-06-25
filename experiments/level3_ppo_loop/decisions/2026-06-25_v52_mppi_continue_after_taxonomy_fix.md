# Decision: Continue V52 MPPI After Taxonomy Fix

Date: 2026-06-25

Decision: `continue_same_hypothesis`

Lane: `v52_mppi_oracle_teacher_level3`

Analysis packet:
`experiments/level3_ppo_loop/analysis/2026-06-25_v52_mppi_post_gate_prealign_taxonomy_analysis.md`

## Decision

Continue MPPI-only controller tuning. Do not launch PPO training, BC, DAgger,
imitation learning, teacher dataset generation, PPO fine-tuning, or full
`validation_unseen 101-200` yet.

## Evidence

Retained smoke result on seeds `101-105`:

- success: `0%`;
- mean gates: `0.80`;
- crash: `100%`;
- finite action rate: `100%`;
- termination reasons: `{"contact": 5}`;
- endpoint classes: `{"gate_side_frame": 2, "near_gate_obstacle": 3}`.

Retained dev result on seeds `1-10`:

- success: `0%`;
- mean gates: `0.20`;
- crash: `100%`;
- finite action rate: `100%`;
- endpoint classes: `{"gate_side_frame": 8, "gate_vertical_frame": 2}`.

This does not beat the current PPO frontier:

- PPO best success: `21%`;
- PPO best mean gates: `1.66`;
- PPO best crash: `79%`.

## Next Action

Keep the MPPI lane active, but treat the current result as a diagnostic
baseline, not as a controller candidate.

The next loop should target a stronger gate-aware MPPI guide:

- explicit gate-frame crossing-speed control;
- frame-aware costs for side/top/bottom contacts;
- obstacle avoidance coupled to feasible gate aperture side selection;
- trace-first debugging before larger seed sweeps.

`config/level3.toml` remains immutable.
