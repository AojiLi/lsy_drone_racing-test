# V53 Hybrid Checker Gate

Date: 2026-06-25

Result: `ALL GREEN`

The read-only checker verified the implementation gate for
`v53_completion_first_hybrid_planner_controller`.

## Evidence

- `config/level3.toml` unchanged:
  `git diff --exit-code -- config/level3.toml` exited `0`.
- Patch formatting clean:
  `git diff --check` exited `0`.
- Controller structure/load clean:
  `lsy_drone_racing/control/level3_hybrid_planner_controller.py` defines one
  `Controller` subclass, `Level3HybridPlannerController`, and repo
  `load_controller(...)` can load it.
- Compile clean:
  source compile passed without writing `.pyc`.
- Smoke evidence clean for action finiteness but not behavior promotion:
  `experiments/level3_ppo_loop/mppi/v53_hybrid_smoke_101_105_d_summary.csv`
  records `finite_action_rate=1.0`, `success_rate=0.0`, and `mean_gates=0.0`.
- The hybrid smoke was not recorded as PPO success. `state.json` still records
  the PPO best as `level3_loop_107...`, with `target_met=false`.
- No dev `1-20` v53 artifacts were found, so the lane was not promoted after
  the failed smoke.

## Caveat

The per-episode CSV records `finite_action=True` per seed. The aggregate
`finite_action_rate=1.0` is in the summary CSV, not as a column in the episode
CSV.

## Git Scope

Relevant files for this gate:

- `lsy_drone_racing/control/level3_hybrid_planner_controller.py`
- `experiments/level3_ppo_loop/analysis/2026-06-25_v53_hybrid_level2_virtual_gate_smoke.md`
- `experiments/level3_ppo_loop/analysis/2026-06-25_v53_hybrid_checker_gate.md`
- `experiments/level3_ppo_loop/state.json`
- `drone_notes/level3_loops/v53-hybrid-level2-virtual-gate-smoke.md`

Unrelated existing dirty files were not part of this gate:

- `lsy_drone_racing/control/mppi_level3_oracle.py`
- `drone_notes/Welcome.md`
