# Loop116 V45 Subagent Reviews

Trial:
`level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.md`

Hard-eval target:
unchanged `config/level3.toml`

## Main Result

v45 is valid evidence that flat MLP retention is mechanically active, but it
does not clear the promotion gate. The best checkpoint is the 4M checkpoint:

| Checkpoint | Success | Mean Gates | Crash | Timeout | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1M | 15% | 1.56 | 85% | 0% | 6.901s |
| 2M | 14% | 1.46 | 86% | 0% | 6.486s |
| 3M | 17% | 1.56 | 83% | 0% | 6.925s |
| 4M | 20% | 1.60 | 80% | 0% | 6.941s |
| final | 19% | 1.59 | 81% | 0% | 6.880s |

The global frontier remains:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash,
  `7.578s` mean successful time;
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash,
  `6.756s` mean successful time.

## Evaluator Metrics Review

- Key finding: v45 did not clear the promotion or maturation gate.
- Evidence: milestones were `15%/1.56`, `14%/1.46`, `17%/1.56`,
  `20%/1.60`, and `19%/1.59`.
- Failure distribution at the best 4M checkpoint remains concentrated in
  contact/bounds failures: gate 0 `36`, gate 1 `12`, gate 2 `29`, gate 3 `3`.
- Seed coverage does not clearly broaden. Versus loop110 3M, v45 preserves
  `16/21` successful validation seeds, loses `5`, and gains `4`. Versus
  loop107 1M, v45 preserves `13/21`, loses `8`, and gains `7`.
- Recommendation: do not continue v45 as executed and do not start future
  training from loop116 final.

## W&B / PPO Diagnostics Review

- Key finding: retention worked mechanically, and PPO did not show a classic
  instability signature.
- Evidence: teacher KL moved from about `0.0452` to `0.0314`, teacher action
  MSE from about `0.00883` to `0.00535`, and teacher agreement from about
  `0.897` to `0.946`, with sampled batch size `512` throughout.
- PPO metrics were calm: final approximate KL was near zero, clip fraction was
  `0`, entropy remained about `4.48`, explained variance was about `0.75`, and
  value loss was high but bounded.
- The training signal did not convert into hard-eval progress. The best
  validation checkpoint stayed below loop107 and loop110.
- Recommendation: do not treat v45 as a PPO instability tuning problem.

## Structure / Research Review

- Key finding: v45 preserved the familiar `18%-21%` plateau, but did not expand
  the frontier.
- Evidence: healthy retention metrics plus unchanged hard-eval plateau point
  toward limited teacher/data coverage or a missing frontier teacher, not an
  inactive loss.
- Recommendation: launch a new named structural lane, not a reward-number-only
  continuation and not same-hypothesis maturation.
- Proposed next lane:

```text
v46_v5_residual_frontier_teacher_action_retention_preflight
```

The next question is whether the actual global frontier teacher, loop107/v37
1M, can be used safely as training-only teacher data. Because loop107 is a
residual-GRU policy, the dataset builder must first prove that extracted
teacher actions include the residual branch and correct recurrent hidden-state
handling.

## Main-Agent Synthesis

Reject v45 as executed. The useful conclusion is narrow but important:

1. flat v5 MLP dataset retention is active;
2. the loop101+loop110 MLP teacher union is not enough to break the plateau;
3. continuing v45 longer is likely to spend compute inside the same
   `18%-22%` seed reshuffle band;
4. the next step should be a held preflight lane for loop107 residual-GRU
   teacher action extraction before any training.

No Level3 track geometry, gate layout, obstacle layout, or randomization may be
changed. Final acceptance remains hard eval on `config/level3.toml`.
