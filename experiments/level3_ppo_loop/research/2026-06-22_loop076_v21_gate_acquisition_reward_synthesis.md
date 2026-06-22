# Loop076 To V21 Gate-Acquisition Reward Synthesis

Scope: local evidence synthesis for the next named Level3 lane. This packet
does not modify `config/level3_dr.toml`; hard acceptance remains the unchanged
Level3 hard evaluator.

## Evidence

Loop076 default-distribution recovery from loop071 20M failed promotion:

- best loop076 checkpoint: 5M
- success rate: 0.20
- mean successful time: 7.935s
- crash rate: 0.80
- mean gates: 1.65
- final checkpoint: 0.15 success, 1.70 mean gates, 0.85 crash

It did not beat:

- loop069 global best: 0.20 success, 6.675s, 0.80 crash, 1.45 gates
- loop071 diagnostic frontier: 0.25 success, 8.524s, 0.75 crash, 2.00 gates

Three-reviewer consensus after loop076:

- evaluator: do not promote or mature loop076
- W&B/PPO: optimization is stable; do not change PPO/training numbers
- structure: do not continue v20 and do not return to seed replay

## Reward-Structure Constraint

The existing broad frame/gate reward-structure experiments are not strong
candidates for immediate reuse:

- gate potential lanes did not mature into pass conversion
- legacy frame-clearance and direct-aperture lanes collapsed success
- soft-centerline variants did not beat the earlier frontier

Therefore v21 should not make a large reward-structure swap. The safer next
test is a bounded reward-number move using the existing `legacy_staged`
structure from the loop071 family.

## V21 Hypothesis

Loop076 shows that simply returning loop071 to the default distribution does
not preserve the 0.25 success / 2.00 mean-gates frontier. W&B shows PPO is
stable but gate/race proxies do not convert. The next hypothesis is that the
loop071 policy neighborhood needs stronger gate-acquisition and pass-conversion
pressure while preserving obstacle safety and default-distribution training.

V21 should:

- start from loop071 20M
- keep train/eval config `level3_dr.toml`
- keep v5 local-obstacle observation
- keep 2x256 Tanh MLP
- keep constant 5e-5 learning rate and PPO settings
- keep `reward_structure=legacy_staged`
- avoid seed replay and corridor sampler
- strengthen gate acquisition/pass rewards using the loop076 analyzer's bounded
  recommendation
- preserve the existing obstacle and crash safety numbers

Recommended reward-number changes relative to loop071:

- `gate_stage_coef`: 10 -> 13
- `gate_axis_coef`: 12 -> 24
- `gate_front_bonus`: 0 -> 5
- `gate_bonus`: 90 -> 200
- `gate_back_bonus`: 12 -> 35
- `finish_bonus`: 160 -> 175
- `time_penalty`: 0.03 -> 0.02

Keep unchanged:

- `crash_penalty=100`
- `obstacle_coef=8`
- `obstacle_margin=0.4`
- `obstacle_clearance_coef=6`
- `cmd_tilt_coef=1`
- `rpy_coef=1`
- `tilt_limit_deg=40`
- `tilt_excess_coef=15`

## Promotion Rule

V21 should be a 20M screen with 5M checkpoint evaluation.

Promote or mature only if it beats one of:

- loop071 frontier: success `> 0.25` or mean gates `> 2.00` without crash
  worse than `0.75`
- loop069 global-best floor: success `>= 0.20`, crash `<= 0.80`, and mean
  successful time near or below `6.675s`

Reject if success falls below 0.20 and no checkpoint has clear mean-gates
improvement.
