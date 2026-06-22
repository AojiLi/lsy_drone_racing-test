# Loop083 Decision: Continue V26 Success-Replay Retention To 60M

Decision: continue_same_hypothesis

Pending gate resolved:

- trial_id:
  `level3_loop_083_structural_v26_v23_10m_success_replay_retention_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_083_structural_v26_v23_10m_success_replay_retention_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_083_structural_v26_v23_10m_success_replay_retention_20m_analysis.json`

## Verdict

Do not promote loop083/v26. Keep loop078 final as the global best.

Run one bounded maturation:

`v26_v23_10m_success_replay_retention_maturation_to_60m`

## Evidence

Loop083/v26 best checkpoint was the 15M checkpoint:

- success: 0.20
- mean gates: 2.00
- crash: 0.80
- mean successful time: 7.595s
- successful seeds: 4, 8, 9, 12

Loop078 global best remains better:

- success: 0.25
- mean gates: 2.05
- crash: 0.75
- mean successful time: 8.048s
- successful seeds: 4, 9, 12, 18, 19

The v26 strong claim is not proven. It did not preserve the union of loop078
and v23-10M successful seeds: it recovered 9 and added 8, but lost v23 seed 5
and loop078/v23 seed 18, and did not retain loop078 seed 19.

## Reviewer Findings

Evaluator metrics:

- Reject promotion.
- No checkpoint beats loop078 on success, mean gates, or crash.
- The 15M checkpoint is diagnostic only.

W&B/PPO diagnostics:

- PPO did not show optimizer instability: KL and clip fraction were low, policy
  loss was flat, entropy and explained variance were stable enough.
- Training signals did not reliably convert into hard-eval finish ability:
  finished rate stayed flat, passed-gate rate stayed flat, and crash pressure
  remained high.
- Do not change PPO optimizer hyperparameters silently.

Structure/research synthesis:

- A single continuation is defensible under the step-curve rule because the
  branch has non-zero hard-eval success and mean gates close to the frontier.
- Mature from the loop083 15M checkpoint, not from v23 10M and not from v25.

## Next Lane Contract

- start from loop083 15M checkpoint
- train 45M more steps, reaching a 60M-style horizon for the v26 branch
- keep v8 gate-corridor obstacle observation
- keep 2x256 Tanh MLP actor/critic
- keep v23 decoupled frame-clearance reward settings
- keep training-only profile `loop078_v23_success_replay_lowprob`
- hard eval on unchanged `config/level3_dr.toml`
- checkpoint interval 5M
- W&B project `ADR-PPO-Racing-Level3`

## Stop Rule

If this maturation fails to exceed loop078 final on the hard evaluator, reject
v26 and hold for a new hypothesis. The next branch must not modify Level3 track
geometry, randomization, gates, or obstacles.

