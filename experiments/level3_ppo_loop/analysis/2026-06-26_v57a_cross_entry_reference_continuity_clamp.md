# V57A Cross-Entry Reference Continuity Clamp

## Summary

This iteration implemented exactly one planner-interface change:

```text
v57a_cross_entry_reference_continuity_clamp
```

The change clamps the first phase3 -> phase4 cross-entry reference step in
`GeometricSlowGatePlanner` so the current reference advances by at most
`0.28m` instead of jumping about `0.74m`.

No PPO training was launched. Rewards, observation layout, checkpoint, PPO
weights, algorithm, MPPI, and `config/level3.toml` were not changed.

## Builder / Checker Gate

Builder changed only:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`

Checker result:

```text
ALL GREEN
```

Checker evidence:

- required tests: `23 passed, 1 warning`;
- required ruff checks: `All checks passed!`;
- `git diff -- config/level3.toml`: clean;
- diff limited to planner reference continuity and its tests;
- no reward, PPO, observation, checkpoint, MPPI, controller-action, or config
  changes found.

## Implementation

The planner now remembers the previous local `current_local` reference. When
the phase is `cross` and a previous reference exists, it limits the displacement
from the previous reference to:

```text
CROSS_ENTRY_MAX_REFERENCE_STEP_M = 0.28
```

The whole short horizon is shifted with the clamped current point, preserving
the relative spacing of current / next / lookahead. Desired speed stays
`0.32m/s`, and gate-pass semantics remain unchanged: only the environment
`target_gate` transition counts as a real gate pass.

## Commands

Validation before smoke:

```bash
pixi run -e tests pytest tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/control/test_level3_reference_tracker_env.py -q
pixi run -e tests ruff check scripts/check_level3_reference_tracker_smoke.py scripts/evaluate_level3_tracker_stage.py lsy_drone_racing/control/level3_reference_tracker.py lsy_drone_racing/control/level3_reference_tracker_controller.py tests/unit/control/test_level3_reference_tracker_env.py
git diff -- config/level3.toml
```

Smoke:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage planner_integration_smoke \
  --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt \
  --seeds 101-120 \
  --level3-steps 500 \
  --early-termination-step-threshold 50 \
  --trace-output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57a_cross_entry_reference_continuity_clamp_500step_trace.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57a_cross_entry_reference_continuity_clamp_500step_metrics.json
```

Compatibility checker:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage planner_integration_smoke \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57a_cross_entry_reference_continuity_clamp_500step_metrics.json \
  --history-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_required_stage_history_through_zigzag.json \
  --require-prerequisites \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v57a_cross_entry_reference_continuity_clamp_500step_gate.json
```

The compatibility checker passed, but it remains a plumbing check only.

## Smoke Result

- config: unchanged `config/level3.toml`
- checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- seeds: `101-120`
- Level3 steps: `500`
- trace rows: `2455`
- active interface rows, excluding terminal contact rows: `2435`
- all finite: `true`

Headline result:

- gate0 pass: `2/20`, seeds `113, 120`
- first-gate progress: `19/20`
- contact: `20/20`
- early termination: `2/20`
- `level3_toml_diff_clean`: `true`

## V57 Baseline Versus V57A

Key interface metrics exclude terminal contact rows.

| Metric | V57 | V57A |
| --- | ---: | ---: |
| phase3 -> phase4 transition count | 9 | 9 |
| phase3 -> phase4 reference jump median | `0.740m` | `0.280m` |
| phase3 -> phase4 reference error median | `0.783m` | `0.340m` |
| phase3 -> phase4 action delta median | `0.727` | `0.491` |
| phase3 -> phase4 aperture Y/Z error median | `0.172m` | `0.172m` |
| near-plane phase4 abs gate-local X speed median | `0.522m/s` | `0.521m/s` |
| near-plane phase4 abs gate-local X speed p75 | `0.695m/s` | `0.694m/s` |
| reasonable-cross rows | 192 | 190 |
| fast reasonable-cross rows | 103 | 100 |
| gate0 pass | `2/20` | `2/20` |
| contact | `20/20` | `20/20` |
| phase5 rows | 0 | 0 |

## Acceptance Audit

V57A acceptance requirements:

- phase3 -> phase4 reference jump median `<= 0.30m`: passed, `0.280m`;
- phase3 -> phase4 reference error median `<= 0.45m`: passed, `0.340m`;
- phase3 -> phase4 action delta clearly below v57 `0.727`: passed, `0.491`;
- gate0 pass not below `2/20`: passed, `2/20`;
- contact does not worsen: passed, still `20/20`;
- recover-before-real-target-gate-switch remains clean: passed, phase5 rows `0`;
- all actions finite: passed;
- `config/level3.toml` unchanged: passed.

The interface fix worked. It did not convert into better gate pass or contact
outcomes.

## Diagnosis

V57A fixed the abrupt reference jump, so the previous objection to tracker
training is mostly removed. The command entering cross is now much more
continuous:

```text
0.740m jump -> 0.280m jump
0.783m reference error -> 0.340m reference error
0.727 action delta -> 0.491 action delta
```

However, contact remains `20/20`, gate0 pass remains `2/20`, and near-plane
phase4 gate-local X speed is effectively unchanged:

```text
median abs vx: 0.522m/s -> 0.521m/s
p75 abs vx:    0.695m/s -> 0.694m/s
```

This supports the user's earlier hypothesis: after making the route less
abrupt, the remaining bottleneck is likely low-level tracker braking and
planner-like reference following, not another small geometric planner threshold.

## Next Action

Propose launching:

```text
v58_tracker_planner_like_reference_training
```

The v58 goal should train the tracker on planner-like reference segments:

- slow cross-style reference following;
- braking to target;
- short pre -> aperture -> post trajectories;
- low overshoot;
- heading-stable tracking;
- speed reduction from about `0.7m/s` toward `0.25-0.35m/s`.

Do not continue ordinary v56 geometric one-knob tuning unless a future decision
packet identifies a new planner-specific failure not explained by tracker
braking/following.
