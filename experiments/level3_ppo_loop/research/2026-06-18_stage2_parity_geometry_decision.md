# Level3 PPO Stage 2 Decision: Parity Closed, Geometry Is The Next Bottleneck

## Scope

This is a diagnostic decision report. It does not approve reward, PPO,
observation, network, environment, curriculum, or training-structure changes.
It does not start a new train/eval chunk.

## Current Status

The target is still unmet:

- Required: `success_rate >= 0.60`
- Required: `mean_time_s_success <= 7.0s`
- Current best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Current best evaluator metrics:
  `success_rate=0.0`, `crash_rate=1.0`, `mean_gates=0.85`,
  `mean_time_s_success=null`

Stage 1 reward-only tuning remains stopped.

## Diagnostic 1: Controller Path Parity

Artifacts:

- Level2-path summary:
  `experiments/level3_ppo_loop/diagnostics/level3_parity_level2_path_001_summary.csv`
- Level2-path episodes:
  `experiments/level3_ppo_loop/diagnostics/level3_parity_level2_path_001_episodes.csv`
- Level3-path summary:
  `experiments/level3_ppo_loop/diagnostics/level3_parity_level3_path_001_summary.csv`
- Level3-path episodes:
  `experiments/level3_ppo_loop/diagnostics/level3_parity_level3_path_001_episodes.csv`

Result:

- Same checkpoint: `level3_loop_001_baseline_final.ckpt`
- Same config: `level3_dr.toml`
- Same seeds: `1..20`
- Per-seed mismatches across success/crash/timeout/steps/gates/time/smooth/tilt
  fields: `0`
- Aggregate metrics matched exactly apart from the intentional
  `inference_module` label.

Conclusion:

- The current selected-checkpoint evaluator is valid for the incumbent
  checkpoint when explicit injection is used.
- The main parity risk is closed for this checkpoint: `ppo_level2_inference`
  and `ppo_level3_inference` produce identical outcomes under the parity test.
- Keep the new evaluator `--inference-module` flag for future Level3
  diagnostics, but do not treat controller path divergence as the active
  bottleneck.

## Diagnostic 2: First-Gate Geometry

Artifacts:

- Samples:
  `experiments/level3_ppo_loop/diagnostics/level3_first_gate_geometry_500_samples.csv`
- Summary:
  `experiments/level3_ppo_loop/diagnostics/level3_first_gate_geometry_500_summary.json`

Sample:

- Config: `level3_dr.toml`
- Seeds: `1..500`
- Crash overlap: existing incumbent crash taxonomy seeds `1..40`

Key results:

| Metric | Value |
| --- | ---: |
| Gate 0 visible at reset | `17.0%` |
| Gate 0 inside sensor range by XY distance | `17.0%` |
| Obstacle 0 within `0.2m` of start-to-gate corridor | `34.8%` |
| Obstacle 0 within `0.4m` of start-to-gate corridor | `67.2%` |
| Gate 0 horizontal distance median / p95 | `1.287m` / `2.107m` |
| Gate-local start `x` median / p95 | `-0.918m` / `0.476m` |
| Gate-local absolute lateral offset median / p95 | `0.590m` / `1.521m` |
| Observed-vs-actual gate 0 XY error median / p95 | `0.108m` / `0.175m` |

Crash-overlap observations for seeds `1..40`:

- Target-gate `0` crash rows: `17`
  - mean first-gate distance: `1.147m`
  - mean absolute gate-local lateral offset: `0.773m`
  - mean obstacle-corridor distance: `0.280m`
  - reset visibility rate: `23.5%`
- Target-gate `1` crash rows: `17`
  - mean first-gate distance: `1.262m`
  - mean absolute gate-local lateral offset: `0.624m`
  - mean obstacle-corridor distance: `0.344m`
  - reset visibility rate: `5.9%`
- Target-gate `2` crash rows: `6`
  - mean first-gate distance: `1.118m`
  - mean absolute gate-local lateral offset: `0.362m`
  - mean obstacle-corridor distance: `0.474m`
  - reset visibility rate: `33.3%`

Interpretation:

- The crash seeds do not prove that only extreme first-gate layouts fail; the
  whole reset distribution is hard.
- The first gate is usually not visible at reset, so the policy often begins
  with nominal object positions.
- Actual gate 0 can differ from the observed nominal gate by roughly `10cm`
  median XY and up to about `20cm` in this sample.
- The start-to-gate corridor often contains obstacle 0, by design, which makes
  early gate acquisition a simultaneous gate-and-obstacle problem.
- The policy's repeated `0%` success is more consistent with a learnability /
  staged-difficulty bottleneck than with an evaluator controller-path mismatch.

## Decision

Do not continue Stage 1 reward-only search.

Do not launch another 30M train/eval chunk from the current loop command yet.

The next useful artifact should be a narrow Stage 2 experiment packet for
first-gate acquisition difficulty staging. That packet should propose one
bounded experiment and must include:

- the exact config/code change;
- why the change targets gate acquisition rather than speed;
- how it preserves final Level3 evaluation as the acceptance gate;
- the rollback condition;
- the W&B run name and evaluation command.

Recommended first experiment family:

- Keep PPO architecture and active reward numbers fixed.
- Temporarily reduce early task difficulty only enough to test learnability:
  either first-gate visibility/staging or reduced initial full-track
  randomization.
- Evaluate the resulting checkpoint only on the original `level3_dr.toml`
  hard gate.

Hold condition:

- If the next packet cannot isolate one narrow staging change, hold rather than
  launching a broad structural run.
