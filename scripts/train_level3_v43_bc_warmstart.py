"""Train a GRU/v10 behavior-cloning warmstart checkpoint for Level3 PPO."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor, optim

from lsy_drone_racing.control.ppo_level3_observation import (
    DEFAULT_ACTION_LOWPASS_ALPHA,
    DEFAULT_ACTION_RP_LIMIT_DEG,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    POLICY_ARCH_RECURRENT_ACTOR_GRU256,
    make_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    RecurrentActorAgent,
    v27_distribution_retention_metrics,
)

ROOT = Path(__file__).parents[1]
DEFAULT_DATASET = (
    "experiments/level3_ppo_loop/retention_datasets/"
    "v43_success_teacher_v5_student_v10_train_pool.npz"
)
DEFAULT_OUT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_v43_success_trajectory_bc_warmstart/"
    "level3_v43_success_trajectory_bc_warmstart.ckpt"
)
DEFAULT_METRICS = (
    "experiments/level3_ppo_loop/parity/"
    "2026-06-23_v43_success_trajectory_bc_warmstart_metrics.json"
)


@dataclass(frozen=True)
class SequenceDataset:
    """In-memory sequence dataset for supervised recurrent Actor warmstart."""

    obs: np.ndarray
    teacher_mean: np.ndarray
    teacher_logstd: np.ndarray
    sequences: tuple[np.ndarray, ...]
    metadata: dict[str, Any]

    @property
    def obs_dim(self) -> int:
        """Return flattened Actor observation dimension."""
        return int(self.obs.shape[1])

    @property
    def action_dim(self) -> int:
        """Return normalized action dimension."""
        return int(self.teacher_mean.shape[1])


def repo_path(value: str | Path) -> Path:
    """Resolve a repo-relative path."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def _metadata_from_npz(data: np.lib.npyio.NpzFile) -> dict[str, Any]:
    if "metadata_json" not in data.files:
        return {}
    raw = data["metadata_json"]
    try:
        return json.loads(str(raw.item()))
    except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
        return {}


def load_sequence_dataset(path: str | Path, min_sequence_len: int = 2) -> SequenceDataset:
    """Load retention-style samples and group them into episode sequences."""
    dataset_path = repo_path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"dataset not found: {dataset_path}")

    data = np.load(dataset_path, allow_pickle=False)
    required = ("student_obs", "teacher_action_mean", "teacher_action_logstd", "seed")
    missing = [key for key in required if key not in data.files]
    if missing:
        raise ValueError(f"dataset is missing arrays: {missing}")

    obs = np.asarray(data["student_obs"], dtype=np.float32)
    teacher_mean = np.asarray(data["teacher_action_mean"], dtype=np.float32)
    teacher_logstd = np.asarray(data["teacher_action_logstd"], dtype=np.float32)
    seeds = np.asarray(data["seed"], dtype=np.int64)
    episode_steps = (
        np.asarray(data["episode_step"], dtype=np.int64)
        if "episode_step" in data.files
        else np.arange(obs.shape[0], dtype=np.int64)
    )

    if obs.ndim != 2:
        raise ValueError(f"student_obs must be rank 2, got shape {obs.shape}")
    if teacher_mean.shape != (obs.shape[0], 4):
        raise ValueError(
            "teacher_action_mean must have shape "
            f"({obs.shape[0]}, 4), got {teacher_mean.shape}"
        )
    if teacher_logstd.shape != teacher_mean.shape:
        raise ValueError(
            f"teacher_action_logstd shape {teacher_logstd.shape} "
            f"does not match {teacher_mean.shape}"
        )
    for name, array in (
        ("student_obs", obs),
        ("teacher_action_mean", teacher_mean),
        ("teacher_action_logstd", teacher_logstd),
    ):
        if not np.isfinite(array).all():
            raise ValueError(f"dataset contains non-finite {name}")

    sequences: list[np.ndarray] = []
    for seed in np.unique(seeds):
        indices = np.where(seeds == seed)[0]
        order = np.argsort(episode_steps[indices], kind="stable")
        ordered = indices[order]
        if ordered.size >= min_sequence_len:
            sequences.append(ordered.astype(np.int64))

    if not sequences:
        raise ValueError("dataset has no episode sequence long enough for BC")

    metadata = _metadata_from_npz(data)
    metadata.update(
        {
            "dataset_path": str(dataset_path),
            "num_samples": int(obs.shape[0]),
            "num_sequences": len(sequences),
            "obs_dim": int(obs.shape[1]),
            "action_dim": int(teacher_mean.shape[1]),
        }
    )
    return SequenceDataset(
        obs=obs,
        teacher_mean=teacher_mean,
        teacher_logstd=teacher_logstd,
        sequences=tuple(sequences),
        metadata=metadata,
    )


