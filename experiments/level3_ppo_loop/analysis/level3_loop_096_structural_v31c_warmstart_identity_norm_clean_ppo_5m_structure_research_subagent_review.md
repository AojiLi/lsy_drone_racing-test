# Structure / Research Review: loop096 / v31c

## Key Finding

Reject v31c and do not mature it. The identity-normalized checkpoint preserved
loop094 behavior before training, but v31c training collapsed to `0/100`
success and `0.0` mean gates.

## Evidence

- v31c has neither nonzero success nor meaningful gate progress after
  training, so the step-curve maturation rule does not apply to v31c.
- The next roadmap stage after normalization is asymmetric privileged critic,
  but it requires trainer/evaluator support before launch.

## Recommended Next Action

Prepare the next named structural lane from the current best loop094/v31a 4M
checkpoint, not from a trained v31c checkpoint. If launching asymmetric
privileged critic, first prove:

- trainer/evaluator support exists;
- checkpoint metadata/save/load/inference do not leak privileged inputs into
  the deployed actor path;
- zero-update hard-eval parity on `config/level3.toml` validation_unseen
  seeds 101-200 matches loop094/v31a 4M;
- dry-run passes with milestone hard eval configured.

The no-track-edit boundary is preserved because these changes affect only
training architecture or continuation strategy; the final target track remains
unchanged `config/level3.toml`.

