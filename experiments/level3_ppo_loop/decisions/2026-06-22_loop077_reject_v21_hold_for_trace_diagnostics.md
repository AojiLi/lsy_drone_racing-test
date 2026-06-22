# Loop077 Decision: Reject V21, Hold For Targeted Trace Diagnostics

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id: `level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.json`

## Verdict

Reject v21. Do not continue it. Do not mature to 60M. Do not rerun the same
gate-acquisition reward numbers.

Best loop077 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_step_005000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.10
- mean successful time: 6.670s
- crash rate: 0.90
- timeout rate: 0.00
- mean gates: 1.70
- target met: false

Milestones:

- 5M: 0.10 success, 0.90 crash, 1.70 mean gates, 6.670s
- 10M: 0.10 success, 0.90 crash, 1.50 mean gates, 6.390s
- 15M: 0.10 success, 0.90 crash, 1.55 mean gates, 7.260s
- final: 0.05 success, 0.95 crash, 1.35 mean gates, 6.880s

The global best remains loop069 25M:

`lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`

- success rate: 0.20
- mean successful time: 6.675s
- crash rate: 0.80
- mean gates: 1.45

## Reviewer Consensus

Evaluator metrics:

- Reject loop077.
- Do not promote any loop077 checkpoint.
- Loop077 is worse than loop069, loop071, and loop076 on success/crash.

W&B/PPO diagnostics:

- PPO is not the primary failure.
- The stronger gate rewards raised train reward/gate bonus but did not convert
  into passed-gate or finish progress.
- Wrong-side/crash behavior worsened.
- Do not change PPO/training numbers from this evidence.

Structure/research synthesis:

- Reject v21 and hold for targeted diagnostics.
- Do not continue v20/v21.
- Do not naively return to loop069/loop071 maturation, because loop070 and
  loop072 already rejected those continuations.

## Required Diagnostic Before Next Training

Run a compact trace diagnostic comparing:

- loop069 25M global best
- loop071 20M diagnostic frontier
- loop076 5M default-recovery best
- loop077 5M v21 best
- loop077 10M
- loop077 15M
- loop077 final

Use fixed hard-eval seeds `1-20` on unchanged `config/level3_dr.toml`.

Focus:

- non-replay transfer
- gate0-to-gate1 and gate1-to-gate2 transition
- wrong-side and axis failures
- obstacle/frame crash classes
- whether v21 shifted success seeds or only increased crash-prone gate pressure

No next training command is approved until the diagnostic is written and a new
main-agent decision packet chooses the next lane.