def sample_sequence_batch(
    dataset: SequenceDataset,
    *,
    sequence_len: int,
    batch_size: int,
    rng: np.random.Generator,
    device: torch.device,
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    """Sample time-major sequence tensors and reset GRU state at sequence starts."""
    if sequence_len <= 0:
        raise ValueError("sequence_len must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    obs_batch = np.zeros((sequence_len, batch_size, dataset.obs_dim), dtype=np.float32)
    mean_batch = np.zeros((sequence_len, batch_size, dataset.action_dim), dtype=np.float32)
    logstd_batch = np.zeros_like(mean_batch)
    done_batch = np.zeros((sequence_len, batch_size), dtype=np.float32)
    done_batch[0, :] = 1.0

    for batch_idx in range(batch_size):
        seq = dataset.sequences[int(rng.integers(len(dataset.sequences)))]
        if seq.size >= sequence_len:
            start = int(rng.integers(seq.size - sequence_len + 1))
            indices = seq[start : start + sequence_len]
        else:
            pad = np.repeat(seq[-1:], sequence_len - seq.size)
            indices = np.concatenate([seq, pad])
        obs_batch[:, batch_idx] = dataset.obs[indices]
        mean_batch[:, batch_idx] = dataset.teacher_mean[indices]
        logstd_batch[:, batch_idx] = dataset.teacher_logstd[indices]

    return (
        torch.as_tensor(obs_batch, dtype=torch.float32, device=device),
        torch.as_tensor(mean_batch, dtype=torch.float32, device=device),
        torch.as_tensor(logstd_batch, dtype=torch.float32, device=device),
        torch.as_tensor(done_batch, dtype=torch.float32, device=device),
    )


def bc_loss(
    agent: RecurrentActorAgent,
    obs: Tensor,
    teacher_mean: Tensor,
    teacher_logstd: Tensor,
    done: Tensor,
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    """Return supervised KL, MSE, agreement, and student action mean."""
    hidden = agent.get_initial_state(obs.shape[1], obs.device)
    student_mean, _ = agent._actor_mean(obs, hidden, done)
    student_logstd = agent.actor_logstd.expand_as(student_mean)
    flat_teacher_mean = teacher_mean.reshape_as(student_mean)
    flat_teacher_logstd = teacher_logstd.reshape_as(student_mean)
    teacher_kl, teacher_action_mse, teacher_agreement = v27_distribution_retention_metrics(
        student_mean,
        student_logstd,
        flat_teacher_mean,
        flat_teacher_logstd,
    )
    return teacher_kl, teacher_action_mse, teacher_agreement, student_mean


def train_bc(
    dataset: SequenceDataset,
    *,
    out_path: Path,
    metrics_path: Path | None,
    observation_layout: str,
    hidden_dim: int,
    recurrent_hidden_dim: int,
    sequence_len: int,
    batch_size: int,
    steps: int,
    lr: float,
    seed: int,
    action_rp_limit_deg: float,
    action_lowpass_alpha: float,
    device: torch.device,
) -> dict[str, Any]:
    """Train and save a recurrent Actor checkpoint from trajectory imitation."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    agent = RecurrentActorAgent(
        (dataset.obs_dim,),
        (dataset.action_dim,),
        hidden_dim=hidden_dim,
        recurrent_hidden_dim=recurrent_hidden_dim,
    ).to(device)
    optimizer = optim.AdamW(agent.parameters(), lr=lr, eps=1e-5)

    eval_batch = sample_sequence_batch(
        dataset,
        sequence_len=sequence_len,
        batch_size=batch_size,
        rng=rng,
        device=device,
    )
    with torch.no_grad():
        initial_kl, initial_mse, initial_agreement, initial_mean = bc_loss(
            agent,
            *eval_batch,
        )
        initial_action_abs_mean = float(initial_mean.abs().mean().cpu().item())

    for _step in range(steps):
        batch = sample_sequence_batch(
            dataset,
            sequence_len=sequence_len,
            batch_size=batch_size,
            rng=rng,
            device=device,
        )
        teacher_kl, teacher_action_mse, teacher_agreement, student_mean = bc_loss(
            agent,
            *batch,
        )
        loss = teacher_kl + teacher_action_mse
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(agent.parameters(), 1.0)
        optimizer.step()

    with torch.no_grad():
        final_kl, final_mse, final_agreement, final_mean = bc_loss(
            agent,
            *eval_batch,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = make_checkpoint(
        agent.state_dict(),
        hidden_dim=hidden_dim,
        observation_layout=observation_layout,
        action_rp_limit_deg=action_rp_limit_deg,
        action_lowpass_alpha=action_lowpass_alpha,
        policy_arch=POLICY_ARCH_RECURRENT_ACTOR_GRU256,
        recurrent_hidden_dim=recurrent_hidden_dim,
        recurrent_sequence_len=sequence_len,
        extra_metadata={
            "v43_bc_warmstart": {
                "dataset": dataset.metadata,
                "steps": int(steps),
                "batch_size": int(batch_size),
                "sequence_len": int(sequence_len),
                "learning_rate": float(lr),
                "seed": int(seed),
            }
        },
    )
    torch.save(checkpoint, out_path)

    metrics = {
        "checkpoint": str(out_path),
        "observation_layout": observation_layout,
        "policy_arch": POLICY_ARCH_RECURRENT_ACTOR_GRU256,
        "dataset": dataset.metadata,
        "steps": int(steps),
        "batch_size": int(batch_size),
        "sequence_len": int(sequence_len),
        "initial_teacher_kl": float(initial_kl.cpu().item()),
        "initial_teacher_action_mse": float(initial_mse.cpu().item()),
        "initial_teacher_agreement": float(initial_agreement.cpu().item()),
        "initial_action_abs_mean": initial_action_abs_mean,
        "final_teacher_kl": float(final_kl.cpu().item()),
        "final_teacher_action_mse": float(final_mse.cpu().item()),
        "final_teacher_agreement": float(final_agreement.cpu().item()),
        "final_action_abs_mean": float(final_mean.abs().mean().cpu().item()),
    }
    if metrics_path is not None:
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    return metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--metrics-out", default=DEFAULT_METRICS)
    parser.add_argument(
        "--observation-layout",
        default=LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    )
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--recurrent-hidden-dim", type=int, default=256)
    parser.add_argument("--sequence-len", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=43)
    parser.add_argument("--action-rp-limit-deg", type=float, default=DEFAULT_ACTION_RP_LIMIT_DEG)
    parser.add_argument("--action-lowpass-alpha", type=float, default=DEFAULT_ACTION_LOWPASS_ALPHA)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run v43 behavior-cloning warmstart training."""
    args = parse_args(argv)
    dataset = load_sequence_dataset(args.dataset, min_sequence_len=2)
    metrics = train_bc(
        dataset,
        out_path=repo_path(args.out),
        metrics_path=repo_path(args.metrics_out) if args.metrics_out else None,
        observation_layout=args.observation_layout,
        hidden_dim=args.hidden_dim,
        recurrent_hidden_dim=args.recurrent_hidden_dim,
        sequence_len=args.sequence_len,
        batch_size=args.batch_size,
        steps=args.steps,
        lr=args.learning_rate,
        seed=args.seed,
        action_rp_limit_deg=args.action_rp_limit_deg,
        action_lowpass_alpha=args.action_lowpass_alpha,
        device=torch.device(args.device),
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
