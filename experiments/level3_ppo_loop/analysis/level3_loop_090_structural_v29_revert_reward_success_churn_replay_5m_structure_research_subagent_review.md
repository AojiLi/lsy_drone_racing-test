# Structure/Research Review: loop090 v29 Success-Churn Replay

## Key Finding

v29 should be rejected as a continuation hypothesis. The train-pool
success-churn replay idea was reasonable as a bounded screen, but it did not
generalize to hard eval on unchanged `config/level3_dr.toml`.

Evidence:

- Best v29 checkpoint was 3M: 0.14 success, 0.86 crash, 1.39 mean gates, 6.72s
  mean successful time.
- It regressed versus the prior evaluated trial: success `-0.04`, crash
  `+0.04`, mean gates `-0.10`.
- It is also worse than the loop088 4M parent checkpoint: 0.19 success, 0.81
  crash, 1.57 mean gates.
- W&B/PPO signals do not indicate optimizer collapse: KL/clip were flat,
  retention was healthy, and teacher agreement improved, but gate/finish
  behavior did not convert.

## Recommendation

Choose `hold_for_more_analysis`.

Do not continue v29, do not mature it toward 60M/90M, and do not launch another
automatic reward-number tweak. If the next training move is eventually approved,
it should be a new named structural lane backed by a packet, not "same v29 but
longer."

## Evidence Needed Before Another Train Chunk

- Validation seed-level churn comparison across loop052, loop088 4M, loop089
  2M, and v29 3M: successes lost/gained, target-gate failure shifts, and
  bounds/ground endpoints.
- Train-pool replay efficacy check: did v29 preserve the loop088/loop089 union
  success seeds on `2300-2399`, or did replay fail even on its source slice?
- Milestone table for v29 1M-5M, including final, to confirm 3M was the true
  best and not a noisy evaluator artifact.
- W&B/PPO review confirming no hidden retention collapse or value/entropy issue
  before blaming structure.

## Constraints

- Keep `config/level3_dr.toml` unchanged for hard eval and final acceptance.
- Do not use `final_locked` seeds for replay, diagnostics, tuning, or lane
  selection.
- Do not silently change PPO/training hyperparameters; any such move must be a
  named structural/training lane with evidence.
- W&B reward improvement remains diagnostic only; the hard evaluator decides.
