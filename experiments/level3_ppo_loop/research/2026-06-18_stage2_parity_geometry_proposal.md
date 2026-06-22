# Level3 PPO Stage 2 Proposal: Parity And First-Gate Geometry Diagnostics

## Scope

This packet authorizes diagnostic work only. It does not approve reward,
observation, PPO, curriculum, training-structure, network, or environment
changes, and it does not start another train/eval chunk.

The Stage 1 reward-number loop is exhausted. The current global incumbent is:

```text
lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Current target remains unmet:

- Required success rate: `>= 0.60`
- Required mean successful time: `<= 7.0s`
- Best measured success rate: `0.0`
- Best measured mean successful time: `null`
- Best measured mean gates: `0.85`

## Why This Proposal Exists

Six evaluated active-reward-only trials all produced `0%` evaluator success and
`100%` crash rate. The latest crash taxonomy shows that both the incumbent and
latest probe still crash in `40/40` diagnostic episodes. Failures concentrate
while targeting gates `0` and `1`, and crash positions are usually before the
active target gate plane.

The next useful work is not another blind reward coefficient move. The next
work should answer two narrow questions:

1. Does the Level3 deploy-style controller path evaluate exactly the checkpoint
   we intend to test?
2. Does the randomized Level3 first-gate geometry create an initial approach
   distribution that explains the repeated early crashes?

## Local Code Evidence

Evaluator/checkpoint-injection evidence:

- `scripts/evaluate_level2_selected_ppo.py` imports
  `ppo_level2_inference` and injects the checkpoint by mutating
  `ppo_level2_inference.MODEL_NAME`.
- `scripts/analyze_level2_ppo_crashes.py` does the same for crash taxonomy.
- `config/level3_dr.toml` points to `ppo_level3_inference.py`.
- `ppo_level3_inference.py` defaults to
  `checkpoints/level3_DR_initial/level3_DR_initial_step_040000000.ckpt`.
- `ppo_level2_inference.py` and `ppo_level3_inference.py` have effectively the
  same controller logic, so the main unresolved parity risk is checkpoint
  injection/default checkpoint selection, not action or observation code
  divergence.

Randomized geometry evidence:

- Level3 full-track randomization samples its own `start_xy` inside
  `build_random_track_fn`, then places gate `0` relative to that sampled point.
- The actual drone start in `config/level3_dr.toml` is near `[0, 0, 0]` with
  only a small `drone_pos` randomization.
- Full-track randomization is followed by per-gate/per-obstacle perturbations.
  Observations report nominal object positions until objects enter sensor
  range, while actual positions may differ after perturbation.

This combination may be intended, but it must be measured before we choose a
structural training change.

## Approved Diagnostic 1: Level3 Checkpoint-Injection Parity

Goal:

- Verify that a selected Level3 checkpoint can be evaluated through the
  `ppo_level3_inference.py` controller path with explicit checkpoint injection.
- Compare the result against the current selected-checkpoint evaluator path.

Proposed diagnostic implementation:

- Add or adapt a diagnostic evaluator flag that can choose the inference module:
  `ppo_level2_inference` or `ppo_level3_inference`.
- Inject the same checkpoint into the selected module before controller
  construction.
- Keep seeds, config, environment construction, controller reset, and metrics
  unchanged.

Recommended parity check:

```text
pixi run -e gpu python scripts/evaluate_level2_selected_ppo.py \
  --config level3_dr.toml \
  --seed-start 1 \
  --num-seeds 20 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_parity_level2_path_001 \
  lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt
```

Then run the equivalent Level3-controller diagnostic and compare:

- `success_rate`
- `crash_rate`
- `mean_gates`
- `mean_time_s_success`
- per-seed gates/time/crash labels

Acceptance rule:

- If the metrics and per-seed outcomes match, close this parity risk and use the
  current evaluator numbers as valid for this checkpoint.
- If they differ, standardize future Level3 evaluations on explicit
  `ppo_level3_inference.py` checkpoint injection before any more training.

## Approved Diagnostic 2: First-Gate Randomized Geometry Sampler

Goal:

- Sample the actual reset distribution for Level3 first-gate geometry.
- Measure whether gate `0` is often placed in a difficult relation to the real
  drone start.
- Compare sampled geometry with crash taxonomy rows for seeds `1..40`.

Minimum fields to record per sampled reset:

- seed
- drone start position
- actual gate `0` position and quaternion
- observed gate `0` position at reset
- whether gate `0` is initially visited/visible
- vector from drone start to actual gate `0`
- horizontal distance to gate `0`
- vertical offset to gate `0`
- gate-local position of drone start relative to gate `0`
- gate `0` yaw
- obstacle `0` position and distance to the start-to-gate corridor

Recommended sample size:

- `500` to `2000` resets for summary statistics.
- Also force seeds `1..40` to align with existing crash taxonomy.

Useful summaries:

- percentiles for start-to-gate distance
- percentiles for start-to-gate lateral offset in gate-local frame
- percentiles for vertical offset
- percentage of resets where gate `0` is outside sensor range at reset
- percentage of resets where obstacle `0` lies near the start-to-gate corridor
- correlation between crash taxonomy seeds and extreme geometry quantiles

Acceptance rule:

- If early-crash seeds cluster in extreme first-gate geometry, the next Stage 2
  training proposal should be a narrow difficulty-staging/curriculum experiment.
- If geometry is not extreme, prioritize observation/event parity diagnostics
  before curriculum.

## Not Approved By This Packet

This packet does not approve:

- changing reward channels or coefficients;
- changing PPO hyperparameters;
- changing observation layout or feature order;
- changing the policy network;
- disabling or reducing randomization for training;
- adding curriculum or staged configs;
- changing gate-pass, crash, or termination semantics;
- starting a new train/eval chunk.

## Next Decision Gate

After both diagnostics are complete, write a short Stage 2 decision report with:

- parity result;
- geometry sampler result;
- recommended single next action;
- rollback/hold criterion.

Only then should Codex propose one narrow Stage 2 experiment.
