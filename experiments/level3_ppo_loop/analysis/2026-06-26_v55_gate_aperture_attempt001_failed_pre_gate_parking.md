# v55 Gate Aperture Attempt001 Failed: Pre-Gate Parking

## Summary

- Stage: `gate_aperture_reference`
- Run: `v55_tracker_gate_aperture_from_zigzag_attempt001`
- W&B: <https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/sio6h3n4>
- Training config: `config/level3_tracker_gate_aperture.toml`
- Initial checkpoint: `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Final checkpoint: `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/gate_aperture_reference/v55_tracker_gate_aperture_from_zigzag_attempt001_final.ckpt`
- Final metrics: `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_gate_aperture_from_zigzag_attempt001_final_metrics.json`
- Gate checker output: `/tmp/v55_gate_aperture_attempt001_final_gate.json`

The stage did not pass. The tracker learned stable aperture alignment and
survival, but it did not cross the gate plane or recover after the gate.

## Milestone Sweep

| checkpoint | valid cross | recovery | crash | mean aperture yz m | p90 aperture yz m | mean speed m/s | terminal speed m/s | hold ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| step1m | 0.000 | 0.000 | 1.000 | 0.4458 | 0.7351 | 0.4587 | 0.6017 | 0.000 |
| step2m | 0.000 | 0.000 | 1.000 | 0.3887 | 0.7268 | 0.4619 | 0.5499 | 0.000 |
| step3m | 0.000 | 0.000 | 1.000 | 0.2394 | 0.6313 | 0.3397 | 0.4518 | 0.271 |
| step4m | 0.000 | 0.000 | 0.000 | 0.1253 | 0.3038 | 0.1043 | 0.0001 | 0.784 |
| step5m | 0.000 | 0.000 | 0.000 | 0.0951 | 0.2602 | 0.1004 | 0.0000 | 0.823 |
| step6m | 0.000 | 0.000 | 0.000 | 0.0694 | 0.1496 | 0.1011 | 0.0000 | 0.855 |
| step7m | 0.000 | 0.000 | 0.000 | 0.0581 | 0.1195 | 0.1033 | 0.0000 | 0.875 |
| step8m | 0.000 | 0.000 | 0.000 | 0.0529 | 0.0726 | 0.1002 | 0.0000 | 0.893 |
| step9m | 0.000 | 0.000 | 0.000 | 0.0494 | 0.0685 | 0.1036 | 0.0000 | 0.887 |
| step10m | 0.000 | 0.000 | 0.000 | 0.0481 | 0.0732 | 0.1032 | 0.0000 | 0.887 |
| step11m | 0.000 | 0.000 | 0.000 | 0.0460 | 0.0419 | 0.0998 | 0.0000 | 0.903 |
| step12m | 0.000 | 0.000 | 0.000 | 0.0471 | 0.0580 | 0.1005 | 0.0003 | 0.896 |
| step13m | 0.000 | 0.000 | 0.000 | 0.0485 | 0.0297 | 0.1013 | 0.0003 | 0.899 |
| step14m | 0.000 | 0.000 | 0.000 | 0.0489 | 0.0391 | 0.1014 | 0.0000 | 0.893 |
| final | 0.000 | 0.000 | 0.000 | 0.0466 | 0.0269 | 0.1014 | 0.0009 | 0.901 |

## Gate Result

The final checkpoint failed exactly the two functional crossing metrics:

- `valid_aperture_cross_rate = 0.0`, required `>= 0.7`
- `post_gate_recovery_rate = 0.0`, required `>= 0.6`

The final checkpoint passed the supporting metrics:

- `checkpoint_backed = true`
- `all_finite = true`
- `crash_rate = 0.0`
- `mean_aperture_yz_error_m = 0.04664`
- `p90_aperture_yz_error_m = 0.02694`
- `mean_post_gate_speed_mps = 0.0`

`mean_post_gate_speed_mps = 0.0` is not a positive recovery signal here; there
were no post-gate samples.

## Three-Review Synthesis

`tracker_eval_metrics` found that no milestone checkpoint was close to passing
the real event gate. From step4 onward the policy stopped crashing and became
very accurate in Y/Z, but all episodes still timed out without valid crossing
or post-gate recovery.

`tracker_wandb_ppo` found healthy PPO signals rather than optimizer failure:
reward improved, episode length reached the horizon, explained variance rose,
and KL/clip diagnostics were plausible. The learned behavior was stable
pre-gate alignment, not crossing.

`tracker_structure_research` found that the actor already observes enough local
gate/reference information. The missing piece is the training objective and
curriculum: dense reward pays position/YZ/smoothness, while the gate checker
requires actual plane crossing and post-gate recovery.

## Diagnosis

Attempt001 learned a local optimum:

```text
approach gate aperture -> align accurately -> stop before crossing
```

This is not a reason to continue the same reward for another 25M steps. It is
a reward/curriculum semantics failure for the gate-aperture mini task.

## Next Action

Launch `v55_gate_aperture_phase_completion_attempt002` after builder/checker.
Keep evaluator thresholds unchanged and keep `config/level3.toml` unchanged.

The fix should:

- add explicit gate-X progress, valid-cross, post-gate recovery, and near-plane
  lingering reward diagnostics/terms;
- start the gate-aperture mini task from an airborne near-plane distribution so
  PPO trains crossing rather than relearning takeoff;
- run a smoke, then a bounded 15M maturation with 1M milestone checkpoints.
