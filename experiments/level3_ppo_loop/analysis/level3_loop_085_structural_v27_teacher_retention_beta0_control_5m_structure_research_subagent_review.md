# Loop085 Structure/Research Synthesis Review

Role: structure_research_synthesis

Trial:
`level3_loop_085_structural_v27_teacher_retention_beta0_control_5m`

## Verdict

The beta=0 control arm is implemented and complete, but real v27
teacher-retention is not implemented yet. Hold before beta=0.03 or beta=0.10.

## What Loop085 Implemented

Loop085 is a no-teacher-KL control arm:

- train and hard eval config: `level3_dr.toml`
- student observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- warm start: loop078 final
- teacher reference metadata: loop052 final
- v27 beta: 0.00
- retention dataset: disabled control arm
- horizon: 5M
- checkpoint interval: 1M
- eval protocol: `dev_then_validation`

## What Is Not Implemented

Current training code does not yet implement:

- collecting or loading a teacher-success retention dataset
- excluding dev, validation, and final locked seeds from retention collection
- loading a frozen loop052 teacher policy for loss computation
- converting retained states into teacher v5 observations while the student
  trains on v8 observations
- computing `KL(pi_teacher || pi_student)` on retention states
- adding `beta * teacher_kl` to the PPO loss
- real retention metrics beyond placeholder zeros or NaNs

The training script explicitly rejects `v27_teacher_kl_beta > 0.0`, and the
orchestrator keeps the beta=0.03 and beta=0.10 lanes blocked behind
`teacher_retention_kl` support.

## Required Next Implementation

Create a named implementation lane:

`implement_v27_teacher_retention_kl_minimal`

Minimum scope:

- build a train_pool retention dataset from successful loop052 teacher
  episodes;
- exclude `dev_seen`, `validation_unseen`, and `final_locked` seeds;
- store observations, teacher action mean/log_std, gate index, clearance
  diagnostics, and success time;
- load the frozen loop052 teacher;
- support teacher v5 observations and student v8 observations from the same
  retained rollout state;
- compute teacher KL on sampled retention states;
- add the weighted KL to PPO loss when beta > 0;
- log real `losses/teacher_kl`, `teacher_action_mse`,
  `retention/teacher_agreement`, and `retention/sampled_batch_size`.

## Hard Constraints

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Keep hard eval on unchanged `config/level3_dr.toml`.
- Keep the first v27 nonzero-beta screen at 5M with 1M checkpoints.
- Keep dev, validation, and final seed roles separated.
- Do not inspect or use final_locked seeds in the loop.
- Do not change observation layout, hidden width, GRU, PPO optimizer, or the
  Level3 track in the first nonzero-beta v27 screen.
