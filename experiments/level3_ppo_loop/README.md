# Level3 PPO Loop

This folder stores the resumable train/evaluate/tune state for the Level3
domain-randomized PPO controller.

## Target

- Config: `config/level3_dr.toml`
- Mean successful time: `<= 7.0s`
- Success rate: `>= 60%`
- W&B project: `ADR-PPO-Racing-Level3`

## Commands

Dry-run the next trial without training:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run
```

Run one bounded train/evaluate/tune iteration:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled
```

The orchestrator blocks `--max-iterations > 1` by default because post-run
analysis is required between iterations. Do not use
`--allow-unanalysed-multi-iteration` for the Codex-supervised loop; it is only
for an explicitly accepted blind run without analysis.

For the user's unattended Codex-supervised loop, run one train/evaluate chunk at
a time and let the Codex main agent do the analysis/subagent/research decision
between invocations:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop
```

`--codex-autonomous-loop` records that Codex may spawn analysis and research
subagents and choose the next reward-only hypothesis without per-run user
confirmation. It implies automatic reward-hypothesis search with relaxed
reward-number bounds, but it does not bypass W&B/evaluator analysis, reward-only
guards, or long-run guards.

When the loop plateaus, it holds by default instead of repeatedly scaling the
same reward numbers. To let it automatically try a new reward-only hypothesis,
run a bounded screening trial:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 20000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --auto-hypothesis-search
```

For a wider exploratory reward-number search, add `--relaxed-reward-bounds`.
This still does not permit PPO, observation, algorithm, curriculum, or reward
structure changes.

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 20000000 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --auto-hypothesis-search \
  --relaxed-reward-bounds
```

Long runs above `30M` steps require prior screened improvement unless you
explicitly pass `--allow-long-run-without-improvement`.

Start a new random-init baseline instead of continuing from the existing
`level3_DR_initial` checkpoint:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --from-scratch
```

If you launch the orchestrator from a different Python, keep train/eval
subprocesses on the GPU pixi environment:

```bash
<python> scripts/level3_ppo_loop.py \
  --python-command "pixi run -e gpu python" \
  --max-iterations 1 \
  --wandb-enabled
```

Before online W&B runs, log in once:

```bash
pixi run -e gpu wandb login
```

Each loop trial uses a stable W&B run id like `level3_loop_001_baseline`. The
training subprocess writes live PPO curves, and the loop resumes the same run
after evaluation to log `eval/success_rate`, `eval/mean_time_s_success`,
`eval/crash_rate`, `eval/score`, and a summary table.

Run a shorter smoke-sized iteration:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --train-timesteps 65536 \
  --checkpoint-interval 32768 \
  --num-envs 8 \
  --num-steps 16 \
  --jax-device cpu \
  --no-cuda \
  --eval-seeds 2
```

The loop writes local logs, summaries, and the resumable `state.json` here.
The hard stop condition is based on evaluator metrics, not PPO training reward.

## Post-Run Analysis

After each completed train/evaluate iteration, build an analysis packet before
starting the next training run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

The analyzer combines:

- evaluator CSV metrics from the loop state
- sampled W&B curves for `train/*`, `losses/*`, `race/*`, and
  `reward_components/*`
- reward-only diagnosis and a candidate next command
- subagent briefs for evaluator review, W&B curve review, and reward-only tuning
  synthesis

Outputs are written under `experiments/level3_ppo_loop/analysis/` and the paths
are copied back into the selected trial in `state.json`.

For Codex-driven analysis, the main agent should hand those generated briefs to
parallel subagents, compare their findings, and then choose one of:

- stop because the hard gate is met
- hold reward parameters and inspect instability/regression
- launch one bounded next iteration with reward-only `--param` overrides

For Codex-driven autonomy, the main agent should attach ordinary analysis with
`--analysis-packet`, source-backed research with `--research-packet`, and a
main-agent decision packet with `--approved-hypothesis-packet`. Analysis packets
never bypass plateau guards by themselves.

## Two-Stage Tuning Boundary

Stage 1 is reward-only. It must not change PPO hyperparameters, algorithm,
observation layout, network/training structure, or add new reward channels.

Allowed `--param` overrides are limited to active reward numbers:

```text
gate_stage_coef, gate_axis_coef, gate_bonus, gate_front_bonus,
gate_back_bonus, finish_bonus, wrong_side_penalty, crash_penalty,
obstacle_coef, obstacle_margin, timeout_penalty, time_penalty, act_coef,
d_act_th_coef, d_act_xy_coef, cmd_tilt_coef, rpy_coef, tilt_limit_deg,
tilt_excess_coef
```

These disabled reward channels stay at zero unless the user explicitly approves
a reward-structure change:

```text
progress_coef, near_gate_coef, gate_plane_bonus, missed_gate_penalty,
obstacle_clearance_coef
```

Stage 2, structural escalation, is allowed only after reward-only tuning is
demonstrably exhausted. Before any structural change, write a detailed
escalation packet proving all of:

- at least 6 evaluated reward-only trials
- at least 4 distinct active-reward hypotheses
- at least 120M accumulated evaluated reward-only training steps
- at least 4 consecutive no-improvement evaluated trials
- target success is still not met
- W&B curves fail to convert into evaluator progress
- separate subagents agree from evaluator, W&B, reward-failure, papers/GitHub
  research, and codebase-diagnosis reviews

If this gate passes, structural work must be explicit and separate from
reward-only trial records; do not hide observation, algorithm, reward-structure,
or training-structure changes inside a reward-only run.

## Research-Guided Tuning

For tuning decisions that need papers, GitHub examples, or PPO references, use
the templates in `experiments/level3_ppo_loop/research/`. Research may guide
which active reward numbers to scale during Stage 1. It must not propose
framework changes until the Stage 2 escalation gate is met.

Attach the main-agent synthesis to the next trial:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --research-packet experiments/level3_ppo_loop/research/<synthesis>.md
```

Attached packets are copied into each trial record in `state.json`, so the
reason for a parameter move is traceable later.
