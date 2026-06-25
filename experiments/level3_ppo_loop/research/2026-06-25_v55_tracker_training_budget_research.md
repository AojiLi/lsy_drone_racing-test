# v55 Tracker Training Budget Research

Date: 2026-06-25

## Question

The tracker loop had a real failure mode: Codex could run only tiny bounded
smoke jobs because `train_level3_reference_tracker_ppo.py` defaults to
`--total-timesteps 4096`, then accidentally treat the result as evidence that
PPO did not learn. This packet calibrates how long the v55 tracker stages
should train before a stage is judged from learning metrics.

## Local Finding

- The tracker trainer default `--total-timesteps 4096` is a smoke value only.
- The trainer already supports `--checkpoint-interval`, so the loop can save and
  evaluate milestone checkpoints without changing trainer semantics.
- W&B is off unless `--wandb-enabled` is set. Real learning chunks must enable
  W&B and use explicit run names.
- The stage evaluator and checker do not enforce training budget directly yet;
  the loop policy and gate spec now carry the budget semantics.

## External Evidence

- DATT reports PPO-style quadrotor trajectory-tracking training in the
  `15M-25M` step range, including an initial fixed-reference curriculum before
  broader randomization:
  <https://proceedings.mlr.press/v229/huang23a.html>,
  <https://arxiv.org/abs/2310.09053>,
  <https://github.com/KevinHuang8/DATT>.
- OmniDrones reports trained PPO task budgets such as `20M` frames for Track and
  `5M` frames for FlyThrough, with large parallel simulation:
  <https://omnidrones.readthedocs.io/en/latest/tasks/single/Track.html>,
  <https://omnidrones.readthedocs.io/en/latest/tasks/single/FlyThrough.html>.
- safe-control-gym's quadrotor PPO configs use `1M` environment steps as a
  small-task/default scale, useful as a floor but too small to reject difficult
  tracker skills:
  <https://github.com/learnsyslab/safe-control-gym>.
- Learned agile quadrotor controller comparisons report PPO training on the
  order of `50M` environment interactions with many parallel agents:
  <https://arxiv.org/abs/2202.10796>.
- Swift and obstacle-rich drone racing papers use much larger budgets for full
  racing or broad generalization, often `100M+` interactions. These are not the
  right first-stage tracker budget, but they show why full Level3 integration
  should not be judged from tiny runs:
  <https://www.nature.com/articles/s41586-023-06419-4>,
  <https://arxiv.org/html/2602.24030>.
- Local Level2 history also warns against early judgment: useful gate/race
  ability emerged after tens of millions of steps, not at 1M-5M.

## Decision

Use three budget tiers:

1. **Preflight smoke**: `4096` to at most `100k` steps. This only checks trainer
   plumbing, W&B, checkpoint writing, evaluator loading, finite
   actions/observations, and unchanged `config/level3.toml`.
2. **Default maturation chunk**: the first real learning budget for a stage.
   This is explicit in
   `experiments/level3_ppo_loop/tracker_qualification_gates.json`.
3. **Research-backed extension chunk**: if milestone curves are still improving
   or failure looks like undertraining, the main agent may approve an extension
   after three reviews and a decision packet.

Do not declare a learning stage failed from `<=100k` steps unless the failure is
semantic or plumbing related: NaNs, non-finite actions/observations, trainer or
evaluator exception, invalid checkpoint metadata, or `config/level3.toml`
mutation.

## v55 Default Budgets

| Stage | Default chunk | Extension ceiling for same-stage maturation |
|---|---:|---:|
| `hover` | 1M | 5M |
| `point_hold` | 2M | 5M |
| `point_reach` | 4M | 8M |
| `brake_to_point` | 4M | 10M |
| `line_tracking` | 5M | 10M |
| `heading_tracking` | 4M | 10M |
| `multi_point_reference` | 8M | 15M |
| `l_shape_tracking` | 8M | 15M |
| `curve_tracking` | 10M | 20M |
| `zigzag_or_lemniscate_tracking` | 12M | 25M |
| `gate_aperture_reference` | 15M | 25M |
| `planner_integration_smoke` | 0 | 0 |

The extension ceiling is not automatic. It requires milestone evidence, W&B
diagnostics, three subagent reviews, and a main-agent decision packet.

## Loop Implication

The v55 `/goal` should follow:

```text
stage smoke
-> default maturation training with explicit --total-timesteps
-> evaluate milestone checkpoints
-> gate check
-> if failed, run exactly three reviews
-> decide whether same-stage extension, reward/curriculum change, structural fix, or hold
```

This prevents the opposite mistakes:

- too short: treating `4096`, `32k`, or `100k` steps as PPO learning evidence;
- too loose: launching unbounded overnight training without milestone gates.
