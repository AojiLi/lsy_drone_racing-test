# Loop057 V8 vs Loop052 Episode And Taxonomy Synthesis

Date: 2026-06-21

## Scope

- Target remains hard eval on `config/level3_dr.toml`.
- Level3 track geometry and randomization were not modified.
- This packet compares loop057 v8 25M against the current global best loop052
  final before deciding whether to mature v8.

## Hard-Eval Comparison

Loop052 final:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

- Success: `0.20`
- Crash: `0.80`
- Mean gates: `1.40`
- Mean successful time: `6.975s`

Loop057 v8 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m/level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m_step_025000000.ckpt`

- Success: `0.15`
- Crash: `0.85`
- Mean gates: `1.40`
- Mean successful time: `6.153s`

Interpretation:

V8 does not beat the global best. It ties mean gates and improves successful
episode time, but loses one success seed and has worse crash rate.

## Hard-Eval Seed Comparison

Loop052 final success seeds:

`11, 12, 13, 16`

Loop057 v8 25M success seeds:

`1, 11, 12`

Gate count changes, loop052 final versus loop057 v8 25M:

- improved on `5 / 20` seeds: `1`, `6`, `17`, `19`, `20`;
- worsened on `3 / 20` seeds: `5`, `13`, `16`;
- unchanged on `12 / 20` seeds.

Success changed on:

- seed `1`: loop052 crash with `1` gate -> v8 success;
- seed `13`: loop052 success -> v8 crash with `1` gate;
- seed `16`: loop052 success -> v8 crash with `1` gate.

Interpretation:

V8 has local signal: it improves gate count on more seeds than it worsens, and
adds a new success seed. It is also unstable: it loses two loop052 success
seeds and final regresses after 25M.

## Crash Taxonomy

Artifacts:

- `experiments/level3_ppo_loop/diagnostics/level3_loop_052_final_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_057_25M_20seed_crash_taxonomy_summary.json`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_057_25M_20seed_crash_taxonomy_episodes.csv`
- `experiments/level3_ppo_loop/diagnostics/level3_loop_057_25M_20seed_crash_taxonomy_hotspots.png`

Note:

The taxonomy tool uses a single-controller replay path and can differ from the
competition-style hard evaluator on individual seeds. It is diagnostic only.

Taxonomy loop052 final:

- Successes: `3 / 20`
- Crashes: `17 / 20`
- Crash target gates: gate0 `9`, gate1 `2`, gate2 `5`, gate3 `1`
- Top likely objects: `obstacle_0` `4`, `gate_0_bottom` `2`,
  `gate_0_right` `2`, `obstacle_1` `2`, `obstacle_2` `2`

Taxonomy loop057 v8 25M:

- Successes: `4 / 20`
- Crashes: `16 / 20`
- Crash target gates: gate0 `7`, gate1 `6`, gate2 `3`
- Top likely objects: `obstacle_0` `4`, `gate_0_right` `3`,
  `obstacle_1` `2`, plus individual gate/obstacle hits.

Interpretation:

The v8 diagnostic replay reduces gate0 and gate2 crash concentration and
slightly improves diagnostic success, but it shifts more failures to gate1.
This is a weak positive structural signal, not enough to promote the checkpoint
as best.

## Decision Implication

The evidence is borderline:

- Against maturation: hard eval did not beat loop052; W&B pass/finish signals
  stayed flat; final regressed.
- For one guarded maturation: v8 has non-zero hard-eval success, mean gates
  equal to loop052 at 25M, hard-eval gate counts improved on more seeds than
  they worsened, and taxonomy shows a weak early-gate crash shift.

Therefore a single guarded maturation from the 25M checkpoint is defensible
under the Level2 step-curve rule, but only if it keeps reward/PPO/controller
settings unchanged and uses milestone hard eval to reject the lane if it still
fails to beat loop052.
