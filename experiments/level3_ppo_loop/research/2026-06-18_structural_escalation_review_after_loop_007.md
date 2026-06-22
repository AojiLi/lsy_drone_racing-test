# Level3 PPO Structural Escalation Review: after level3_loop_007

## Verdict

- Eligible for Stage 2 structural review: yes
- Main reason: six evaluated active-reward-only trials failed to produce any
  successful evaluator episode or beat the original baseline gate count.
- Recommended next action: stop Stage 1 reward-number search and run a
  structural diagnosis stage. This packet authorizes review and proposal work
  only; it does not directly approve code/config changes.

## Reward-Only Exhaustion Gate

| Criterion | Required | Actual | Pass |
| --- | ---: | ---: | --- |
| Evaluated reward-only trials | 6 | 6: `001`, `002`, `004`, `005`, `006`, `007` | yes |
| Distinct active-reward hypotheses | 4 | 6 reward-number signatures | yes |
| Accumulated evaluated reward-only steps | 120M | about 210M command timesteps; 209,911,808 actual logged train steps | yes |
| Consecutive no-improvement evaluated trials | 4 | 5 trials after `001` did not beat global best | yes |
| Target still unmet | success `< 0.60` or time `> 7.0s` | best success `0.0`, time `null` | yes |
| W&B conversion absent | gate/finish curves fail to improve evaluator metrics | 005/006/007 showed flat or zero gate/finish conversion | yes |
| Required subagent agreement | evaluator, W&B, reward-failure, research, codebase diagnosis | all five post-007 audits support opening review | yes |

Note: the script's pairwise plateau counter may treat 007 as a small local
increase over 006 because mean gates moved from `0.70` to `0.75`. This does not
change the escalation decision: 007 still failed its own decision rule because
`success_rate == 0.0` and `mean_gates <= 0.85`, and it did not beat the global
incumbent.

## Local Evidence

Current global incumbent:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

- Success rate: `0.0`
- Mean successful time: `null`
- Crash rate: `1.0`
- Mean gates: `0.85`
- Score: `-71.6`

Evaluated reward-only trials:

| Trial | Best checkpoint | Success | Crash | Mean gates | Beat incumbent |
| --- | --- | ---: | ---: | ---: | --- |
| `001_baseline` | `level3_loop_001_baseline:final` | `0.0` | `1.0` | `0.85` | incumbent |
| `002_gate_acquisition_safety` | `level3_loop_002_gate_acquisition_safety:10M` | `0.0` | `1.0` | `0.80` | no |
| `004_gate_acquisition_safety` | `level3_loop_004_gate_acquisition_safety:30M` | `0.0` | `1.0` | `0.80` | no |
| `005_auto_precision_low_pressure` | `level3_loop_005_auto_precision_low_pressure:final` | `0.0` | `1.0` | `0.70` | no |
| `006_custom_safety_axis_recovery` | `level3_loop_006_custom_safety_axis_recovery:20M` | `0.0` | `1.0` | `0.70` | no |
| `007_custom_axis_dominant_controlled_probe` | `level3_loop_007_custom_axis_dominant_controlled_probe:final` | `0.0` | `1.0` | `0.75` | no |

## W&B Non-Conversion Evidence

W&B runs reviewed:

- `level3_loop_005_auto_precision_low_pressure`
- `level3_loop_006_custom_safety_axis_recovery`
- `level3_loop_007_custom_axis_dominant_controlled_probe`

Key evidence:

| Trial | Eval result | Train reward movement | Gate/finish conversion | PPO stability |
| --- | --- | --- | --- | --- |
| `005` | success `0.0`, gates `0.70`, crash `1.0` | train reward delta `+205.768814` | `passed_gate_rate` tail `0.006805`, `finished_rate` tail `0.0` | KL tail `0.000395`, clip tail `0.000008` |
| `006` | success `0.0`, gates `0.70`, crash `1.0` | train reward delta `+140.666237` | `passed_gate_rate` tail `0.009598`, `finished_rate` tail `0.000031` | KL tail `0.002047`, clip tail `0.003366` |
| `007` | success `0.0`, gates `0.75`, crash `1.0` | train reward delta `+182.707336` | `passed_gate_rate` tail `0.008525`, `finished_rate` tail `0.0` | KL tail `0.000535`, clip tail `0.000043` |

The PPO update metrics do not indicate an optimizer blow-up: max KL stayed
below `0.007` in the reviewed runs against `target_kl=0.03`. The failure is
behavioral and task-structural: reward/proxy changes did not convert into
finishes or even reliable gate traversal.

## Subagent Findings

