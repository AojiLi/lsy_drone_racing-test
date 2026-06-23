# Subagent Reviews: loop113 / v42 GRU-V10 Gate-Phase Curriculum

Source trial:
`level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_analysis.md`

## Evaluator Metrics

Key finding: reject v42 as-is. It did not produce any hard-eval successes and
did not meaningfully escape gate 0.

Evidence:

- all evaluated checkpoints had `0/100` successes;
- best checkpoint was `4M` with `0%` success, `0.01` mean gates, `54%`
  crash, `46%` timeout;
- failures at best checkpoint were `99%` at gate 0 and `1%` at gate 1;
- across checkpoints, mean gates peaked at only `0.01`;
- crash ranged `54%-65%`, timeout ranged `35%-46%`;
- loop107 1M remains the corrected frontier at `21%` success, `1.66` mean
  gates, `79%` crash, and `7.578s` mean successful time.

Recommendation: do not promote or mature v42. Do not continue from loop113
checkpoints. Launch a new named structural lane.

## W&B / PPO Diagnostics

Key finding: loop113 shows weak training-side learning, but PPO is massively
under-updating and gate-phase curriculum progress did not transfer to normal
starts.

Evidence:

- hard eval best was still `0%` success and `0.01` mean gates;
- W&B gate signals improved only inside training: `race/gate_stage ~0.111`,
  `race/gate_axis_x ~-0.480`, `passed_gate_rate ~1.5e-4` to `2.1e-4`;
- finished rate remained effectively zero;
- `approx_kl` was far below the `0.03` target, with analyzer packet around
  `4.1e-05` and local summary around `1.08e-07`;
- `clipfrac=0.0`, policy loss was around `-1.8e-05` to `-7.6e-05`;
- final learning rate annealed to about `1.64e-7`;
- entropy stayed around `0.84`, so this was not simple entropy collapse;
- deterministic eval behavior had low authority: best mean action delta
  `0.0356`, mean max command tilt `11.9 deg`, and `0` tilt-over-limit;
- Critic remained weak with explained variance around `0.036-0.038`.

Recommendation: do not continue v42 and do not do a reward-only tweak. The next
lane should address transfer plus under-updating as an explicit
structural/training lane.

## Structure / Research Synthesis

Key finding: reject `v42_gru_v10_gate_phase_reset_curriculum_from_scratch`
as-is. The result is a structural start-distribution / skill-composition
failure, not a track issue and not an obvious GRU/v10 wiring bug.

Evidence:

- v41 cleared v10 observation parity, action-scale parity, recurrent Actor
  parity, hidden reset/carry parity, save/reload parity, and recurrent PPO
  gradient sanity;
- v42's own promotion bar required nonzero success, mean gates above `0.5`, or
  a clear passed-gate conversion signal;
- loop113 had `0%` success at every milestone and nearly all failures at gate
  0;
- W&B/eval conversion was effectively absent: `race/passed_gate_rate=0.000214`,
  `finished_rate=0`, hard-eval best `mean_gates=0.01`;
- behavior looked like a cautious low-action local optimum, not an
  over-aggressive controller.

Recommendation: launch a new named structural lane:
`v43_success_trajectory_imitation_warmstart_gru_v10`. Use training-only
success-trajectory imitation or behavior-cloning warm start from existing
successful v5-family hard-eval trajectories, then PPO fine-tune a single
end-to-end GRU/v10 Actor. Keep `config/level3.toml` unchanged for hard eval; do
not add MPC, planner, shield, or an inference-time controller. Do not start
from loop113 checkpoints.
