# Evaluator Metrics Review: loop087

Verdict: hold v27 beta=0.10; do not mature this same lane.

Loop087 improved over the earlier v27 beta screens, but it did not restore or
exceed the loop052 validation anchor.

| Checkpoint | Split | Success | Wilson 95% CI | Crash | Mean gates | Mean success time |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| loop052 anchor final | validation_unseen | 0.20 | [0.133, 0.289] | 0.80 | 1.47 | 6.858s |
| loop087 3M | validation_unseen | 0.16 | [0.101, 0.244] | 0.84 | 1.49 | 6.944s |
| loop087 final | validation_unseen | 0.17 | [0.109, 0.255] | 0.83 | 1.50 | 6.991s |

Dev_seen peaked at 3M with 0.20 success, 0.80 crash, 1.80 mean gates, and
6.64s mean successful time, but unseen validation did not confirm anchor
restoration.

Compared with recent v27 arms, loop087 final is better than loop085 beta=0 best
validation success 0.10 and loop086 beta=0.03 success 0.14. It remains below
loop052 on success, crash, and successful time. Its only anchor-positive metric
is mean gates, by a small +0.03.

## Failure Taxonomy

Loop087 validation failures are all `bounds_or_ground`:

- 3M: 84 `bounds_or_ground`, 16 successes
- final: 83 `bounds_or_ground`, 17 successes

Final failures by target gate:

- gate0: 38
- gate1: 17
- gate2: 19
- gate3: 9

This is not a material taxonomy improvement over loop052. It mostly preserves
low reliability while concentrating failures into bounds/ground.

## Recommendation

Use loop087 as evidence that stronger teacher retention beta helps versus
beta=0 and beta=0.03, but not enough to recover the loop052 anchor. From
evaluator evidence alone, hold v27 beta=0.10, reject maturation, and treat it
as next-lane evidence rather than a promotion checkpoint.
