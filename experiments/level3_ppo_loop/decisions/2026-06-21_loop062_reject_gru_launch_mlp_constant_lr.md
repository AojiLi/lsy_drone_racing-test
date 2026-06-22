# Loop062 Decision: Reject GRU Maturation, Launch MLP Constant-LR Lane

## Decision

`launch_named_structural_lane`

Launch:

`v12_mlp_loop052_constant_lr_nominal_reward`

This is a named training-number lane. It returns to the global-best loop052
MLP/v5 checkpoint and changes only `anneal_lr=False` for a short 20M screen.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Evidence

Loop062 tested:

- Proposal: `structural_v11_recurrent_actor_gru256_screen_30m`
- Observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Policy: recurrent Actor GRU-256 from scratch, same-observation 2x256 Critic
- Training horizon: 30M
- Best hard-eval checkpoint: 10M
- Best hard eval:
  - success_rate: 0.00
  - mean_gates: 0.10
  - crash_rate: 0.55
  - timeout_rate: 0.45
  - mean successful time: none

Later 15M, 20M, 25M, and final checkpoints had 0.00 mean_gates.

Global best remains loop052:

- success_rate: 0.20
- mean_gates: 1.40
- mean successful time: 6.975s
- crash_rate: 0.80

## Subagent Synthesis

Evaluator reviewer:

- Reject loop062 maturation.
- 0% success and 0.10 mean_gates do not meet the step-curve condition for
  extending to 60M/90M.
- Lower crash at 10M is not useful because it comes with 45% timeouts and only
  two total gate passes across 20 seeds.

W&B/PPO reviewer:

- Loop062 is not useful learning that merely failed late.
- W&B shows no race conversion: passed-gate and finished rates stay at zero.
- PPO update pressure is extremely low: near-zero KL, zero clip fraction, tiny
  policy loss, and learning rate annealed to near zero.
- No obvious GRU wiring failure was found, but this configured GRU hypothesis
  should be rejected.

Structure/research reviewer:

- Reject GRU maturation.
- Do not launch privileged Critic or another recurrent lane off this result.
- Return to the best MLP/v5 checkpoint and make an explicit training-number
  decision aimed at gate acquisition and completion.

## Next Lane Contract

`v12_mlp_loop052_constant_lr_nominal_reward`

- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`
- Observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Actor/Critic:
  existing 2x256 Tanh MLP
- Reward:
  nominal loop052 reward numbers, unchanged
- Training-number change:
  `anneal_lr=False`
- Keep unchanged:
  `learning_rate=5e-5`, `update_epochs=5`, `num_minibatches=8`,
  `ent_coef=0.02`, `target_kl=0.03`, controller limits, network size, and
  reward structure
- Training horizon:
  20M screening with 5M checkpoint interval
- Hard eval:
  unchanged `config/level3_dr.toml`

## Promotion Rule

If v12 beats loop052's 0.20 success rate or materially exceeds 1.40 mean_gates,
continue the same hypothesis toward 60M/90M with milestone-aware evaluation.

If v12 does not beat loop052, reject constant-LR MLP fine-tuning and do not
repeat the same MLP/v5 nominal lane with only cosmetic reward-number changes.

