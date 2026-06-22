# Main-Agent Decision After loop034

Date: 2026-06-20

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue
  `level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m`
  unchanged.
- Do not promote loop034 as the new base checkpoint.
- Keep loop020 25M as the trusted rollback anchor/global best.

## Evidence

Latest analyzed trial:

- Trial:
  `level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m`

Best loop034 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_step_015000000.ckpt`
- Success rate: `0.05`
- Mean successful time: `5.08s`
- Crash rate: `0.95`
- Mean gates: `0.90`
- Command tilt over-limit fraction: `0.44113195808597394`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`
- Command tilt over-limit fraction: `0.5800860395510893`

## Reviewer Synthesis

Evaluator metrics:

- loop034 should not continue or mature unchanged.
- It improves smoothness and command saturation, but it regresses from loop020
  on success, crash rate, and mean gates.
- loop025 remains a stronger smoothing-related result than loop034:
  `0.10` success and `1.10` mean gates versus loop034's `0.05` and `0.90`.

W&B/PPO diagnostics:

- Mild low-pass reduced command and physical tilt pressure:
  - command tilt over-limit improved from loop020's `0.580` to loop034's
    `0.441`;
  - mean max command tilt improved from `70.65deg` to `58.90deg`;
  - physical tilt over-limit improved from `0.218` to `0.109`.
- This did not convert into hard-eval gate passage:
  - W&B `passed_gate_rate` tail mean stayed weak at about `0.003805`;
  - `finished_rate` tail mean stayed `0.0`;
  - hard-eval mean gates dropped to `0.90`.
- PPO metrics were not the primary failure:
  - KL and clip fraction stayed low;
  - explained variance was stable;
  - entropy remained high.

Structure/research synthesis:

- Do not launch another numeric reward-only tweak. The analyzer's generic gate
  acquisition suggestion repeats loop027's failed direction.
- Do not launch another low-pass/controller smoothing lane without a new
  mechanism for gate pass conversion.
- The next runnable lane should be designed around stable gate crossing,
  likely beyond reward/PPO/low-pass numbers alone: action parameterization,
  pass-event/trajectory supervision, or a reward/observation structure that
  explicitly handles gate-frame crossing and obstacle/frame collisions.

## Additional 40-Seed Diagnostic

The main agent ran a 40-seed crash taxonomy on loop034's best checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_step_015000000.ckpt`
- Output:
  `experiments/level3_ppo_loop/diagnostics/level3_loop_034_15M_v5_mild_lowpass_crash_taxonomy_40seed_summary.json`

Summary:

- Successes: `2/40`
- Success rate: `0.05`
- Crash rate: `0.95`
- Mean successful time: `5.93s`
- Crashes by target gate:
  - gate 0: `15`
  - gate 1: `15`
  - gate 2: `7`
  - gate 3: `1`
- Main likely crash objects:
  - obstacles: `18` total across obstacle 0/1/2
  - gate 1 left: `5`
  - gate 2 top: `5`
  - gate 0 frame parts: multiple bottom/left/right/top hits

Interpretation:

- The failure is not just speed or late-track navigation.
- The policy is still colliding around the first two gates and nearby
  obstacles/frames.
- Smoother commands alone can reduce saturation while still producing a
  smoother crash policy.

## Rejected Next Moves

Rejected:

- continue loop034 unchanged;
- mature loop034 to 60M-90M;
- tune another low-pass alpha without a new gate-conversion mechanism;
- repeat loop027's gate-acquisition reward-number rebalance;
- retry loop032 no-wrapper curriculum;
- modify Level3 track geometry or randomization.

## Required Next Work Before Training

Create a short synthesis packet under `experiments/level3_ppo_loop/research/`
before launching another training chunk. It must define one concrete next
structural lane and include:

- why loop020 still passes gates better than smoother/PPO-pressure variants;
- how the new lane targets stable gate crossing rather than only W&B proxy
  movement;
- what code/config parameters are changed;
- why `config/level3_dr.toml` remains the hard-eval target and is not modified;
- promotion/rollback criteria against loop020, loop025, loop033, and loop034.

Allowed next decision after that synthesis:

- `launch_named_structural_lane` only if the lane has a concrete mechanism and
  can be represented in code/config without changing the Level3 track;
- otherwise remain in `hold_for_more_analysis`.
