# Subagent Brief: Level3 PPO Tuning Research

## Context

We are training a PPO policy for `config/level3_dr.toml` in
`lsy_drone_racing`. The hard gate is:

- success rate `>= 60%`
- mean successful time `<= 7.0s`

Current loop state lives in `experiments/level3_ppo_loop/state.json`. Training
and evaluator metrics are logged to W&B project `ADR-PPO-Racing-Level3`.

The loop is reward-only. Do not recommend changing PPO hyperparameters,
algorithm, observation layout, network/training structure, curriculum, or adding
new reward channels. Suggest only numerical changes to active reward parameters:

- `gate_stage_coef`, `gate_axis_coef`, `gate_bonus`, `gate_front_bonus`,
  `gate_back_bonus`
- `finish_bonus`, `time_penalty`, `timeout_penalty`
- `crash_penalty`, `obstacle_coef`, `obstacle_margin`
- `act_coef`, `d_act_xy_coef`, `d_act_th_coef`, `cmd_tilt_coef`, `rpy_coef`
- `wrong_side_penalty`, `tilt_limit_deg`, `tilt_excess_coef`

Keep these disabled reward channels at zero unless the user explicitly approves
a reward-structure change: `progress_coef`, `near_gate_coef`,
`gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

Structural changes are a separate Stage 2. Do not recommend them in a normal
reward-scaling packet unless the reward-only exhaustion gate has been met and
the task explicitly asks for an escalation packet.

## Research Task

Find source-backed tuning guidance from one lane:

- papers/technical reports about PPO, quadrotor racing, agile flight,
  sim-to-real, reward shaping, or domain randomization
- GitHub/open-source implementations or docs for drone racing RL, PPO reward
  tuning, SB3/CleanRL workflows, or sim-to-real training loops
- high-signal tuning references for sparse reward, progress/safety/speed
  reward tradeoffs, or smoothness penalties

## Output Format

Return a concise research packet:

```md
# <short packet title>

## Sources

- <title> - <url>

## Findings

| Evidence | Trigger metric pattern | Suggested loop action | Risk |
| --- | --- | --- | --- |
| <what the source suggests> | <when to use it> | <concrete reward-only parameter change> | <caveat> |

## Recommended Next Experiment

- Hypothesis:
- Command/parameter change:
- Expected W&B/eval signal:
- Stop/rollback condition:
```

Keep claims tied to sources. Prefer actionable guidance over broad summaries.
