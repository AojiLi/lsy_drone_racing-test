# Decision: Reject V52 Local MPPI Tuning And Launch V53 Controller Redesign

Date: 2026-06-25

Decision: `launch_named_structural_lane`

Completed analysis:
`experiments/level3_ppo_loop/analysis/2026-06-25_v52_mppi_structural_negative_sweep_analysis.md`

## Decision

Stop continuing the current v52 local MPPI guide/cost/sample tuning path.

Launch a new MPPI-only structural lane:

```text
v53_level3_mppi_controller_redesign
```

## Reason

The latest MPPI sweep tested gate-frame velocity control, gate-frame clearance
costs, roll/pitch authority, action response, lower MPPI temperature, larger
sample count, pure pursuit, yaw-aligned acceleration mapping, and multi-branch
guide proposals. None beat the retained v52 baseline:

- retained smoke `101-105`: `0%` success, `0.80` mean gates;
- retained dev `1-10`: `0%` success, `0.20` mean gates;
- all new smoke trials: `0%` success and `<=0.80` mean gates;
- full validation is not justified.

The current MPPI controller is below the PPO frontier and is not a useful
teacher yet.

## V53 Scope

Approved:

- keep the work MPPI/controller-only;
- keep hard eval on unchanged `config/level3.toml`;
- redesign the MPPI/controller architecture around gate-aware geometric
  control, aperture-point selection, and obstacle-aware path proposals;
- run smoke and dev evals before any validation eval.

Not approved:

- changing `config/level3.toml`;
- launching PPO, BC, DAgger, or teacher-data generation;
- recording MPPI-only success as PPO success;
- replaying static seed-specific trajectories.

## Next Action

Implement the smallest v53 controller redesign that first improves first-gate
conversion on smoke/dev. Do not run `validation_unseen 101-200` until smoke or
dev has nonzero success or clearly beats the PPO frontier on mean gates.
