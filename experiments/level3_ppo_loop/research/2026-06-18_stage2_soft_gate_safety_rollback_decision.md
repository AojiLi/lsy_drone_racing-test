# Level3 PPO Stage 2 Decision: Reject Soft Gate Safety

## Decision

Reject `level3_loop_011_stage2_no_train_wrappers_soft_gate_safety` and hold
training. Keep `level3_loop_010_stage2_no_train_wrappers:15M` as the fragile
global best.

Do not continue from 011 checkpoints and do not follow the automatic analysis
recommendation to keep lowering gate rewards or add time pressure.

## Evidence

011 hard eval on `level3_dr.toml`:

```text
best checkpoint = level3_loop_011_stage2_no_train_wrappers_soft_gate_safety:25M
success_rate = 0.0
crash_rate = 1.0
mean_gates = 0.85
mean_time_s_success = null
```

Current incumbent remains:

```text
level3_loop_010_stage2_no_train_wrappers:15M
success_rate = 0.05
crash_rate = 0.95
mean_gates = 0.8
mean_time_s_success = 5.64
```

011 hit the rollback condition from the 010 decision packet:

- returned to `0%` success
- returned to `100%` crash
- did not show W&B gate/finish conversion

## Subagent Consensus

- Evaluator reviewer: reject 011; keep 010 15M as global best.
- W&B reviewer: no gate/finish conversion, no PPO instability; 011 is not an
  effective soft-gate-safety step.
- Tuning reviewer: hold/rollback; do not immediately open another reward
  adjustment from 011.

## Interpretation

The no-train-wrappers branch remains the only branch that broke zero success,
but the signal is fragile. 011 shows that simply softening gate reward and
raising `cmd_tilt_coef` does not stabilize success.

Next progress should come from a new evidence-backed Stage 2 diagnosis or a
carefully justified return to the 010 parameter set, not from continuing 011.

## Next Action

Hold training. Before the next train/eval chunk, write a new packet that answers
one of:

- why 010 can solve seed 3 but almost no other seeds,
- whether first-gate/second-gate geometry has a narrow failure cluster that can
  be addressed without changing observation or algorithm,
- whether a different narrow training-distribution staging is warranted while
  hard eval remains `level3_dr.toml`.
