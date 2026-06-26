# Decision: Record V59 Local Safety Reflex Proposal

Decision: hold_for_more_analysis

Status: no training launched.

## Decision

Record `v59_reference_tracker_with_local_safety_reflex` as a future tracker
extension after v58 semantic reference support, not as the immediate command.

The immediate next action remains bounded v58 semantic planner-reference
preflight/evaluation. V59 should be launched only if v58 shows that references
are continuous and trackable but contact persists because the tracker lacks a
small local collision-avoidance reflex.

## Rationale

The user's design is correct: the tracker should not be a pure blind point
follower, but it also should not become an autonomous Level3 policy.

The intended split is:

```text
planner: decides route, slowdown, and short-horizon reference
tracker: follows that reference
local safety reflex: nudges away from nearby collision risk
```

Current code already includes nearest visible obstacle relative position,
obstacle distance, obstacle detected flag, obstacle margin, obstacle coefficient,
and crash penalty support. That means the first v59 step should audit and tune
existing safety support before adding a new observation layout.

## Guardrails

- Do not modify `config/level3.toml`.
- Do not add gate-pass, finish, race-progress, or stage-progress rewards to the
  tracker.
- Do not add full target-gate semantics, gate-pass phase, or route-level gate
  progress as actor inputs for the safety reflex.
- Keep reference tracking, desired speed/velocity tracking, heading tracking,
  braking/hold behavior, and action smoothness as the dominant reward terms.
- Keep local safety auxiliary, roughly 10-20% of the reward pressure or active
  only inside a collision margin.
- Use builder/checker before any observation-layout, reward-semantics, trainer,
  evaluator, controller, or loop-orchestration change.

## Next Action

Run the bounded v58 semantic planner-reference preflight/evaluation first. If
the v58 result still has contact with otherwise reasonable tracking, prepare a
v59 builder/checker packet for local safety reflex support.
