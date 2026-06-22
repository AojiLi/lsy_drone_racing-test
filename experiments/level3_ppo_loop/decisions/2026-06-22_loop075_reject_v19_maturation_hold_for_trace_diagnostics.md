# Loop075 Decision: Reject V19 Maturation, Hold For Trace Diagnostics

Decision: hold_for_more_analysis

Pending gate resolved:

- trial_id: `level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m`
- analysis_report: `experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.md`
- analysis_json: `experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.json`

## Verdict

Reject v19 maturation. Do not continue v19 to 90M. Do not launch another
low-probability replay continuation from loop075. Do not run the analyzer's
generic reward-number suggestion without a new named decision packet.

Best loop075 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_step_025000000.ckpt`

Metrics on hard eval `config/level3_dr.toml`:

- success rate: 0.15
- mean successful time: 7.933s
- crash rate: 0.85
- mean gates: 1.55
- target met: false

Comparison:

- loop069 25M global best: 0.20 success, 1.45 mean gates, 0.80 crash, 6.675s
- loop071 20M diagnostic frontier: 0.25 success, 2.00 mean gates, 0.75 crash, 8.524s
- loop074 20M v19 rollback floor: 0.20 success, 1.60 mean gates, 0.80 crash, 7.755s
- loop075 25M best: 0.15 success, 1.55 mean gates, 0.85 crash, 7.933s
- loop075 30M gate blip: 0.10 success, 1.70 mean gates, 0.90 crash, 9.150s

Loop075 fails rollback and promotion. The only milestone that beats loop074's
mean-gates floor is loop075 30M, but it does so with success falling to 0.10
and crash rising to 0.90. That is not compensating progress.

## Subagent Consensus

Evaluator metrics:

- Reject loop075.
- Keep loop069 25M as global best.
- Do not promote any loop075 checkpoint.

W&B/PPO diagnostics:

- PPO is numerically stable: KL, clip fraction, value loss, explained variance,
  and entropy are controlled.
- The failure is behavioral conversion: W&B gate/finish signals are flat or
  worse, and hard eval regresses.
- Do not tune PPO hyperparameters from this evidence.

Structure/research synthesis:

- v19 looks like replay-seed over-concentration, not a clean reward-scale miss.
- Loop075 successes are only on replay seeds; non-replay transfer is missing.
- Hold for trace/seed diagnostics before the next training chunk.

## Required Diagnostic Before Next Training

Produce a trace/seed diagnostic packet comparing:

- loop069 25M global best
- loop071 20M diagnostic frontier
- loop074 20M v19 rollback floor
- loop075 25M best
- loop075 30M mean-gates blip

Use hard-eval seeds `1-20` and tag v19 replay seeds:

`[1, 4, 9, 11, 12, 16, 17, 18, 20]`

The diagnostic should report:

- per-seed success, gates, time, crash, timeout;
- replay vs non-replay success and mean gates;
- gate transition at first and second gate;
- first-gate approach and wrong-side indicators;
- crash timing and obstacle/frame/stand class when available;
- action, command-tilt, tilt, and smoothness stats;
- whether loop075 lost non-replay transfer compared with loop071.

## Next Action

No next training command is approved yet.

After the diagnostic, the main agent should either:

- reject the seed-replay family and write a new named structural packet, likely
  aiming to restore loop071-style default-distribution transfer; or
- write a specific reward-number packet if the traces identify a coherent
  reward-scale failure.

In all cases, hard eval remains on unchanged `config/level3_dr.toml`.
