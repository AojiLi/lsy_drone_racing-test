# Launch V27 Beta0 Control Screen

Decision: launch_named_structural_lane

## Scope

Launch only the v27 beta `0.00` control arm:

`v27_teacher_retention_beta0_5m`

This is the no-teacher-KL control arm for the v27 teacher-retention family. It
does not claim that nonzero teacher KL is implemented. The beta `0.03` and
`0.10` arms remain blocked until the retention dataset and teacher/student
dual-observation path are implemented and reviewed.

## Contract

- hard evaluation remains on unchanged `config/level3_dr.toml`;
- do not edit Level3 track geometry, gates, obstacles, or final evaluator
  seeds;
- train config remains `level3_dr.toml`;
- observation layout: `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`;
- policy: 2x256 Tanh MLP;
- initial checkpoint: `loop078_final`;
- teacher reference: `loop052_final`;
- beta: `0.00`;
- training horizon: `5M`;
- checkpoint interval: `1M`;
- evaluator protocol: `dev_then_validation`, Wilson CI, failure taxonomy;
- W&B project: `ADR-PPO-Racing-Level3`.

## Rationale

The latest unseen validation audit selected loop052 final as the reliability
anchor, while loop078 final is the compatible v8 student/warm-start checkpoint.
Before implementing nonzero teacher KL, the control arm is needed to measure
how much of any v27 result comes from the short v8 continuation itself.

## Stop Rule

After the 5M control arm, run the analyzer and three separate reviews before
launching any nonzero-beta arm. Hold if hard-eval validation success, crash, or
mean gates regress below the loop052 validation anchor without a clear
diagnostic reason.

