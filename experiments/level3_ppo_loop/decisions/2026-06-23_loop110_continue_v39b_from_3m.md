# Decision: Continue V39 From Loop110 3M

Decision: `continue_same_hypothesis`

Pending gate resolved by this packet:

- trial:
  `level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_analysis.md`
- subagent synthesis:
  `experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_subagent_reviews.md`

Approved continuation lane:

```text
v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v38 or start from loop109 checkpoints.
- Do not continue loop110 final.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

Best loop110 / v39 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt`
- success: `21/100`
- mean gates: `1.64`
- crash rate: `79%`
- mean successful time: `6.756s`

Dense loop110 milestones:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 1M | 15% | 1.40 | 85% | 6.673s |
| 2M | 17% | 1.51 | 83% | 6.938s |
| 3M | 21% | 1.64 | 79% | 6.756s |
| 4M | 13% | 1.46 | 87% | 6.395s |
| final | 17% | 1.53 | 83% | 6.624s |

Reference checkpoints:

- loop107 1M: `21%` success, `1.66` mean gates, `79%` crash, `7.578s`;
- loop101 final: `20%` success, `1.69` mean gates, `80%` crash, `6.873s`.

loop110 3M tied the success/crash frontier and improved successful time, but it
did not beat the mean-gate frontier. The success-seed set changed: 8
validation seeds were newly solved relative to loop107 1M, while 8 old success
seeds were lost. This is promising enough for a short continuation, but not a
promotion.

## Reviewer Synthesis

- Evaluator reviewer: mature v39 from loop110 3M. Do not treat it as a solved
  or clearly superior checkpoint, and do not continue from final.
- W&B/PPO reviewer: PPO was stable but conservative. Reward/race signals moved
  mildly in the intended direction, but conversion remained weak.
- Structure reviewer: continue v39 from loop110 3M without changing reward
  numbers. First test whether the seed expansion reproduces before more reward
  scaling.

## Approved V39B Scope

`v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m`

- Student start:
  loop110 3M feed-forward MLP checkpoint.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Policy:
  `mlp_2x_tanh`; no GRU, no retention, no privileged critic.
- Controller:
  end-to-end PPO Actor only.
- Training horizon:
  bounded `3M` continuation with `0.5M` milestone checkpoints.
- Reward/training numbers:
  keep the v39 gate-acquisition numbers exactly:
  - `gate_stage_coef=13`
  - `gate_axis_coef=24`
  - `gate_front_bonus=5`
  - `gate_bonus=200`
  - `gate_back_bonus=35`
  - `finish_bonus=175`
  - `time_penalty=0.02`

## Promotion / Rejection Rule

Promote or mature further only if hard eval on `validation_unseen` shows one of:

- success `> 21%`;
- success `>= 21%` with mean gates above `1.66`;
- success `>= 20%` with mean gates above `1.69` and crash `<= 80%`;
- the loop110 seed expansion is preserved while crash decreases.

Reject v39b if it drifts below `20%` success, stays at or below `1.64` mean
gates with about `80%` contact crashes, or repeats the loop110 late-checkpoint
collapse.

## Next Command

After this packet is committed, dry-run then launch:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop110_continue_v39b_from_3m.md
```
