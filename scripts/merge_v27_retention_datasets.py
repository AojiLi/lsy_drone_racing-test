"""Merge v27 teacher-retention datasets into one audited training artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).parents[1]

REQUIRED_ARRAYS = (
    "student_obs",
    "teacher_action_mean",
    "teacher_action_logstd",
    "target_gate",
    "seed",
    "episode_step",
    "success_time_s",
    "gate_axis",
    "gate_lateral_error",
    "obstacle_min_dist",
    "metadata_json",
)


def repo_path(path: str | Path) -> Path:
    """Resolve a repo-relative or absolute path."""
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def repo_rel(path: str | Path) -> str:
    """Render a path relative to the repo when possible."""
    value = repo_path(path).resolve()
    try:
        return str(value.relative_to(ROOT))
    except ValueError:
        return str(value)


def parse_input(value: str) -> tuple[str, Path]:
    """Parse LABEL=PATH or PATH input syntax."""
    if "=" in value:
        label, path_text = value.split("=", 1)
        label = label.strip()
        if not label:
            raise ValueError(f"empty input label in {value!r}")
        return label, repo_path(path_text)
    path = repo_path(value)
    return path.stem, path


def load_dataset(label: str, path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Load one retention dataset with strict array validation."""
    if not path.exists():
        raise FileNotFoundError(f"retention dataset not found: {path}")
    data = np.load(path, allow_pickle=False)
    missing = [key for key in REQUIRED_ARRAYS if key not in data.files]
    if missing:
        raise ValueError(f"{path} is missing arrays: {missing}")
    arrays = {key: np.asarray(data[key]) for key in REQUIRED_ARRAYS if key != "metadata_json"}
    metadata = json.loads(str(data["metadata_json"].item()))
    sample_count = int(arrays["student_obs"].shape[0])
    if sample_count <= 0:
        raise ValueError(f"{path} has no samples")
    if arrays["teacher_action_mean"].shape != (sample_count, 4):
        raise ValueError(
            f"{path} teacher_action_mean has shape {arrays['teacher_action_mean'].shape}, "
            f"expected ({sample_count}, 4)"
        )
    if arrays["teacher_action_logstd"].shape != arrays["teacher_action_mean"].shape:
        raise ValueError(
            f"{path} teacher_action_logstd has shape {arrays['teacher_action_logstd'].shape}, "
            f"expected {arrays['teacher_action_mean'].shape}"
        )
    for key, array in arrays.items():
        if array.shape[0] != sample_count:
            raise ValueError(
                f"{path} array {key} has length {array.shape[0]}, expected {sample_count}"
            )
    for key in ("student_obs", "teacher_action_mean", "teacher_action_logstd"):
        if not np.isfinite(arrays[key].astype(np.float32)).all():
            raise ValueError(f"{path} contains non-finite values in {key}")
    metadata.setdefault("source_label", label)
    metadata.setdefault("source_path", repo_rel(path))
    return arrays, metadata


def merge_datasets(inputs: list[tuple[str, Path]]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Merge input datasets and build combined metadata."""
    if not inputs:
        raise ValueError("at least one --input is required")

    loaded: list[tuple[str, Path, dict[str, np.ndarray], dict[str, Any]]] = []
    obs_dim: int | None = None
    for label, path in inputs:
        arrays, metadata = load_dataset(label, path)
        current_obs_dim = int(arrays["student_obs"].shape[1])
        if obs_dim is None:
            obs_dim = current_obs_dim
        elif current_obs_dim != obs_dim:
            raise ValueError(
                f"student_obs dimension mismatch: {path} has {current_obs_dim}, "
                f"expected {obs_dim}"
            )
        loaded.append((label, path, arrays, metadata))

    merged = {
        key: np.concatenate([arrays[key] for _label, _path, arrays, _metadata in loaded])
        for key in REQUIRED_ARRAYS
        if key != "metadata_json"
    }
    source_index = np.concatenate(
        [
            np.full(arrays["student_obs"].shape[0], index, dtype=np.int16)
            for index, (_label, _path, arrays, _metadata) in enumerate(loaded)
        ]
    )
    source_label = np.concatenate(
        [
            np.full(arrays["student_obs"].shape[0], label, dtype=np.str_)
            for label, _path, arrays, _metadata in loaded
        ]
    )
    merged["source_index"] = source_index
    merged["source_label"] = source_label

    success_seeds = sorted(int(seed) for seed in np.unique(merged["seed"]))
    source_summaries = []
    for index, (label, path, arrays, metadata) in enumerate(loaded):
        source_summaries.append(
            {
                "index": index,
                "label": label,
                "path": repo_rel(path),
                "num_samples": int(arrays["student_obs"].shape[0]),
                "success_seeds": sorted(int(seed) for seed in np.unique(arrays["seed"])),
                "metadata": metadata,
            }
        )

    metadata = {
        "schema_version": 1,
        "purpose": "v46 residual-frontier union teacher-retention KL dataset",
        "num_samples": int(merged["student_obs"].shape[0]),
        "student_obs_shape": [int(value) for value in merged["student_obs"].shape],
        "teacher_action_shape": [int(value) for value in merged["teacher_action_mean"].shape],
        "num_success_episodes": len(success_seeds),
        "success_seeds": success_seeds,
        "source_datasets": source_summaries,
    }
    return merged, metadata


def write_dataset(path: Path, arrays: dict[str, np.ndarray], metadata: dict[str, Any]) -> None:
    """Write the merged compressed retention dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        student_obs=np.asarray(arrays["student_obs"], dtype=np.float32),
        teacher_action_mean=np.asarray(arrays["teacher_action_mean"], dtype=np.float32),
        teacher_action_logstd=np.asarray(arrays["teacher_action_logstd"], dtype=np.float32),
        target_gate=np.asarray(arrays["target_gate"], dtype=np.int16),
        seed=np.asarray(arrays["seed"], dtype=np.int32),
        episode_step=np.asarray(arrays["episode_step"], dtype=np.int32),
        success_time_s=np.asarray(arrays["success_time_s"], dtype=np.float32),
        gate_axis=np.asarray(arrays["gate_axis"], dtype=np.float32),
        gate_lateral_error=np.asarray(arrays["gate_lateral_error"], dtype=np.float32),
        obstacle_min_dist=np.asarray(arrays["obstacle_min_dist"], dtype=np.float32),
        source_index=np.asarray(arrays["source_index"], dtype=np.int16),
        source_label=np.asarray(arrays["source_label"], dtype=np.str_),
        metadata_json=np.asarray(json.dumps(metadata, sort_keys=True), dtype=np.str_),
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        help="Input dataset as LABEL=PATH or PATH. May be repeated.",
    )
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def main() -> None:
    """Merge datasets and print the resulting metadata."""
    args = parse_args()
    inputs = [parse_input(value) for value in args.input]
    arrays, metadata = merge_datasets(inputs)
    out_path = repo_path(args.out)
    write_dataset(out_path, arrays, metadata)
    metadata["path"] = repo_rel(out_path)
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
