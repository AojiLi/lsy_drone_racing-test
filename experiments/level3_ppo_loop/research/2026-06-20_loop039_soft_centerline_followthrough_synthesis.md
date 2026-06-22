# Soft Centerline Followthrough Synthesis After loop039

Date: 2026-06-20

## Scope

This packet supports a named Level3 structural lane:

`v5_soft_centerline_followthrough_pass_conversion`

Hard boundary:

- Do not modify `config/level3_dr.toml`.
- Train/evaluate acceptance remains hard eval on `config/level3_dr.toml`.
- Keep v5 local-obstacle observations, PPO/network settings, controller, and
  action authority fixed for the next screen.

## Local Evidence

Current global best remains loop020:

- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

loop039 direct-aperture screen:

- Best hard eval: `0.00` success, `1.00` mean gates, `1.00` crash.
- `race/gate_plane_center_hit_rate` tail about `0.000031`.
- `race/gate_pass_hit_rate` tail about `0.000122`.
- `race/passed_gate_rate` tail about `0.000275`.
- `race/wrong_side_gate_rate` rose to about `0.0688` tail.
- `race/gate_frame_pressure` rose to about `2.40` tail.
- `losses/value_loss` rose sharply, with tail about `7455`.

## Interpretation

The direct-aperture reward was too sparse and too punitive. It made the reward
target more literal, but the agent did not discover stable centered gate-pass
behavior. Instead, positive pass/event rewards collapsed while wrong-side and
near-frame penalties increased.

The next lane should not continue direct-aperture. It should preserve the
parts of loop020 that already produced non-zero hard-eval success:

- normal `passed_gate` reward remains active;
- staged gate progress remains dense;
- followthrough/back-plane reward remains active.

The structural change should be softer:

- widen centerline shaping rather than require exact aperture hit;
- add a modest centered plane-crossing bonus;
- keep missed-plane and frame-pressure penalties small;
- reduce over-reliance on front-gate contact.

## Proposed Lane

Name:

`v5_soft_centerline_followthrough_pass_conversion`

Reward structure:

`soft_centerline_followthrough`

Intended behavior:

- Keep `passed_gate` as a valid event reward to avoid starving pass conversion.
- Use softer centerline-weighted axis progress so approach behavior is not
  shut off when slightly off-center.
- Reward centered gate-plane crossings as an intermediate event.
- Preserve back/followthrough reward.
- Penalize missed-plane and near-frame pressure lightly, not as a dominant
  term.

Fixed from loop020:

- v5 local-obstacle observation layout.
- PPO/network settings.
- Full 90-degree action authority.
- No action low-pass.
- Hard eval on the unchanged Level3 track.

## Promotion And Rollback

Promote or mature only if the lane beats loop020 on at least one primary
signal:

- success rate `>0.15`; or
- mean gates `>1.45`; or
- same success with lower crash/timeout or materially better time.

Reject or retune if:

- success remains `0.00`; or
- mean gates stay below `1.00`; or
- W&B `passed_gate_rate`, `gate_pass_hit_rate`, and
  `gate_plane_center_hit_rate` stay flat/down while wrong-side/frame pressure
  rises.
