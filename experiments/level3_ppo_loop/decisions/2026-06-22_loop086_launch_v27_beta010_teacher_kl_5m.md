# Loop086 Decision: Launch V27 Beta0.10 Teacher KL Screen

Decision: launch_named_structural_lane

Pending gate resolved for:

- trial_id:
  `level3_loop_086_structural_v27_teacher_retention_beta003_5m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_086_structural_v27_teacher_retention_beta003_5m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_086_structural_v27_teacher_retention_beta003_5m_analysis.json`

## Verdict

Reject beta=0.03 maturation.

Launch exactly one medium-strength v27 teacher-retention screen:

`v27_teacher_retention_beta010_5m`

This is not permission to run multiple chunks. After beta=0.10 finishes, run the
analyzer, exactly three reviews, and a new main-agent decision packet.

## Evidence

Loop086 beta=0.03 validation best, 1M:

- success: 0.14
- crash: 0.86
- mean gates: 1.55
- mean successful time: 6.791s
- success CI95: [0.085, 0.221]

Loop085 beta=0 validation best:

- success: 0.10
- crash: 0.90
- mean gates: 1.38
- mean successful time: 6.970s

Loop052 validation anchor:

- success: 0.20
- crash: 0.80
- mean gates: 1.47
- mean successful time: 6.858s

Beta=0.03 improved over the beta=0 control arm, but it still failed to recover
loop052 reliability. Later beta=0.03 checkpoints did not improve the dev
screen, so longer maturation is not justified.

## Retention Evidence

The v27 teacher-retention path is active:

- dataset samples: 2681
- successful teacher episodes: 8
- excluded seed ranges: 1-20, 101-200, 1001-1200
- `retention/sampled_batch_size`: 512
- `losses/teacher_kl`: about 2.18 down to about 1.69
- `losses/teacher_action_mse`: about 0.153 down to about 0.072
- `retention/teacher_agreement`: about 0.599 up to about 0.723

The implementation is therefore no longer a placeholder, but retention
agreement remains below the intended 0.80 proxy.

## Subagent Synthesis

Evaluator metrics:

- beta=0.03 improved success, crash, and gates versus beta=0;
- beta=0.03 did not beat loop052;
- failure taxonomy remains dominated by `bounds_or_ground`.

W&B/PPO diagnostics:

- PPO is stable;
- teacher KL is finite and nonzero;
- retention improves during training;
- training rewards still do not reliably convert into hard-eval success.

Structure/research:

- v27 minimal implementation is real, but offline and dataset-limited;
- beta=0.10 is the appropriate final medium arm in the current three-arm
  v27 design;
- if beta=0.10 fails, stop v27 and improve the implementation/data rather than
  keep sweeping.

## Approved Next Command Shape

Use the named structural lane:

`v27_teacher_retention_beta010_5m`

Required properties:

- hard eval on unchanged `config/level3_dr.toml`;
- train config `level3_dr.toml`;
- student observation v8;
- frozen teacher source loop052;
- student initial checkpoint loop078;
- beta `0.10`;
- same retention dataset;
- 5M training;
- 1M checkpoint interval;
- W&B enabled;
- `dev_then_validation`, Wilson CI, failure taxonomy;
- no final_locked seeds.

## Rejected Actions

- continue beta=0.03;
- mature beta=0.03 to 60M or 90M;
- run beta=0.10 and then automatically continue without analysis;
- follow the analyzer's generic reward-scaling command;
- modify `config/level3_dr.toml`;
- inspect or train on final_locked seeds.

## Stop Rule After Beta0.10

Hold v27 if beta=0.10 does not restore or exceed the loop052 anchor:

- validation success should be at least 0.20;
- crash should be at or below 0.80;
- bounds/ground failures should materially improve;
- retention agreement should move toward 0.80 with nonzero sampled batches.

If these fail, write a hold decision and improve implementation/data, including
dataset metadata validation, analyzer retention summaries, episode-level
teacher-retention evaluation, and a larger or stratified retention dataset.
