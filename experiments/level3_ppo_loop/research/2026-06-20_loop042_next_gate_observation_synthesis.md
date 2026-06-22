# Next-Gate Local Observation Synthesis After loop042

Date: 2026-06-20

## Scope

This packet supports a named Level3 structural lane:

`v6_next_gate_localobs_warmstart`

Hard boundary:

- Do not modify `config/level3_dr.toml`.
- Final acceptance remains hard eval on `config/level3_dr.toml`.
- Do not continue loop042 unchanged.
- Do not launch another soft-centerline reward-number nudge.

## Local Evidence

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

Recent adjacent v5 lanes failed to beat that frontier:

- loop040 soft-centerline follow-through: best `0.10` success, `1.15`
  mean gates, `0.90` crash.
- loop041 stronger gate-acquisition retune: best `0.05` success, `0.85`
  mean gates, `0.95` crash, command tilt over-limit `0.746`.
- loop042 saturation guard: best `0.05` success, `1.00` mean gates,
  `0.95` crash. It reduced command tilt over-limit to `0.457`, but did
  not improve pass conversion.

Parity diagnostics after loop042 were clean:

- Action scaling parity: clean, max action-scale diff `0.0`.
- Observation/event parity: clean, train/inference observation dimension `68`,
  max observation diff `4.76837158203125e-07`, event mismatch counts `0`.

This makes a train/inference wiring bug unlikely. The remaining failure mode
is structural: the v5 policy repeatedly learns some first-gate approach
behavior, but does not convert it into stable pass-through/continuation.

## Remote Reference

Fetched `origin/main` from `https://github.com/stateirving/lsy_drone_racing`
at commit `4201cb16ec725499695f8f58019764b3ad8e3c2c`.

The latest remote notebook evidence points in the same broad direction:

- `notebooks/train_level3_ppo.ipynb` uses the local-observation family for a
  long `level3_less` run on `level3_dr.toml`, with `300_000_000` timesteps.
- `notebooks/finetune_level3_ppo.ipynb` warm-starts from
  `level3_localobs_relax_final.ckpt` and tries a safer 50M finetune with lower
  learning rate and stronger crash/obstacle/action/tilt penalties.
- The notebook baseline records `level3_localobs_relax_final` at `15/100`
  success, crash `85/100`, mean gates `1.38`, and mean success time `6.40s`.

I audited the latest remote high-crash-penalty final checkpoint locally on
`config/level3_dr.toml` using the loop audit path:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_localobs_safer_finetune_from_final_highcrashpenalty/level3_localobs_safer_finetune_from_final_highcrashpenalty_final.ckpt`
- Success rate: `0.10`
- Mean successful time: `5.640000000000001s`
- Crash rate: `0.90`
- Mean gates: `1.15`
- Mean action delta: `0.25711860748381443`
- Command tilt over-limit fraction: `0.37126480274066787`

This remote checkpoint is smoother than loop020, but it does not beat loop020
on success or mean gates. It supports using safety diagnostics, but not
switching the current best to the remote high-crash checkpoint.

## Hypothesis

The v5 observation contains:

- current target gate corners;
- current gate known/visited flag;
- nearest non-target gate corners;
- nearest non-target gate known/visited flag;
- two nearest obstacle features;
- last action and short local history.

On Level3, the nearest non-target gate can be a geometric distractor. It is not
guaranteed to be the race-order next gate. The repeated wrong-side/pass
conversion failures suggest the policy may need the next race gate rather than
the closest other gate to learn follow-through geometry.

The proposed v6 layout keeps the same 68-dimensional local observation shape
and replaces only the second gate block:

- current target gate corners;
- current gate known/visited flag;
- race-order next gate corners;
- next gate known/visited flag;
- two nearest obstacle features;
- last action and short local history.

Because the input dimension remains unchanged, the v6 lane can warm-start from
the loop020 v5 checkpoint. The transferred weights treat the second gate block
as a same-shaped gate-geometry feature, while training can adapt its semantics
from nearest-other to next-in-sequence.

## Proposed Lane

Name:

`v6_next_gate_localobs_warmstart`

Code/config knobs:

- Observation layout:
  `level3_target_next_gate_2obs_local_history_v6`
- Warm-start compatibility:
  allow only v5 local-obstacle checkpoint to initialize this v6 layout when
  first-layer actor and critic input dimensions match exactly.
- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Reward/PPO/controller parameters:
  keep loop020 frontier values for the first screen.
- Train config:
  `level3_dr.toml`
- Hard eval config:
  `level3_dr.toml`
- Train timesteps:
  `30_000_000`
- Checkpoint interval:
  `5_000_000`

## Promotion And Rollback

Promote or mature toward 60M if any checkpoint beats loop020 on at least one
primary frontier:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success as loop020 with lower crash/timeout or materially better time.

Also consider maturation if the branch has non-zero success with clear W&B
gate/pass conversion improvement, because the Level2 step-curve packet says
30M is screening evidence, not a final judgment.

Reject or hold if:

- success stays `<=0.10`;
- mean gates stay below `1.45`;
- crash stays `>=0.95`;
- wrong-side/pass-conversion metrics stay flat despite stable PPO diagnostics.

If this lane fails, the next structural packet should move beyond v5/v6 local
gate semantics and examine either explicit progress/phase features or training
curriculum, while still keeping the final hard eval on unchanged
`config/level3_dr.toml`.
