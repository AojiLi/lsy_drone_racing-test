# Decision: Reject v35 and Launch v36 Online Level Replay

Decision: `launch_named_structural_lane`

Approved next lane:
`v36_online_competence_gated_level_replay_from_loop101`

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization to make the metric easier.
- Do not start from loop102 or loop103 checkpoints.
- Start from loop101 final, the current global frontier checkpoint.
- Keep deployed inference as the existing v5 feed-forward PPO Actor:
  `Level3 observation/history -> PPO actor -> roll/pitch/yaw/thrust`.

## Evidence

loop103/v35 tested competence-gated gate-phase reset curriculum from loop101 for
10M steps.

Best loop103 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m_step_009000000.ckpt`
- success: `19/100`
- mean successful time: `7.245s`
- crash rate: `81%`
- timeout rate: `0%`
- mean gates: `1.68`

Global best remains loop101 final:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt`
- success: `20/100`
- mean successful time: `6.873s`
- crash rate: `80%`
- timeout rate: `0%`
- mean gates: `1.69`

v35 did not pass its promotion gate: it neither exceeded `20%` success nor
exceeded `1.69` mean gates with crash no worse than `80%`. The final checkpoint
fell to `17%` success, `1.58` mean gates, and `83%` crash.

## Reviewer Synthesis

- Evaluator reviewer: reject v35 as-is. Failure remains dominated by
  contact/bounds, concentrated around gate 0 and gate 2.
- W&B/PPO reviewer: PPO is not obviously unstable. v35's competence gate never
  opened; replaying the same MLP/v5 lane without a new mechanism is weak.
- Structure/research reviewer: prefer online competence-gated level replay from
  loop101 over continuing v35 or reusing loop102/loop103 checkpoints.

## Why Not Direct GRU Now

GRU remains a valid next memory hypothesis, but the old from-scratch GRU lane
already failed badly: loop062 reached `0%` success and only `0.10` mean gates
at best. A useful GRU retry should be a separate transfer or pretraining packet,
not a blind repeat of that run.

v36 is narrower: it keeps the current best MLP controller and changes only the
training-time level sampling pressure.

## Approved v36 Scope

`v36_online_competence_gated_level_replay_from_loop101`

- Initial checkpoint:
  loop101 final checkpoint listed above.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Policy:
  current 2x256 Tanh MLP Actor/Critic.
- Reward numbers:
  unchanged loop052 remote nominal values.
- PPO numbers:
  unchanged loop052 remote nominal values.
- Replay profile:
  `v36_train_pool_bounds_gate0_gate2`.
- Replay seed source:
  audited train-pool bounds-or-ground failure seeds only; no dev_seen,
  validation_unseen, or final_locked seed leakage.
- Replay probability:
  start `0.03`, max `0.08`, increment `0.01`.
- Replay competence gate:
  passed-gate rate `>=0.0065`, finish rate `>=0.0005`, crash rate `<=0.0082`.
- Gate-phase reset curriculum:
  keep v35 competence-gated schedule, start `0.12`, max `0.45`.

## Promotion And Rollback

Promote or mature v36 only if the 10M screen beats the frontier:

- success `>20%`, or
- mean gates `>1.69` with crash `<=80%` and no late-checkpoint collapse.

Reject v36 if success stays `<=20%`, mean gates stay `<=1.69`, or crash remains
`>=81%`. If rejected, do not keep tuning replay probability; write a GRU
transfer or memory-structure packet.

## Approved Command Shape

After tests and a dry-run pass, the next real command may use:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v36_online_competence_gated_level_replay_from_loop101 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_pasted_structural_update.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop103_reject_v35_launch_v36_online_level_replay.md
```
