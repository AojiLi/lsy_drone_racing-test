# Loop088 Structure/Research Synthesis Review

Verdict: weak continue/mature v28. Do not hold and do not change the structural
lane yet.

v28 missed the hard target, but it is not a structural failure signal yet. The
best hard-eval checkpoint reached 19% success, 6.846s mean successful time,
81% crash, and 1.57 mean gates, with positive deltas versus the previous
evaluated trial: +2pp success, -2pp crash, and +0.07 gates. That is close to
the loop052 validation anchor and better on gate progress.

Evidence:

- the v28 launch packet defined this as a data-correction lane: success24
  retention plus small bounds/ground failure replay, with unchanged hard eval
  on `config/level3_dr.toml`
- the run nearly matched loop052 success, 0.19 versus 0.20, with better mean
  gates, 1.57 versus 1.47
- retention wiring looks healthy: teacher KL decreased, teacher action MSE
  stayed low, and teacher agreement improved to 0.879 last / 0.868 tail
- the failure is still mainly gate acquisition plus crash conversion, not clear
  evidence of bad observation layout, controller wiring, reward structure, or
  PPO structure
- the launch packet's failure signal is partially present because success is
  still below loop052 and crash is above 0.80, but its promotion signal is also
  partially present because gate progress improved without retention
  destabilization

Recommended next action:

Choose `continue_same_hypothesis` for a bounded v28 maturation chunk. Keep the
same v28 observation layout, beta 0.10, success24 retention dataset,
bounds/ground replay profile, and no final_locked seeds. Use milestone
evaluation and be ready to stop or change lane if the next chunk still shows
success below 0.20, crash above 0.80, and no further validation gate progress.
