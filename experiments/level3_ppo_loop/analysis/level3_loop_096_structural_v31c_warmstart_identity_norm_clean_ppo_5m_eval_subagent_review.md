# Evaluator Metrics Review: loop096 / v31c

## Key Finding

Reject `v31c_warmstart_identity_norm_clean_ppo_5m`; it regressed from the
loop094/v31a best checkpoint.

## Evidence

- loop094/v31a best 4M: `19/100` success, `19%`, mean successful time
  `6.8758s`, mean gates `1.55`, crash `81%`, timeout `0%`.
- v31c zero-update identity-normalized warm-start matched loop094, so the
  checkpoint wrapper itself was not destructive.
- All trained v31c checkpoints had `0/100` success on `config/level3.toml`
  validation_unseen seeds 101-200.
- v31c final: success `0%`, mean successful time `None`, crash `84%`, timeout
  `16%`, mean gates `0.0`.
- v31c 1M was the only checkpoint with any gate movement, mean gates `0.23`;
  from 2M onward mean gates collapsed to `0.0`.
- Final failures: `81` contact, `3` bounds, `16` timeout; all `100` failed
  while still targeting gate 0.

## Recommended Next Action

Do not continue or mature v31c. Use a named structural lane or hold for more
analysis; keep final evaluation on unchanged `config/level3.toml`.

