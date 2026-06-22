# Loop086 W&B/PPO Diagnostics Review

Role: wandb_ppo_diagnostics

Trial:
`level3_loop_086_structural_v27_teacher_retention_beta003_5m`

## Verdict

The teacher-retention implementation is active and numerically healthy, but
beta=0.03 is too weak to recover the loop052 validation anchor. Do not continue
beta=0.03; run one beta=0.10 screen.

## Retention Metrics

The KL path is real:

- `retention/sampled_batch_size`: 512 throughout training
- `losses/teacher_kl`: about 2.18 at start, about 1.69 at the end
- `losses/teacher_action_mse`: about 0.153 at start, about 0.072 at the end
- `retention/teacher_agreement`: about 0.599 at start, about 0.723 at the end

Signals are finite and nonzero, so this is no longer the placeholder beta=0
control behavior. The agreement remains below the intended 0.80 retention
proxy, however.

## PPO Diagnostics

PPO appears stable:

- approx_kl tail mean about 0.0041, last about 0.0050
- target_kl is 0.03
- clipfrac tail mean about 0.010
- entropy is flat
- explained variance is about 0.78
- value loss trends down

There is no evidence for PPO optimizer instability.

## Conversion

Training reward improved, but race metrics remained nearly flat:

- passed gate rate did not materially improve
- finished rate remained nearly flat
- gate-stage and gate-plane proxies did not convert into validation success

Hard eval improved over beta=0 but not enough:

- beta=0.03 validation: 0.14 success, 0.86 crash, 1.55 mean gates
- loop052 anchor: 0.20 success, 0.80 crash, 1.47 mean gates

## Recommendation

Do not follow the analyzer's generic reward-scaling command.

Run one bounded `v27_teacher_retention_beta010_5m` screen. If beta=0.10 still
does not raise retention agreement toward 0.80 and restore or beat the loop052
anchor, stop the v27 beta sweep and hold for implementation/data analysis.
