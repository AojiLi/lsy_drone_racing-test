# Loop088 Decision: Continue V28 With Gate-Conversion Reward Adjustment

Decision: `change_reward_or_training_numbers`

## Verdict

Do not accept loop088 as solved. The target remains hard-eval success rate
>=60% with mean successful time <=7.0s on unchanged `config/level3_dr.toml`.

Do not abandon v28 yet. Loop088 did not beat the loop052 validation anchor, but
it produced enough positive signal to justify one bounded continuation from its
best checkpoint with a gate-conversion reward adjustment.

## Evidence

Best loop088 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt`

| Checkpoint | Success | Crash | Mean gates | Mean success time |
| --- | ---: | ---: | ---: | ---: |
| loop052 validation anchor | 0.20 | 0.80 | 1.47 | 6.858s |
| loop087 beta=0.10 final | 0.17 | 0.83 | 1.50 | 6.991s |
| loop088 4M best | 0.19 | 0.81 | 1.57 | 6.846s |
| loop088 final | 0.17 | 0.83 | 1.42 | 6.752s |

Loop088 4M improved over loop087 final by +2pp success, -2pp crash, +0.07
mean gates, and faster successful runs. It remains below loop052 by -1pp
success and +1pp crash, so global best stays loop052.

## Subagent Synthesis

Evaluator metrics:

- not target met;
- use loop088 4M, not final;
- failures remain dominated by `bounds_or_ground`;
- gate0 failures improved somewhat, but failures shifted into gate1/gate2;
- recommends `change_reward_or_training_numbers`.

W&B/PPO diagnostics:

- PPO looks numerically stable;
- no silent PPO hyperparameter change is justified;
- teacher retention is healthy: teacher KL down, action MSE down, agreement up;
- reward/retention did not strongly convert to hard-eval success;
- recommends gate-acquisition reward pressure.

Structure/research synthesis:

- v28 is not proven good enough, but it is not structurally disproven;
- success24 retention plus bounds replay improved gate progress without
  destabilizing retention;
- recommends one bounded v28 continuation before changing lane.

Main-agent decision:

Continue the same v28 data-correction lane from loop088 4M, but adjust reward
numbers toward gate acquisition/conversion. This reconciles the evaluator and
W&B recommendation to increase gate pressure with the structure review's
recommendation not to abandon v28 yet.

## Approved Next Chunk

Use exactly one bounded train/evaluate chunk:

- structural hypothesis: `v28_success24_retention_bounds_replay_5m`
- proposal name:
  `structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m`
- initial checkpoint: loop088 4M, not loop088 final
- train timesteps: 5M
- checkpoint interval: 1M
- hard eval: unchanged `config/level3_dr.toml`
- seed protocol: dev-to-validation; no final_locked seeds
- W&B project: `ADR-PPO-Racing-Level3`

Approved parameter overrides:

- `gate_stage_coef=13`
- `gate_axis_coef=24`
- `gate_front_bonus=5`
- `gate_bonus=200`
- `gate_back_bonus=35`
- `finish_bonus=175`
- `time_penalty=0.02`

Keep unchanged:

- observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- teacher KL beta: 0.10
- success24 retention dataset
- train_pool bounds failure replay profile
- PPO optimizer/training structure
- `config/level3_dr.toml` track geometry and randomization

## Approved Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --override-state-hold \
  --structural-hypothesis v28_success24_retention_bounds_replay_5m \
  --proposal-name structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop088_continue_v28_gate_conversion_reward_adjust.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_v27_retention_data_audit_success24.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Stop/Continue Gate After Next Chunk

After the chunk, run analyzer and exactly three reviews again.

Prefer continuing v28 only if at least one validation checkpoint shows:

- success rate >=0.20 with crash <=0.80, or
- mean gates clearly above 1.57 without worsening success below 0.19, or
- a meaningful reduction in `bounds_or_ground` failures without retention
  collapse.

Hold or change lane if the next chunk remains below 0.20 success, crash remains
above 0.80, and gate progress does not improve.
