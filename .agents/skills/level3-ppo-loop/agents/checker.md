---
name: level3-loop-checker
description: Read-only checker for Level3 PPO loop code or config-semantics changes.
---

# Level3 Loop Checker

You only verify. Do not edit files.

## Discover Checks

Do not assume the check list from memory. Read the changed files, `AGENTS.md`,
`.agents/skills/level3-ppo-loop/SKILL.md`, and relevant project config or
script help to discover the right checks.

Minimum expectations for this repo:

- `git diff --check`
- Python compile checks for touched scripts/modules
- relevant `scripts/level3_ppo_loop.py --dry-run`
- relevant observation/inference/parity smoke checks for the changed surface
- confirm `config/level3.toml` track geometry/randomization was not modified

## Report Format

If all checks pass:

```text
ALL GREEN
- <check name>: <proof, e.g. command passed or exact passing line>
- level3.toml: unchanged track geometry/randomization confirmed
```

If anything fails:

```text
FAILED
- <file:line> - <what broke> - <check that caught it>
  key output: <copy the important real error line>
```

If multiple failures likely share one root cause, say so. Do not fix anything.
