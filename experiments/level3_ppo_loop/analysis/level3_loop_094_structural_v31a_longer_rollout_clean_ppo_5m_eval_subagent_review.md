# Loop094 Evaluator Metrics Review

Verdict: do not promote v31a as target-ready. It is a weak positive screen and
eligible only for cautious maturation.

Best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt`

Evidence:

- vs loop093: success `0.17 -> 0.19`, crash `0.83 -> 0.81`, mean successful
  time `7.04s -> 6.88s`;
- mean gates did not improve: `1.55 -> 1.55`;
- final checkpoint regressed to `13/100`, so checkpoint selection must remain
  milestone-aware;
- target remains far away: Wilson upper bound for success is only `0.278`,
  below the required `0.60`.

Failure pattern at the best 4M checkpoint:

- termination reasons: `81 contact`, `19 finish`;
- endpoint classes: `81 bounds_or_ground`, `19 success`;
- failures by target gate: gate 0 `33`, gate 1 `21`, gate 2 `23`, gate 3 `4`;
- compared with loop093, gate 2 improved but gate 1 worsened.

Recommended next action:

`continue_same_hypothesis` only as bounded v31a maturation from the 4M
checkpoint, with milestone hard eval. Do not tune speed and do not modify
`config/level3.toml`.

Rollback condition:

If maturation fails to clear success `>=0.20` and preferably mean gates
`>=1.60`, move to the next structural-support lane rather than more
rollout-only continuation.
