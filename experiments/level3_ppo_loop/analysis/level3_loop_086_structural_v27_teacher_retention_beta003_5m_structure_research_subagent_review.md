# Loop086 Structure/Research Synthesis Review

Role: structure_research_synthesis

Trial:
`level3_loop_086_structural_v27_teacher_retention_beta003_5m`

## Verdict

The v27 teacher-retention KL minimal implementation is real enough for bounded
screening, but it is an offline minimal version. Run beta=0.10 next; if that
fails, hold v27 and improve implementation/data rather than keep sweeping.

## Implementation Status

Implemented:

- retention dataset loading;
- student v8 observations stored in the dataset;
- teacher action mean/logstd precomputed from loop052 teacher;
- `KL(pi_teacher || pi_student)` on retention batches;
- `loss += beta * teacher_kl` for MLP PPO;
- W&B/log metrics for teacher KL, action MSE, agreement, and sampled batch size.

Caveats:

- the training loop does not load the frozen teacher online;
- teacher outputs are precomputed by the dataset builder;
- `v27_teacher_model_name` and `v27_teacher_observation_layout` are provenance
  parameters, not runtime metadata checks;
- the current dataset does not include explicit failure-correction trajectory
  classes from the v27 spec.

## Dataset

Dataset:

`experiments/level3_ppo_loop/retention_datasets/v27_loop052_train_pool_success_v5_teacher_v8_student.npz`

Properties:

- samples: 2681
- successful teacher episodes: 8
- seeds: 2001, 2010, 2019, 2021, 2023, 2029, 2041, 2042
- excluded seed ranges: 1-20, 101-200, 1001-1200
- teacher layout: v5
- student layout: v8

This is sufficient for the 5M v27 beta sweep, but too small to prove broad
retention generalization.

## Recommendation

Launch `v27_teacher_retention_beta010_5m` with the same dataset and protocol.

Do not mature beta=0.03. If beta=0.10 fails to restore at least the loop052
anchor, hold v27 and improve:

- dataset metadata validation;
- analyzer retention summaries;
- episode-level teacher-retention evaluation;
- larger or stratified retention/failure-correction data.

## Hard Constraints

- keep `config/level3_dr.toml` unchanged;
- do not use final_locked seeds;
- run only one train/eval chunk;
- use W&B, dev_then_validation, Wilson CI, failure taxonomy, and 1M
  checkpoints;
- after beta=0.10, run analyzer and exactly three reviews before any next
  training.
