# Main-Agent Decision After Loop059 More Analysis

Date: 2026-06-21

## Decision

`launch_named_structural_lane`

Named lane:

`v9_gate_aperture_margin_obs_from_loop052_30m`

## Prior Decision

The immediate post-loop059 decision packet was:

`experiments/level3_ppo_loop/decisions/2026-06-21_loop059_reject_low_entropy_hold_for_new_structural_packet.md`

That packet rejected low-entropy continuation and held for a new structural
packet. This packet is the follow-up structural packet.

## Evidence

Loop059 analysis:

`experiments/level3_ppo_loop/analysis/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_analysis.md`

Loop059 subagent reviews:

`experiments/level3_ppo_loop/analysis/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_subagent_reviews.md`

Loop059 crash taxonomy:

`experiments/level3_ppo_loop/diagnostics/level3_loop_059_final_20seed_crash_taxonomy_summary.json`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-21_loop059_gate_aperture_margin_observation_synthesis.md`

## Rationale

Loop059 lowered entropy and improved some training reward proxies, but hard eval
regressed. This rejects further low-entropy exploitation.

The recent loop052-derived sequence has also rejected nominal maturation, mild
gate pressure, PPO update pressure, soft-centerline/light-plane shaping, v8
obstacle-corridor observation, and v8 maturation.

Crash taxonomy now points to a specific structural gap:

- loop059 final has `18 / 20` crashes;
- crashes concentrate on gate0 and gate2;
- nearest gate part is right side in `10 / 18` crashes;
- likely objects include obstacle2, obstacle0, obstacle3, and right gate-frame
  hits.

v8 appended obstacle geometry in the gate corridor but did not directly expose
square gate-aperture margins. The next bounded test is to append explicit
current-gate aperture margin features while keeping loop052 reward/PPO/control
settings fixed.

## Approved Next Experiment

Proposal:

`v9_gate_aperture_margin_obs_from_loop052_30m`

Observation layout:

`level3_gate_aperture_margin_2obs_local_history_v9`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Training setup:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Reward structure: `legacy_staged`
- Train timesteps: `30_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Keep fixed from loop052:

- reward numbers;
- controller settings;
- learning rate;
- entropy coefficient;
- update epochs;
- minibatches;
- target KL;
- network size.

Only structural change:

- append a 9-float gate-aperture margin block to the v5 local observation.

## Required Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v9_gate_aperture_margin_obs_from_loop052 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_059_structural_v5_loop052_low_entropy_exploitation_20m_analysis.md \
  --analysis-packet experiments/level3_ppo_loop/diagnostics/level3_loop_059_final_20seed_crash_taxonomy_summary.json \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_loop059_gate_aperture_margin_observation_synthesis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop059_launch_gate_aperture_margin_observation_lane.md
```

If dry-run passes, launch the same command without `--dry-run`.

## Promotion And Rollback

Promote if the best hard-eval checkpoint reaches at least one:

- success `>0.20`;
- success `0.20` with mean gates `>1.40` and crash `<=0.80`;
- mean gates `>1.45` with nonzero success;
- right-side gate-frame crash share decreases materially versus loop059 while
  success stays at least `0.20`.

Reject if:

- all checkpoints stay `<=0.15` success;
- mean gates stay below `1.40`;
- crash stays `>=0.85`;
- W&B gate/finish signals stay flat;
- crash taxonomy still concentrates on right gate-frame hits without evaluator
  improvement.

## Boundaries

- Do not modify `config/level3_dr.toml` track geometry or randomization.
- Do not edit `notebooks/train_level3_ppo.ipynb`.
- Do not continue v8.
- Do not continue the low-entropy lane.
- Do not change reward numbers in this lane.
- Do not run more than one train/evaluate chunk before analyzer and review.