| Reviewer | Evidence | Conclusion | Confidence |
| --- | --- | --- | --- |
| Evaluator metrics | Six evaluated trials, all `0%` success and `100%` crash; none beat `001` mean gates `0.85` | Open structural review | high |
| W&B curves | 005/006/007 reward movement without `passed_gate_rate` or `finished_rate` conversion; KL/clip stable | Open structural review; not a PPO-instability story | high |
| Reward-only failure audit | Numeric gates met: six evaluated trials, six distinct reward hypotheses, 210M command timesteps, target unmet | Open review, with caveat about formal packet ownership | high |
| Papers / technical reports | Existing research points first to curriculum/domain randomization, observation sufficiency, reward-event geometry, and control interface | Review those lanes before PPO/network changes | medium |
| Codebase diagnosis | Multiple parity and learnability risks found in evaluator/deploy, observation reconstruction, randomization, wrappers, safety limits, terminal semantics, action clipping | Investigate before more reward scaling | medium-high |

## Why Reward-Only Is Not Enough

Failed hypotheses:

- Baseline reward numbers.
- Gate acquisition plus safety scaling.
- Extended gate acquisition/safety continuation.
- Low-pressure completion-oriented probe.
- Safety/axis recovery probe.
- Axis-dominant controlled probe.

Signals that did not move enough:

- Evaluator `success_rate`: always `0.0`.
- Evaluator `crash_rate`: always `1.0`.
- Global best `mean_gates`: never exceeded `0.85`.
- W&B `race/finished_rate`: effectively zero.
- W&B `race/passed_gate_rate`: flat and very low.

Signals that moved but did not convert:

- 006 reduced `cmd_tilt_over_limit_frac` to `0.5880` and improved smoothness,
  but evaluator success stayed `0.0` and mean gates stayed `0.70`.
- 007 pushed axis/stage reward, but best mean gates reached only `0.75` and
  command tilt worsened to `0.8554`.
- Training reward improved in several runs, but evaluator success and finish
  rate did not follow.

Remaining uncertainty:

- Whether the failure is dominated by randomized task difficulty, observation
  parity/sufficiency, event geometry, control dynamics, evaluator parity, or a
  combination.
- Whether 5M checkpoints omitted from the default 007 evaluator would expose a
  brief transient improvement. This is unlikely to change the structural
  conclusion because 10M through final all failed, but it is easy to verify if
  desired.

## Candidate Structural Review Lanes

These are review lanes, not approved changes.

| Candidate review lane | Evidence | Expected benefit | Risk | Minimal validation |
| --- | --- | --- | --- | --- |
| Difficulty, curriculum, and domain-randomization staging | Full Level3 randomization plus latency/noise/dynamics robustness while all trials crash | Determine whether the training distribution is too hard before basic gate traversal | Overfitting to easier starts if staged badly | Run a no-training dataset/rollout audit of first-gate distance/orientation and crash locations; propose staged configs only after review |
| Observation sufficiency and train/inference parity | Training uses `RaceObservation`; inference reconstructs observation manually | Catch feature-order, scaling, history, gate-corner, obstacle-heading mismatches | Touches policy input contract and checkpoints | Write parity tests comparing train observation builder and inference vector on identical env states |
| Reward event geometry and evaluator alignment | Reward coefficients moved proxies but not finishes; gate/front/back/stage events may not match evaluator success | Verify crossing, wrong-side, target-gate update, final-gate done semantics | Could alter reward structure, outside Stage 1 | Instrument event counters and deterministic traces before modifying reward channels |
| Evaluator/deploy parity | Selected-checkpoint evaluator mutates `ppo_level2_inference.MODEL_NAME`; config uses `ppo_level3_inference.py` with a hardcoded checkpoint | Ensure loop evaluation matches deploy-style controller behavior | May reveal current loop metric mismatch | Run parity eval using explicit Level3 inference path and checkpoint injection |
| Randomization geometry audit | Track randomizer samples its own `start_xy`; drone start remains near origin | Check whether first-gate geometries are learnable and intended | Reducing randomization may reduce robustness | Sample and plot first-gate positions/orientations relative to drone start; summarize distributions |
| Training wrappers versus evaluation env | Training includes thrust sag, latency, response lag, observation noise; selected evaluation uses raw Gym env | Decide whether robustness wrappers are useful or premature burden | Removing robustness may hurt final transfer | Compare short controlled training/eval diagnostics with wrappers off/on after packet approval |
| Safety limits and termination contract | TOML safety limits differ from fixed simulation termination bounds | Align task contract and failure labels | Changing limits can inflate metrics artificially | Add failure-reason taxonomy and compare configured vs actual termination triggers |
| Action distribution and clipping | PPO samples unbounded Normal while env clips actions | Investigate saturation/logprob mismatch under high command tilt | PPO/action-interface change is broad | Log action saturation fractions and command clipping before changing policy distribution |

## Decision

Stage 1 reward-number search should stop here. The next Codex stage may propose
specific structural diagnostics or small structural changes, but it must name
them explicitly and keep them out of reward-only trial records.

Immediate recommended next action:

1. Build a failure-taxonomy/evaluator-parity diagnostic packet.
2. Add read-only or test-only instrumentation where possible.
3. Propose at most one narrow Stage 2 change after diagnostics identify the
   most likely bottleneck.

Rollback condition for any Stage 2 experiment:

- If a structural change does not improve `success_rate`, `mean_gates`, or a
  directly linked failure-taxonomy metric within one bounded evaluation, revert
  the change or keep it behind an explicit experiment flag.
