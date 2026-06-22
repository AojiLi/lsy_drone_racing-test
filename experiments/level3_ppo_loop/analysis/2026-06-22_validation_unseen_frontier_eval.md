# Validation-Unseen Frontier Evaluation

Scope: re-evaluate historical Level3 frontier checkpoints on fixed unseen
validation seeds `101-200`.

This is evaluator-only work. It does not train, tune, or modify
`config/level3_dr.toml`.

## Seed Split

- seed manifest:
  `experiments/level3_ppo_loop/seed_manifests/validation_unseen_101_200.txt`
- seed split name: `validation_unseen`
- episodes per checkpoint: 100
- confidence interval: Wilson 95%
- failure taxonomy: enabled

## Results

| checkpoint | success | Wilson 95% CI | crash | mean gates | mean success time | p90 success time |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| loop052 final | 20% | 13%-29% | 80% | 1.47 | 6.86s | 8.26s |
| loop071 20M | 16% | 10%-24% | 84% | 1.65 | 7.87s | 10.27s |
| loop078 final | 13% | 8%-21% | 87% | 1.49 | 6.85s | 7.72s |
| v23 10M | 14% | 9%-22% | 86% | 1.37 | 8.63s | 11.81s |
| loop083 15M | 14% | 9%-22% | 86% | 1.46 | 6.91s | 7.80s |
| loop084 30M | 7% | 3%-14% | 93% | 1.14 | 6.71s | 7.48s |

Artifacts:

- summary CSV:
  `experiments/level3_ppo_loop/validation_unseen_frontier_eval_2026-06-22_summary.csv`
- episode CSV:
  `experiments/level3_ppo_loop/validation_unseen_frontier_eval_2026-06-22_episodes.csv`

## Interpretation

The old dev-seen frontier was over-optimistic:

- loop078 dev_seen: 25% success
- loop078 validation_unseen: 13% success

The latest v26 line does not generalize:

- loop083 15M: 14% validation success
- loop084 30M: 7% validation success

The strongest validation checkpoint by the agreed ordering is loop052 final:

1. highest validation success: 20%
2. highest lower confidence bound: 13%
3. crash rate: 80%
4. mean gates: 1.47
5. mean success time: 6.86s

loop071 has better mean gates, but lower success and lower Wilson lower bound.
Use loop071 as a gate-progress diagnostic, not as the primary reliability
anchor.

## Failure Taxonomy

The dominant failure classes remain shared across candidates:

- near-gate obstacle crashes
- gate side frame crashes
- gate vertical frame crashes
- pre-plane obstacle crashes

This supports the conclusion that the next experiment should address
successful-behavior retention plus targeted failure correction, not another
long maturation of v26.

## Decision Implication

Do not start loop085 or any long training run from v26.

Next valid work is a v27 design packet and implementation plan for
teacher-anchored failure correction. The teacher should be selected using this
validation evidence. A practical first design is:

- teacher action source: loop052 final, because it is the best validation
  reliability anchor
- student warm-start candidate: loop078 final or a v8-compatible checkpoint,
  if the first v27 implementation keeps v8 observations
- retention/failure-correction seeds: from `train_pool`, not from dev,
  validation, or final_locked splits

