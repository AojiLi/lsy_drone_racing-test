# Loop089 Evaluator Metrics Review

Verdict: reject loop089 as a continuation candidate. Hard eval remained on
`config/level3_dr.toml`; only `dev_seen` and `validation_unseen` evidence was
used, not `final_locked` seeds.

| Run | Split / checkpoint | Success | Mean success time | Crash | Mean gates |
| --- | --- | ---: | ---: | ---: | ---: |
| loop052 anchor | validation_unseen final | 20% | 6.858s | 80% | 1.47 |
| loop088 | validation_unseen 4M | 19% | 6.846s | 81% | 1.57 |
| loop089 | validation_unseen 2M | 18% | 7.002s | 82% | 1.49 |

Loop089 regressed versus loop088 4M on every hard-gate metric: -1pp success,
+0.156s mean successful time, +1pp crash, and -0.08 mean gates. It also stays
behind the loop052 anchor on success, crash, and time, with only a tiny
mean-gates edge that did not convert.

Failure taxonomy:

- 82/100 validation episodes ended as `bounds_or_ground`
- 18/100 succeeded
- 0 timed out
- failures by target gate: gate0 34%, gate1 22%, gate2 23%, gate3 3%
- this is early/mid gate-conversion failure, not late-race speed failure

Reward adjustment verdict:

Reject the loop088-to-loop089 reward adjustment. The approved continuation gate
required success >=20% with crash <=80%, or clear mean-gate progress above
1.57 without success regression, or reduced `bounds_or_ground`. Loop089 failed
all three.

Recommended next action:

Choose `launch_named_structural_lane`, not `continue_same_hypothesis` and not
another automatic reward-number tweak. If the main packet is not ready to name
that lane, hold until structure/W&B reviews are synthesized.
