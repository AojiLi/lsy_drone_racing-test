# Decision: Hold v62 Long Training, Launch Learning-Signal Fix

Date: 2026-06-27

## Decision

```text
launch_tracker_structural_fix
```

Do not launch an 8M or longer v62/v60 command-tracker maturation run from the
current configuration.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62_brax_reference_command_tracker_1m_learning_signal.md
```

The formal lane works as a backend:

- `scripts/train_v62_brax_reference_command_tracker.py` exists and ran;
- checkpoint/resume-capable format saved successfully;
- W&B offline logging works;
- milestone checkpoints were produced;
- steady-state speed was about `1.3047M env steps/s`, roughly `32.78x` the
  PyTorch fast path;
- PPO metrics were finite, with final KL `0.000248` and final entropy `3.7046`.

But the learning signal failed:

- deterministic eval reward went from `-3.3313` to `-7.2119`;
- command position error went from `0.5496` to `0.6459`;
- command velocity error went from `0.6065` to `1.5760`;
- cross-track error went from `0.4548` to `0.5189`;
- `has_eval_learning_signal = false`.

## Next Action

Create a v62b learning-signal fix before any long run:

```text
v62b_brax_reference_command_tracker_learning_signal_fix
```

Candidate fixes, in priority order:

1. reduce exploration pressure: lower `initial_log_std`, lower or zero
   `ent_coef`, and/or implement a squashed-action log-prob path so PPO optimizes
   the action actually seen by the environment;
2. add reward scaling or return/value normalization so critic targets are not
   thousands of value-loss units immediately;
3. rerun the same bounded 1M gate with pre/post deterministic eval;
4. only then consider 8M+ maturation.

## Guardrails

- Do not add gate/aperture/race/finish/stage reward.
- Do not add gate/obstacle/planner-phase actor inputs to the clean v60 tracker.
- Do not modify `config/level3.toml`.
- Keep the speed backend on Brax/JAX; SBX remains rejected.
