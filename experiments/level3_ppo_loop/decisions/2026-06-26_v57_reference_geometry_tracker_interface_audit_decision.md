# Decision: V57 Interface Audit Proposes Cross-Entry Reference Continuity Fix

## Decision

Do not launch v58 tracker retraining yet.

Propose exactly one planner-interface fix:

```text
v57a_cross_entry_reference_continuity_clamp
```

Decision type:

```text
propose_single_planner_interface_fix
```

## Evidence

The v57 audit used unchanged `config/level3.toml`, seeds `101-120`, 500 steps,
and the fixed v55 zigzag-qualified tracker checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

No PPO training, reward change, observation-layout change, checkpoint change,
algorithm change, MPPI, or `config/level3.toml` edit was performed.

Headline smoke result:

- gate0 pass: `2/20`
- first-gate progress: `19/20`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `level3_toml_diff_clean`: `true`

Key interface findings, excluding terminal contact rows:

- phase3 -> phase4 reference jump median: `0.740m`
- phase3 -> phase4 reference error median: `0.783m`
- phase3 -> phase4 action delta median: `0.727`
- phase3 -> phase4 aperture error median: `0.172m`
- phase3 -> phase4 gate-local X median: `-0.330m`
- phase4 desired speed: `0.32m/s`
- near-plane phase4 actual absolute gate-local X speed median: `0.522m/s`
- near-plane phase4 actual absolute gate-local X speed p75: `0.695m/s`
- reasonable-cross fast rows: `103/192`

## Diagnosis

Both planner-reference geometry and tracker following are involved.

Planner-reference evidence:

- phase3 -> phase4 always creates an abrupt `0.74m` reference jump;
- the tracker is about `0.78m` from the new reference at the transition;
- action delta spikes at the same transition;
- this command is not yet a gentle, planner-like reference for a low-level
  tracker.

Tracker evidence:

- actual phase4 gate-local X speed stays well above desired speed;
- well-aligned cross rows still often move too fast;
- contact remains `20/20`.

However, the planner-reference issue should be fixed first. The current cross
reference is too abrupt to fairly conclude that the tracker itself is the
primary bottleneck.

## Proposed Fix

Implement one planner-interface change:

```text
v57a_cross_entry_reference_continuity_clamp
```

The change should make phase3 -> phase4 continuous:

- do not jump the current reference by `0.74m` at cross entry;
- initialize the first phase4 reference near the previous phase3 reference;
- roll the reference toward aperture/post-gate over subsequent steps;
- keep desired speed around `0.32m/s`;
- preserve environment `target_gate` transition as the only real pass signal;
- do not enter recover under the same target gate.

## Next Smoke Acceptance

Run the same fixed smoke after the fix:

```text
config/level3.toml
seeds 101-120
500 Level3 steps
same v55 zigzag-qualified tracker checkpoint
```

The next analysis must report:

- phase3 -> phase4 reference jump median below the current `0.740m`;
- phase3 -> phase4 action delta below the current `0.727` median;
- phase4 actual gate-local speed distribution;
- reference-to-drone error near phase3/phase4;
- gate0 pass/contact/early termination;
- phase5 rows and same-target recover rows remain `0`;
- `config/level3.toml` unchanged.

## V58 Gate

Launch `v58_tracker_planner_like_reference_training` only if the continuity
fix produces smooth, reasonable references but the tracker still cannot slow,
brake, or avoid contact.
