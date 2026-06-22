# Loop057 Subagent Reviews

Date: 2026-06-21

Scope:

- Target hard eval remains `config/level3_dr.toml`.
- Level3 track geometry and randomization remain unchanged.
- The latest analyzed trial is
  `level3_loop_057_structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m`.

## evaluator_metrics

Key finding:

V8 deserves a guarded 60M maturation, not rejection or reward-number changes
yet. It is not a new global best, but loop057 has non-zero hard-eval success
and recovered loop052-level mean gates at 25M.

Evidence:

| Checkpoint | Success | Crash | Timeout | Mean gates | Success time |
|---|---:|---:|---:|---:|---:|
| 10M | 5% | 95% | 0% | 1.05 | 6.30s |
| 15M | 5% | 95% | 0% | 0.95 | 6.90s |
| 20M | 15% | 85% | 0% | 1.35 | 7.99s |
| 25M | 15% | 85% | 0% | 1.40 | 6.15s |
| final | 5% | 95% | 0% | 1.00 | 6.72s |

Compared with loop052 final, v8 is weaker on success/crash: `0.15/0.85`
versus `0.20/0.80`, but comparable on mean gates and faster on successful
episodes.

Recommended next action:

`continue_same_hypothesis`: mature v8 to 60M from the loop057 25M checkpoint.
Do not switch reward numbers from evaluator evidence alone.

Rollback:

Rollback to loop052/v5 or change lane if 60M does not beat loop052 on hard
eval: success must exceed `0.20`, or tie `0.20` with crash `<=0.80`, mean gates
`>1.40`, and success time `<=7.0s`.

## wandb_ppo_diagnostics

Key finding:

Loop057 is a W&B/PPO non-conversion run. Training reward and a few approach
metrics moved, but pass/finish/gate-cross rates stayed effectively flat, PPO
updates became tiny, and hard eval did not beat loop052. W&B alone does not
justify maturing v8 to 60M.

Evidence:

- W&B synced and training completed `29,982,720` steps in `2776s`.
- `train/reward` was noisy/up in sampled history, but not stable.
- Reward components did not convert: `gate_bonus` and small finish signal rose,
  but crash and smooth penalties worsened.
- Race metrics stayed flat: `passed_gate_rate` tail `0.008423`,
  `finished_rate` tail `0.000326`, `gate_plane_cross_rate` tail `0.001973`,
  `crashed_rate` tail `0.006826`, timeout `0`.
- PPO updates were conservative: `approx_kl` tail `0.001643` versus
  `target_kl=0.03`, `clipfrac` tail `0.000269`, last `0`; entropy increased
  and value loss stayed high.
- Hard eval peaked at 25M and final regressed.

Recommended next action:

`hold_for_more_analysis` from the W&B/PPO side. Do not continue v8 solely on
W&B evidence.

Rollback:

Rollback to loop052/global-best lineage if a follow-up again shows flat
`passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` with success
`<=0.15` or crash `>=0.85`.

## structure_research_synthesis

Key finding:

loop057 should trigger `hold_for_more_analysis`, not maturation,
reward retuning, PPO-number changes, or another unpacketed structural run.

Evidence:

- v8 best hard eval: success `0.15`, mean time `6.153s`, crash `0.85`, mean
  gates `1.40`.
- This hits the v8 rollback shape: success `<=0.15` and crash `>=0.85`.
- State best remains loop052: success `0.20`, mean time `6.975s`, crash
  `0.80`, mean gates `1.40`.
- W&B did not show conversion: pass/finish signals stayed effectively flat.
- Repeating obvious knobs is already falsified: loop051/054 gate pressure,
  loop055 PPO pressure, loop056 soft-centerline/plane shaping, loop057 v8
  observation.

Recommended next action:

`hold_for_more_analysis`. Do not continue v8 to 60M and do not use the
analyzer's gate-acquisition reward command.

Rollback:

Rollback anchor remains loop052 final. Future promotion should require beating
loop052, not just matching gates with worse success/crash.

## Main-Agent Read

The three reviews disagree:

- evaluator metrics: continue v8 guarded maturation;
- W&B/PPO: hold;
- structure/research: hold.

The main-agent decision weighs the Level2 step-curve rule and the user's
standing preference to avoid rejecting promising branches at 30M. Since v8 has
non-zero hard-eval success, mean gates equal to loop052 at 25M, and a diagnostic
taxonomy signal, one bounded maturation is allowed. It must not be treated as
accepted, and it must not change reward/PPO numbers.
