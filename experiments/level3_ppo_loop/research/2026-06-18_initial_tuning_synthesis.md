# Level3 PPO Tuning Synthesis: 2026-06-18 Initial Loop

## Local Evidence

- Last trial: none yet.
- Best checkpoint: none recorded in `state.json`.
- Existing warm-start candidate:
  `lsy_drone_racing/control/checkpoints/level3_DR_initial/level3_DR_initial_step_040000000.ckpt`.
- Current hard gate: success rate `>= 60%`, mean successful time `<= 7.0s`.
- W&B project: `ADR-PPO-Racing-Level3`.

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout,
  network/training structure, curriculum, or add new reward channels.
- Keep disabled reward channels at zero: `progress_coef`, `near_gate_coef`,
  `gate_plane_bonus`, `missed_gate_penalty`, and `obstacle_clearance_coef`.
- External evidence may choose how to scale active reward numbers only.

## External Evidence Considered

| Source | Relevant finding | Confidence | Link |
| --- | --- | --- | --- |
| Proximal Policy Optimization Algorithms | KL/clip behavior is useful as a diagnostic signal, but this loop will not tune PPO hyperparameters. | High | https://arxiv.org/abs/1707.06347 |
| CleanRL PPO docs | Track PPO losses, approximate KL, entropy, clip fraction, and rollout metrics to interpret reward-only runs. | High | https://docs.cleanrl.dev/rl-algorithms/ppo/ |
| Reaching the Limit in Autonomous Racing | Drone racing RL benefits from directly optimizing task-level racing behavior with domain randomization, not path-tracking proxies. | High | https://arxiv.org/abs/2310.10943 |
| sim2real_drone_racing | Zero-shot drone racing depends on domain randomization, but too much difficulty before competence can slow learning. | Medium | https://github.com/uzh-rpg/sim2real_drone_racing |
| CRL-Drone-Racing / curriculum racing | Staged gate traversal, obstacle avoidance, and speed pressure are useful reward-shaping axes. | Medium | https://arxiv.org/html/2602.24030v1 |
| Flightmare / high-throughput RL pattern | Evaluate multiple checkpoints and enough seeds before changing reward coefficients. | Medium | https://github.com/uzh-rpg/flightmare |

## Diagnosis

No local evaluation exists yet, so the first step should be measurement, not
aggressive tuning. The loop should run a baseline and evaluate multiple
checkpoints. After that, choose one change based on the dominant failure mode.

Primary unknown:

- Whether the current reward can learn gate traversal on full `level3_dr.toml`.

Secondary unknowns:

- Whether failures are mostly acquisition, safety/obstacle, reward balance, or
  speed after successful completion.
- Whether full domain randomization is too hard before the policy becomes
  competent.

What not to optimize yet:

- Do not increase `time_penalty` aggressively before success is reliable.
- Do not widen randomization before the policy can pass gates.
- Do not add path-tracking rewards unless evaluator failures show a specific
  path-following bottleneck.
- Do not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`,
  `num_minibatches`, `hidden_dim`, or `n_obs` in this loop.

## Next Experiment

Hypothesis:

- A baseline run with the current notebook-derived reward will reveal whether
  the first bottleneck is gate acquisition, safety, reward balance, or speed.

Start mode:

- Prefer warm-start from `level3_DR_initial_step_040000000.ckpt` for the first
  measured loop run because it gives faster signal.
- Run a separate `--from-scratch` baseline later if the warm-start result is
  ambiguous or if we need to validate reward learnability from random init.

Train timesteps:

- `20_000_000` for the first measured loop run.

Checkpoint interval:

- `5_000_000`, evaluating up to the latest 4 checkpoints.

Eval seeds:

- `20` first, then increase to `50` if a checkpoint looks close to the gate.

Parameter overrides:

- None for the first measured run.

Command:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --research-packet experiments/level3_ppo_loop/research/2026-06-18_initial_tuning_synthesis.md
```

## Decision Rule After Run

Use evaluator metrics first, W&B PPO metrics second.

| Trigger | Next move |
| --- | --- |
| `mean_gates < 2.5` and success low | Gate acquisition: raise `gate_stage_coef`, `gate_axis_coef`, `gate_front_bonus`, `gate_bonus`, `finish_bonus`, and keep `time_penalty` low. |
| `crash_rate > 0.25`, `worst_tilt_deg > 45`, or `cmd_tilt_over_limit_frac > 0.10` | Safety: raise `crash_penalty`, `obstacle_coef`, `act_coef`, `d_act_*`, `cmd_tilt_coef`, `rpy_coef`; lower `tilt_limit_deg`. |
| `success_rate >= 0.60` but `mean_time_s_success > 7.0` | Speed: raise `time_penalty` and `gate_axis_coef`; relax smoothness slightly. |
| W&B `losses/approx_kl > target_kl`, high clip fraction, or evaluator regression across later checkpoints | Diagnostic only: do not tune PPO hyperparameters in this loop. Prefer holding reward parameters and evaluating whether the last reward move caused regression. |
| Nominal `level3.toml` works but `level3_dr.toml` fails | Robustness diagnosis only: keep task reward stable, increase eval seeds, and identify failure mode before any user-approved framework change. |

## Candidate Follow-Up Commands

Gate acquisition:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

Safety:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --param d_act_xy_coef=0.10 \
  --param d_act_th_coef=0.10 \
  --param act_coef=0.02 \
  --param cmd_tilt_coef=0.9 \
  --param rpy_coef=0.9 \
  --param tilt_limit_deg=38 \
  --param tilt_excess_coef=16
```

Speed:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --param time_penalty=0.07 \
  --param gate_axis_coef=24 \
  --param act_coef=0.01 \
  --param d_act_xy_coef=0.05 \
  --param d_act_th_coef=0.05 \
  --param cmd_tilt_coef=0.55 \
  --param rpy_coef=0.55 \
  --param tilt_limit_deg=42
```

PPO instability diagnosis:

- Do not run a PPO hyperparameter command in this reward-only loop.
- Inspect whether instability appeared only after the latest reward move.
- If instability coincides with worse evaluator metrics, roll back to the
  previous best checkpoint and try a smaller reward-only change.

## Stop / Rollback Conditions

- Stop a branch if success drops while crash or timeout rises for two
  consecutive evaluated checkpoints.
- Roll back to the previous best checkpoint if a parameter branch improves
  W&B reward but worsens evaluator success/time.
- Increase eval seeds before declaring success when `success_rate` is near 60%.
