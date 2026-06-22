# Loop085 Decision: Reject Beta0, Hold For V27 Teacher KL Implementation

Decision: hold_for_more_analysis

Pending gate resolved for:

- trial_id:
  `level3_loop_085_structural_v27_teacher_retention_beta0_control_5m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_085_structural_v27_teacher_retention_beta0_control_5m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_085_structural_v27_teacher_retention_beta0_control_5m_analysis.json`

## Verdict

Reject the loop085 beta=0 control arm as a training branch.

Do not continue beta=0, do not mature it to 60M, and do not start beta=0.03 or
beta=0.10 until real teacher-retention KL support exists and passes a dry-run
and sanity check.

## Evidence

Current validation anchor remains loop052 final:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Loop052 validation anchor:

- success: 0.20
- crash: 0.80
- mean gates: 1.47
- mean successful time: 6.858s
- success CI95: [0.133, 0.289]

Loop085 best validation checkpoint, 3M:

- success: 0.10
- crash: 0.90
- mean gates: 1.38
- mean successful time: 6.97s
- success CI95: [0.055, 0.174]

Loop085 final validation checkpoint:

- success: 0.08
- crash: 0.92
- mean gates: 1.33
- mean successful time: 9.567s

Loop085 did not preserve the anchor behavior. Its best validation success is
10 percentage points below loop052, crash rate is 10 percentage points higher,
and mean gates is lower.

## Subagent Synthesis

Evaluator metrics review:

- reject beta=0;
- validation 3M is worse than loop052 on success, crash, and mean gates;
- failures are dominated by `bounds_or_ground`, not a useful preserved teacher
  behavior pattern.

W&B/PPO diagnostics review:

- PPO is numerically stable, with low KL, low clip fraction, and reasonable
  explained variance;
- W&B training reward and gate proxies do not convert into hard-eval progress;
- retention metrics confirm beta=0 has no actual teacher-retention loss.

Structure/research synthesis:

- loop085 implemented only the no-teacher-KL control arm;
- nonzero-beta teacher retention is still blocked by missing retention dataset,
  frozen teacher inference, dual observation path, and KL loss integration;
- beta=0.03 and beta=0.10 must remain blocked until those pieces are
  implemented and reviewed.

## Rejected Next Actions

- continue beta=0;
- mature loop085 to 60M or 90M;
- launch beta=0.03 or beta=0.10 with the current training code;
- follow the analyzer's simple gate-reward scaling command;
- modify `config/level3_dr.toml` or the hard-eval seed protocol.

## Approved Next Work

The next Codex loop should implement and validate:

`implement_v27_teacher_retention_kl_minimal`

Minimum scope:

1. Build a retention dataset from successful loop052 teacher episodes in
   train_pool seeds only.
2. Exclude `dev_seen`, `validation_unseen`, and `final_locked` seeds.
3. Load a frozen loop052 teacher.
4. Support teacher v5 observations and student v8 observations from retained
   rollout states.
5. Compute `KL(pi_teacher || pi_student)` on retention batches.
6. Add `beta * teacher_kl` to PPO loss only when beta > 0.
7. Log real retention metrics:
   `losses/teacher_kl`, `teacher_action_mse`,
   `retention/teacher_agreement`, and `retention/sampled_batch_size`.
8. Run `py_compile` and orchestrator dry-runs.
9. Only after the implementation sanity check passes, launch one beta=0.03 5M
   screen with 1M checkpoints and the same `dev_then_validation` hard-eval
   protocol.

## Promotion Gate

A beta=0.03 screen may continue only if it restores or exceeds the loop052
validation anchor:

- validation success at least 0.20, preferably higher;
- crash no worse than 0.80, or mean gates clearly improves;
- retention batches are nonzero and teacher KL/agreement metrics are finite;
- no use of final_locked seeds;
- no edits to `config/level3_dr.toml`.
