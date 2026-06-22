# Main-Agent Decision After loop046

Date: 2026-06-20

## Trial

- Trial id:
  `level3_loop_046_v7_10m_stability_retune_from_loop045_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_046_v7_10m_stability_retune_from_loop045_30m`
- Best loop046 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_046_v7_10m_stability_retune_from_loop045_30m/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_step_020000000.ckpt`
- Hard-eval success rate: `0.10`
- Mean successful time: `5.95s`
- Crash rate: `0.90`
- Mean gates: `1.05`
- Target met: `false`

Global best remains:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

with success `0.15`, mean successful time `6.366666666666667s`, crash `0.85`,
and mean gates `1.45`.

## Subagent Findings

- `evaluator_metrics`:
  recommended `continue_same_hypothesis` weakly and metrics-only, because
  loop046 still has non-zero hard-eval success at 10M and 20M. It explicitly
  said continuation should start from the 20M checkpoint, not final, and noted
  that loop046 is weaker than both loop045 and loop020 on success, crash, and
  mean gates.
- `wandb_ppo_diagnostics`:
  recommended `launch_named_structural_lane`. PPO was numerically stable but
  effectively under-updating: tail KL was about `0.000004`, clip fraction was
  `0`, policy loss was near zero, entropy rose, finish rate stayed `0`, and
  passed-gate/plane-crossing signals did not convert into hard-eval progress.
- `structure_research_synthesis`:
  recommended `hold_for_more_analysis`. The v7 stability-retune branch hit
  rollback criteria: lower hard-eval conversion than loop045 and loop020, late
  checkpoint collapse to `0%` success, and no launch-ready next structural
  hypothesis yet.

## Main-Agent Decision

Selected decision:

`hold_for_more_analysis`

## Rationale

The metrics-only continuation argument is not ignored, but it is not strong
enough to justify another same-family v7 maturation:

- loop046 best success is `0.10`, below loop045 `0.15` and loop020 `0.15`.
- loop046 best mean gates is `1.05`, below loop045 `1.20` and loop020 `1.45`.
- loop046 best crash rate is `0.90`, worse than loop045 and loop020 `0.85`.
- 25M and final collapse to `0.00` success and `1.00` crash.

The stability retune did reduce command saturation relative to loop045, but it
did not produce gate-pass conversion. Within loop046, command tilt over-limit
still increased from `0.38` at 10M to `0.46` at final, while W&B showed flat
gate-plane crossing and zero finish conversion.

This means the next action should not be:

- continuing loop046 unchanged;
- restarting from loop046 final;
- applying another generic reward-number tweak;
- accepting W&B reward movement as progress.

The next useful step is a short structural lane packet focused on gate-pass
conversion. It must explicitly decide whether to:

- return to the stronger v5/loop020 checkpoint family;
- keep v7 but change PPO/control damping so policy updates are not frozen;
- use one of the existing reward structures such as `gate_potential`,
  `direct_aperture`, or `soft_centerline_followthrough`;
- or define a new minimal reward/controller change.

No Level3 track geometry, gate layout, obstacle layout, or randomization may be
changed.

## Next Command

No training command is approved by this packet.

Before the next train/evaluate chunk, write a named structural-lane packet under
`experiments/level3_ppo_loop/research/` or `experiments/level3_ppo_loop/decisions/`
that includes:

- lane name;
- start checkpoint;
- observation layout;
- reward structure;
- PPO/training parameter changes;
- controller/action-envelope changes;
- hard-eval promotion and rollback criteria;
- exact dry-run command.

The next training command must attach both:

```bash
--analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_analysis.md
--approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop046_hold_for_structural_lane_packet.md
```

and, if a new structural lane packet is created, attach it as a research or
approval packet according to the loop script's supported flags.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another same-hypothesis v7 stability-retune chunk.
- Do not use loop046 final as a starting checkpoint.
- Do not launch a structural lane until it is named and recorded.
