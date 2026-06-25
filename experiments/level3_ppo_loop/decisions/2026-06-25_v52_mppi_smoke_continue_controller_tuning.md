# Decision: Continue V52 MPPI Controller Tuning

Date: 2026-06-25

Decision: `continue_same_hypothesis`

Lane: `v52_mppi_oracle_teacher_level3`

Analysis packet:
`experiments/level3_ppo_loop/analysis/2026-06-25_v52_mppi_oracle_smoke_preflight_analysis.md`

## Decision

Continue MPPI-only controller tuning. Do not start PPO training, BC, DAgger,
imitation learning, teacher dataset generation, or PPO fine-tuning.

## Evidence

The MPPI preflight implementation passed the builder/checker gate and produced
finite actions through the new non-PPO evaluator.

Smoke result on seeds `101-105`:

- success: `0%`;
- mean gates: `0.80`;
- crash: `100%`;
- finite action rate: `100%`;
- best single-seed progress: seed `103` reached gate index `2`;
- termination reasons: `{"contact": 5}`.

This does not beat the current PPO frontier:

- PPO best success: `21%`;
- PPO best mean gates: `1.66`;
- PPO best crash: `79%`.

## Next Action

Improve the MPPI-only controller before any full hard eval or PPO teacher-data
work.

Priority order:

1. stabilize first-gate and second-gate transitions;
2. reduce contact around gate-plane crossing;
3. improve vertical velocity braking near gate height;
4. add post-gate handoff logic;
5. only then scale horizon/sample count and run a larger dev eval.

`config/level3.toml` remains immutable.
