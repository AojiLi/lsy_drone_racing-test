# Decision: Unlock Gate Aperture Reference

## Decision

`zigzag_or_lemniscate_tracking` attempt001 passed the stage gate. Unlock
`gate_aperture_reference`.

## Evidence

- Selected checkpoint: `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Selected metrics: `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_zigzag_from_curve_attempt001_step8m_metrics.json`
- Gate checker: `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_zigzag_from_curve_attempt001_step8m_gate.json`
- W&B run: <https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/pfo4433u>

The selected checkpoint passed all required metrics:

- completion `1.0`
- crash `0.0`
- mean cross-track error `0.098746 m`
- p90 cross-track error `0.285000 m`
- mean action delta `0.010483`
- p90 action delta `0.014510`

## Rationale

Final and step11m produced slightly lower tracking error, but with much larger
action deltas. The tracker ladder is trying to build a stable low-level servo,
so the best checkpoint is the one that is accurate enough and remains smooth.
Step8m is the best balance from this milestone sweep.

## Next Stage

Run `gate_aperture_reference` next:

- environment: `gate_aperture`
- config: `config/level3_tracker_gate_aperture.toml`
- default maturation budget: `15M`
- checkpoint interval: `1M`
- start from selected zigzag step8m checkpoint

Do not launch planner-driven Level3 long training until
`gate_aperture_reference` and `planner_integration_smoke` both pass.
