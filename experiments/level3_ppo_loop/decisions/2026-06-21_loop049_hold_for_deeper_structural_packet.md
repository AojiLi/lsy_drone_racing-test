# Main-Agent Decision After loop049

Date: 2026-06-21

## Trial

- Trial id:
  `level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m`

Best loop049 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_step_015000000.ckpt`

Hard-eval metrics:

- Success rate: `0.10`
- Mean successful time: `6.30s`
- Crash rate: `0.90`
- Timeout rate: `0.00`
- Mean gates: `1.05`
- Target met: `false`

Global best remains loop020:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`,
crash `0.85`, and mean gates `1.45`.

## Subagent Findings

- `evaluator_metrics` recommended `launch_named_structural_lane`.
  loop049 regressed against loop020, loop047, and loop048. The best checkpoint
  was only `0.10` success and `1.05` mean gates; final collapsed to `0.00`
  success and `1.00` crash.
- `wandb_ppo_diagnostics` recommended `hold_for_more_analysis`.
  Training reward rose, but `passed_gate_rate`, `finished_rate`, and
  gate-plane conversion stayed flat. PPO was numerically stable but weakly
  updating late; this is reward non-conversion, not classic PPO instability.
- `structure_research_synthesis` recommended `hold_for_more_analysis`.
  It concluded that local v5 PPO/controller isolation variants should stop and
  that the next useful step is a deeper structural packet, not another immediate
  20M-30M training command.

## Main-Agent Decision

Selected decision:

`hold_for_more_analysis`

## Rationale

Do not launch another train/evaluate chunk directly from loop049.

Reasons:

- loop049 failed the no-damping isolation hypothesis.
- It did not beat loop020 on success, mean gates, crash, score, or stability.
- Its final checkpoint collapsed to `0.00` success and `1.00` crash.
- loop047 and loop048 plateaued at `0.15` success and `1.25` mean gates.
- loop049 regressed to `0.10` success and `1.05` mean gates.
- Recent v5 local reward/controller/training variations, v6 next-gate
  observation, and v7 phase/progress observation have not improved the loop020
  frontier.
- The current failure mode is pass-through conversion, not successful-run speed.
  Successful episodes are already under `7s`; the blocker is success/crash/gate
  progress.

This means the next action must be a deeper named structural packet. It should
not be:

- continuing loop049;
- continuing loop047/048;
- resuming from loop049 final;
- running another automatic reward move;
- applying analyzer-style generic gate-acquisition reward numbers without a
  source-backed packet;
- changing `config/level3_dr.toml` track geometry or randomization.

## Required Next Work

Before another training chunk, write a deeper structural/research packet under
`experiments/level3_ppo_loop/research/` or `experiments/level3_ppo_loop/decisions/`.

The packet must include:

- lane name;
- start checkpoint, likely loop020 or the current global best;
- observation layout;
- reward structure;
- controller/inference changes if any;
- PPO/training-structure changes if any;
- exact train/eval command;
- W&B logging plan;
- hard-eval promotion and rollback criteria;
- why recent failed lanes do not already falsify the hypothesis.

The next lane should focus on pass-through conversion and survival through
gates, not successful-run speed.

## Constraints For The Next Lane

- Final acceptance remains hard eval on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not start from loop049 final.
- Do not use `--allow-step-curve-maturation` for loop049.
- Do not silently tune PPO structure. Changes to `learning_rate`, `ent_coef`,
  `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`
  require an explicit named structural/training packet.
- Use `--max-iterations 1`.
- Attach:

```bash
--analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_049_v5_loop020_moderate_ppo_no_damping_isolation_30m_analysis.md
--approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop049_hold_for_deeper_structural_packet.md
```

plus the new structural packet before any next training command.

## Promotion Criteria For Any Next Lane

Promote only if hard eval on `config/level3_dr.toml` beats the loop020 frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- success `0.15` with mean gates at least `1.45` and crash no worse than
  `0.85`; or
- success `0.15` with materially lower crash and no gate regression.

Reject quickly if:

- all checkpoints stay `<=0.10` success;
- crash stays `>=0.90`;
- final or late milestones collapse to `0.00` success;
- W&B reward rises but pass/finish/gate-plane conversion stays flat.

## Status

No next training command is approved by this packet.
