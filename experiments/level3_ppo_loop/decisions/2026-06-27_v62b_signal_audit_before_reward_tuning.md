# Decision: Fix v62b PPO Signals Before Reward Tuning

Date: 2026-06-27

## Decision

```text
launch_tracker_structural_fix
```

Do not tune v60/v62 tracker reward numbers yet, and do not launch an 8M+ Brax
tracker maturation run from the current settings.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62b_brax_ppo_signal_audit.md
```

The audit found that default v62 PPO signal health is not acceptable:

- default `initial_log_std=-0.5` gives std `0.6065`;
- `34.34%` of actions have at least one clipped dimension;
- raw Gaussian sample logprob and clipped-action proxy logprob differ by
  `0.3427` on average;
- raw advantage mean/std are `-36.41 / 33.90`;
- reward mean is `-3.21`, large enough to trigger a scale warning.

The existing v62 final checkpoint still has the same core problem:

- std about `0.6110`;
- `40.12%` of actions have at least one clipped dimension;
- logprob mismatch mean `0.3968`;
- advantage mean/std `-25.65 / 11.54`;
- deterministic eval learning signal was negative in the prior v62 1M packet.

The same audit with `initial_log_std=-2.0` has clean signal metrics:

- std `0.1353`;
- clipped action fraction `0.0`;
- logprob mismatch `0.0`;
- advantage mean/std `-24.81 / 9.43`;
- reward mean `-2.36`.

## Next Action

Launch a narrow v62b PPO-signal fix:

```text
v62b_brax_ppo_signal_fix_initial_std_and_action_logprob
```

Required properties:

- keep `reference_command_no_gate_reward` unchanged;
- keep observation layout `level3_reference_tracker_command_v3`;
- set or expose `initial_log_std=-2.0`;
- reduce or disable entropy pressure for the first bounded test;
- fix or explicitly audit the action/logprob path so PPO optimizes the action
  distribution that the environment actually sees;
- rerun the same bounded 1M pre/post deterministic eval gate.

If the next 1M run still has no deterministic learning signal after these
checks are clean, then investigate reward scale, return normalization, value
loss scaling, or optimizer settings. Reward tuning is not the first move.

## Guardrails

- Do not add gate/aperture/race/finish/stage reward.
- Do not add gate/obstacle/planner-phase actor inputs to the clean tracker.
- Do not modify `config/level3.toml`.
- Keep the speed backend on Brax/JAX; SBX remains rejected.
- Do not treat generated JSON metrics as source files for git.
