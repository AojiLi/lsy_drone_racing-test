# V53 Hybrid Level2 Virtual-Gate Tracker Smoke

Date: 2026-06-25

Lane: `v53_completion_first_hybrid_planner_controller`

Controller:

```text
lsy_drone_racing/control/level3_hybrid_planner_controller.py
```

Tracker checkpoint:

```text
lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever/level2_DR_latencyobs_middlemanuever_final.ckpt
```

Hard eval config:

```text
config/level3.toml
```

## What Was Implemented

Implemented the user-approved completion-first stack:

```text
upper planner reference point / reference velocity / desired heading
-> synthetic Level2-style local gate observation
-> stable Level2 PPO tracker
-> [roll, pitch, yaw, thrust]
```

The controller keeps `config/level3.toml` unchanged. It does not train PPO, does
not alter the Level2 checkpoint, and does not record hybrid results as PPO
success.

## Smoke Evidence

Primary smoke:

```text
pixi run -e gpu python scripts/evaluate_level3_controller.py \
  --config level3.toml \
  --controller level3_hybrid_planner_controller.py \
  --seed-start 101 \
  --num-seeds 5 \
  --seed-split-name v53_smoke_101_105_d \
  --out-prefix experiments/level3_ppo_loop/mppi/v53_hybrid_smoke_101_105_d \
  --failure-taxonomy
```

Result:

| Metric | Value |
| --- | ---: |
| episodes | 5 |
| success_rate | 0.00 |
| crash_rate | 0.80 |
| timeout_rate | 0.20 |
| finite_action_rate | 1.00 |
| mean_gates | 0.00 |

Artifacts:

```text
experiments/level3_ppo_loop/mppi/v53_hybrid_smoke_101_105_d_summary.csv
experiments/level3_ppo_loop/mppi/v53_hybrid_smoke_101_105_d_episodes.csv
```

Direct Level2 PPO-on-Level3 control was also checked as a baseline:

```text
experiments/level3_ppo_loop/mppi/v53_level2_direct_level3_smoke_101_105_summary.csv
```

It also scored `0%` success and `0.00` mean gates on the same 5 validation
seeds, mostly by timeout. The hybrid wrapper gets closer to the first gate, but
still fails before converting gate 0.

## Diagnosis

The implementation is loadable and action-finite, but not behavior-clean enough
to promote to dev seeds `1-20`.

Trace inspection on seed `101` showed:

- the controller can take off and approach gate 0;
- it reaches the gate plane neighborhood;
- the failure concentrates at first-gate centerline/collision conversion;
- after making cross more aggressive, it contacts near the first gate instead
  of timing out before the gate.

This means the main blocker is not Python wiring or non-finite actions. The
blocker is planner-to-tracker semantics near the gate opening:

```text
reference point is close enough to pull the drone toward gate 0
but not accurate/stable enough to center the drone through the physical opening
```

## Decision

Do not run dev seeds `1-20` yet. The smoke passed finite-action loading, but it
failed the behavior gate: `0%` success and `0.00` mean gates on seeds `101-105`.

Do not record this as PPO success. This is a non-PPO hybrid-controller smoke
result.

## Next Recommended Work

Continue v53 as an implementation/debug lane, not as a promoted controller.

Recommended next iteration:

1. Add a tighter first-gate pre-cross centering phase that requires local
   `abs(y)` and `abs(z)` margins before commanding a cross reference.
2. During cross, cap closing velocity and keep the reference inside the real
   gate opening until the actual gate pass event occurs.
3. Add a small deterministic trace/debug mode for seeds `101-105` that records
   gate-local position, reference point, phase, and action per step, so future
   adapter changes can be compared without reading ad hoc terminal traces.
4. Re-run smoke only on `101-105`; promote to dev `1-20` only after at least
   nonzero gate progress and no first-gate contact cluster.
