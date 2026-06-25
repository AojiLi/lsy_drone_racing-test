# Decision: Continue V52 MPPI After Velocity Diagnostics

Date: 2026-06-25

Decision: `continue_same_hypothesis`

Lane: `v52_mppi_oracle_teacher_level3`

Analysis packet:
`experiments/level3_ppo_loop/analysis/2026-06-25_v52_mppi_velocity_diagnostics_negative_tuning_analysis.md`

## Decision

Continue MPPI-only controller work. Do not launch PPO training, BC, DAgger,
imitation learning, teacher dataset generation, PPO fine-tuning, or full
`validation_unseen 101-200` yet.

## Evidence

The retained controller baseline still has:

- smoke `101-105`: `0%` success, `0.80` mean gates, `100%` crash;
- dev `1-10`: `0%` success, `0.20` mean gates, `100%` crash.

The newly retained evaluator diagnostics show substantial terminal velocity in
the active gate frame:

- smoke mean `|vx|/|vy|/|vz|`: `1.274 / 0.563 / 0.750 m/s`;
- dev mean `|vx|/|vy|/|vz|`: `1.128 / 0.710 / 0.730 m/s`.

Multiple controller changes were tested and rejected because they failed to
improve smoke/dev gate progress.

## Next Action

Use the new velocity diagnostics to design the next MPPI controller change:

- gate-frame velocity regulation instead of only position aiming;
- frame/contact-aware rollout model that predicts side/top/bottom contact;
- gate-passage handoff that reduces post-gate side-frame crashes.

`config/level3.toml` remains immutable. MPPI success remains MPPI-only
evidence and must not be recorded as PPO success.
