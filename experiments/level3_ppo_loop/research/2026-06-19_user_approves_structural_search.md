# User Approval: Level3 Structural Search

Date: 2026-06-19

User decision:

- Cancel the previous reward-only default.
- Open observation-structure experiments.
- Structural changes are allowed when useful, including controller,
  observation, reward structure, training structure, and PPO/training
  hyperparameters.
- Hard boundary: do not change the Level3 race track itself to make the target
  easier.

Operational interpretation:

- The target and final hard eval remain `config/level3_dr.toml`.
- Do not edit Level3 track geometry/randomization in `config/level3_dr.toml` to
  improve metrics.
- Training-only curricula or alternate training configs may be explored, but
  they must be named as structural lanes and cannot be accepted without hard
  eval on `config/level3_dr.toml`.
- Each structural lane needs a named hypothesis, W&B logging, milestone
  checkpoint evaluation, and post-run analysis before continuing.

Current recommended first structural lane:

- `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Source evidence:
  `experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md`
- Reason: remote hard eval showed the v5 local-obstacle checkpoint outperforming
  the current local best, while all-gates/v4 remained weak.

