# Level3 Decision: V5 Completion Micro Safety After Loop 021

Date: 2026-06-20

## Trial

- Trial id: `level3_loop_021_v5_completion_safety_recovery_from_loop020_25m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m`
- Best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m_step_010000000.ckpt`
- Hard-eval success rate: `0.10`
- Mean successful time: `5.41s`
- Crash rate: `0.90`
- Mean gates: `1.00`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: Loop021 regressed from the global best loop020 25M
  checkpoint. Loop021 best is `10%` success and `1.00` mean gates, while
  loop020 25M remains `15%` success and `1.45` mean gates. Do not continue
  loop021 numbers; resume from loop020 25M.
- `wandb_ppo_diagnostics`: PPO did not collapse. KL, clipfrac, entropy, and
  throughput are stable enough. The failure is reward conversion: W&B reward
  improved while passed-gate, finished, and crash rates stayed flat, and hard
  eval regressed. Use a new explicit reward-number packet, not PPO hyperparameter
  tuning.
- `structure_research_synthesis`: The v5 observation family remains the best
  supported lane, but repeated reward nudging may be hitting a control-saturation
  ceiling. A named action-damped controller lane is a possible future structural
  test, but it needs train/eval parity and explicit implementation evidence
  before launching.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

Reject the loop021 safety-recovery numbers. Keep the v5 observation layout,
PPO/training structure, controller, and Level3 hard-eval track unchanged. Resume
from the loop020 25M global-best checkpoint and test a smaller safety correction
that is closer to the successful loop020 completion-backloaded balance.

This packet does not approve an action-damped controller lane. The current code
has train-side action latency/response wrappers, but no ready hard-eval-parity
controller/action-damping lane in `scripts/level3_ppo_loop.py`. Launching that
without implementation and verification would create an unclear structural test.

## Rationale

- Local evaluator evidence: loop021 fell from loop020's `15%` success and
  `1.45` mean gates to `10%` success and `1.00` mean gates.
- W&B evidence: total reward rose, but race gate/finish/crash signals stayed
  flat. This is no-conversion, not acceptance progress.
- PPO/training evidence: PPO diagnostics are stable enough; do not change
  `learning_rate`, `ent_coef`, `target_kl`, minibatches, epochs, `hidden_dim`,
  or `n_obs` from this evidence alone.
- Structural evidence: v5 should remain active. A controller/action-structure
  lane is plausible, but not ready as the immediate next chunk because the
  orchestrator has no named parity-tested action-damping hypothesis.
- External research evidence: the stateirving packet still supports v5 local
  obstacle observations and remote-scale reward evidence, but local hard eval
  must decide the next step.

## Approved Next Experiment

Name: `v5_completion_micro_safety_from_loop020_25m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Train/eval chunk:

```text
30M steps, 5M checkpoint interval, milestone hard eval on config/level3_dr.toml
```

Approved reward numbers:

```text
progress_coef=0.0
gate_stage_coef=9.0
gate_axis_coef=22.0
near_gate_coef=0.0
gate_bonus=180.0
gate_front_bonus=22.0
gate_plane_bonus=0.0
gate_back_bonus=95.0
finish_bonus=300.0
missed_gate_penalty=0.0
wrong_side_penalty=14.0
crash_penalty=55.0
obstacle_coef=4.7
obstacle_margin=0.3
obstacle_clearance_coef=0.0
timeout_penalty=80.0
time_penalty=0.005
act_coef=0.014
d_act_th_coef=0.062
d_act_xy_coef=0.062
cmd_tilt_coef=0.85
rpy_coef=0.72
tilt_limit_deg=42.0
tilt_excess_coef=12.0
```

Changed relative to loop020:

```text
crash_penalty: 50.0 -> 55.0
obstacle_coef: 4.5 -> 4.7
act_coef: 0.012 -> 0.014
d_act_th_coef: 0.055 -> 0.062
d_act_xy_coef: 0.055 -> 0.062
cmd_tilt_coef: 0.75 -> 0.85
rpy_coef: 0.65 -> 0.72
tilt_excess_coef: 10.0 -> 12.0
```

PPO/training-structure numbers stay unchanged:

```text
learning_rate=0.0003
gamma=0.99
gae_lambda=0.95
update_epochs=5
num_minibatches=8
ent_coef=0.02
target_kl=0.03
hidden_dim=256
n_obs=2
```

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_completion_micro_safety_from_loop020_25m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_021_v5_completion_safety_recovery_from_loop020_25m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_v5_completion_micro_safety_after_loop021.md \
  --param progress_coef=0.0 \
  --param gate_stage_coef=9.0 \
  --param gate_axis_coef=22.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=180.0 \
  --param gate_front_bonus=22.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=95.0 \
  --param finish_bonus=300.0 \
  --param missed_gate_penalty=0.0 \
  --param wrong_side_penalty=14.0 \
  --param crash_penalty=55.0 \
  --param obstacle_coef=4.7 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.005 \
  --param act_coef=0.014 \
  --param d_act_th_coef=0.062 \
  --param d_act_xy_coef=0.062 \
  --param cmd_tilt_coef=0.85 \
  --param rpy_coef=0.72 \
  --param tilt_limit_deg=42.0 \
  --param tilt_excess_coef=12.0
```

## Promotion And Rollback

- Promote if hard eval beats loop020 25M on success rate, crash rate, or mean
  gates.
- Promote for maturation if it ties `15%` success while reducing command tilt or
  actual tilt by a meaningful margin.
- Reject if success stays at or below `10%` with mean gates below `1.15`.
- If this reward-number rollback also fails to improve, prepare a concrete
  structural-lane implementation packet for action/controller damping with
  train/eval parity before launching it.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not launch another chunk without a new post-run analysis and 3-review
  decision after this experiment completes.
