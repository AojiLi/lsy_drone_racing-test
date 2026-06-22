"""Interpolate two compatible PPO checkpoints.

This is diagnostic/model-selection tooling. It does not train or modify any
track configuration.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch


def load_checkpoint(path: Path) -> dict[str, Any]:
    """Load a checkpoint and validate the expected top-level structure."""
    checkpoint = torch.load(path, map_location="cpu")
    if not isinstance(checkpoint, dict):
        raise TypeError(f"{path} is not a dict checkpoint")
    if "model_state_dict" not in checkpoint:
        raise KeyError(f"{path} is missing model_state_dict")
    if not isinstance(checkpoint["model_state_dict"], dict):
        raise TypeError(f"{path} model_state_dict is not dict-like")
    return checkpoint


def interpolate(
    base: dict[str, Any],
    target: dict[str, Any],
    alpha: float,
    *,
    base_path: Path,
    target_path: Path,
) -> dict[str, Any]:
    """Return a checkpoint whose tensors are base + alpha * (target - base)."""
    base_state = base["model_state_dict"]
    target_state = target["model_state_dict"]
    if set(base_state) != set(target_state):
        missing = sorted(set(base_state).symmetric_difference(target_state))
        raise ValueError(f"model_state_dict keys differ: {missing[:20]}")

    output = dict(base)
    output_state = {}
    for key, base_tensor in base_state.items():
        target_tensor = target_state[key]
        if tuple(base_tensor.shape) != tuple(target_tensor.shape):
            raise ValueError(
                f"shape mismatch for {key}: {tuple(base_tensor.shape)} vs "
                f"{tuple(target_tensor.shape)}"
            )
        if not torch.is_floating_point(base_tensor):
            if not torch.equal(base_tensor, target_tensor):
                raise ValueError(f"non-floating tensor differs for {key}")
            output_state[key] = base_tensor.clone()
            continue
        output_state[key] = (1.0 - alpha) * base_tensor + alpha * target_tensor

    for key in ("observation_layout", "hidden_dim", "policy_arch"):
        if base.get(key) != target.get(key):
            raise ValueError(f"metadata mismatch for {key}: {base.get(key)} vs {target.get(key)}")
    output["model_state_dict"] = output_state
    output["interpolation"] = {
        "base_checkpoint": str(base_path),
        "target_checkpoint": str(target_path),
        "alpha": alpha,
    }
    return output


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--alpha", required=True, type=float)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if not 0.0 <= args.alpha <= 1.0:
        raise ValueError("--alpha must be between 0 and 1")
    base_checkpoint = load_checkpoint(args.base)
    target_checkpoint = load_checkpoint(args.target)
    interpolated = interpolate(
        base_checkpoint,
        target_checkpoint,
        args.alpha,
        base_path=args.base,
        target_path=args.target,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(interpolated, args.out)
    print(args.out)
