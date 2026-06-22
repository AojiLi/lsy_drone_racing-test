# Loop093 Evaluator Metrics Review

Role: evaluator metrics

Final target: `config/level3.toml`

## Verdict

Loop093 is not accepted and is not promotable on evaluator metrics alone.

Best checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_093_structural_v30_episode_semantics_only_2m/level3_loop_093_structural_v30_episode_semantics_only_2m_final.ckpt`

Metrics on `validation_unseen` seeds 101-200:

- success: `17 / 100`
- success rate: `0.17`
- mean successful time: `7.04235294117647s`
- crash rate: `0.83`
- timeout rate: `0.00`
- mean gates: `1.55`

Compared with loop052 final-target baseline:

- success rate: `+0.01`
- crash rate: `-0.01`
- mean gates: `+0.12`
- mean successful time: `+0.26860294117647s`

This is a tiny, noisy improvement, not a decisive hard-eval advance.

## Main Failure Pattern

Failures remain persistent contact/bounds crashes during gate acquisition and
conversion. Loop093 final recorded `83` contact failures. They concentrate at
target gate 0 (`34`) and target gate 2 (`31`).

## Recommendation

Do not promote or long-mature v30-A on this single seed. Completing the planned
independent-seed v30-A screen is reasonable, but only as replication evidence.
