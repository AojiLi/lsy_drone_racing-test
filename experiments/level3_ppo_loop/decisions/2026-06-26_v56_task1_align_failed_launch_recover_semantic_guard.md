# Decision: V56 Task 1 Failed, Repair Recover Semantic Guard

## Decision

Do not promote v56 Task 1. Continue the v56 geometric planner loop, but the next
iteration must repair recover semantics before Task 2 cross-speed tuning.

Next action:

```text
v56_task4_recover_after_environment_target_gate_switch_semantic_guard
```

This is a semantic guard fix, not a PPO/training/reward/checkpoint change.

## Evidence

Task 1 fixed trace support and tightened align-to-cross entry, then ran the
fixed smoke:

- seeds: `101-120`
- steps: `500`
- checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task1_align_stabilization_500step_metrics.json`
- trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task1_align_stabilization_500step_trace.json`

Result:

- gate0 pass: `2/20`, below target `>=10/20`
- first-gate progress: `19/20`, below target `20/20`
- contact: `19/20`, above target `<=8/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml`: unchanged

Baseline comparison:

- baseline gate0 pass was `3/20`
- baseline first-gate progress was `20/20`
- baseline contact was `15/20`

The old `planner_integration_smoke` checker passed, but it is not the v56 gate.
It only proves compatibility with the older smoke contract.

## Subagent Reviews

Builder/checker:

- read-only checker reported `ALL GREEN`;
- no `config/level3.toml` edit;
- no PPO, reward, checkpoint, observation-layout, algorithm, or MPPI change;
- relevant pytest, ruff, and diff checks passed.

Trace metrics reviewer:

- v56 target failed;
- phase-4 cross entries occurred in `9/20` seeds;
- only `2/9` cross-entry seeds passed gate0;
- cross speed remains `0.52 m/s`;
- `gate_local_vx` is now present;
- per-step `aperture_y/z` is still missing, limiting exact cross-entry Y/Z
  error reconstruction.

Semantics reviewer:

- reported `FAILED`;
- seed `106` spent all `500` rows in recover phase with
  `pre_target_gate == post_target_gate == 0`;
- no environment gate switch occurred;
- this violates the v56 rule that same-target recover is forbidden.

Next-hypothesis reviewer:

- recommended Task 2 cross slowdown as the next strategy knob;
- however, it also required `recover_before_gate_switch_count` to be reported
  and stated that nonzero fake recover cannot be promotion evidence.

Main-agent arbitration:

- Task 2 is queued, but not next.
- The recover semantic guard is a hard precondition. Otherwise future speed or
  backout tuning would be evaluated on invalid planner state transitions.

## Guardrails For Next Iteration

Allowed:

- change only `GeometricSlowGatePlanner` recover transition semantics and small
  trace/test support needed to verify it;
- keep the fixed tracker checkpoint;
- keep seeds `101-120`;
- keep `level3_steps = 500`;
- keep hard evaluation on unchanged `config/level3.toml`.

Forbidden:

- PPO training;
- reward changes;
- observation-layout changes;
- tracker checkpoint changes;
- MPPI or planner action output;
- editing `config/level3.toml`;
- custom pass checker driving recover or next-gate logic.

## Acceptance For Next Iteration

The next smoke must report:

- `recover_before_gate_switch_count = 0`
- `fake_recover_count = 0`
- `gate0_pass_count` not worse than Task 1 unless the decision packet explains
  the tradeoff
- `first_gate_progress_count >= 19/20`, with a path back to `20/20`
- `all_finite = true`
- `config/level3.toml` unchanged

V56 final acceptance remains:

- first-gate progress `20/20`
- gate0 pass `>=10/20`
- contact `<=8/20`
- early termination `<=6/20`
- all finite
- unchanged `config/level3.toml`
