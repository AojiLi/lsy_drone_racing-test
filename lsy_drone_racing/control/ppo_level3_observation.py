"""Observation-layout metadata for the direct Level3 PPO policy."""

from __future__ import annotations

import math
from typing import Any

LEGACY_OBSERVATION_LAYOUT = "legacy_obstacle_top_xyz_v0"
WORLD_HISTORY_OBSERVATION_LAYOUT = "obstacle_heading_xy_v1"
LOCAL_OBSTACLE_OBSERVATION_LAYOUT = "level3_target_gate_nearest_gate_2obs_local_history_v5"
LOCAL_NEXT_GATE_OBSERVATION_LAYOUT = "level3_target_next_gate_2obs_local_history_v6"
LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUT = "level3_target_gate_phase_progress_2obs_local_history_v7"
LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT = (
    "level3_gate_corridor_obstacle_relative_2obs_local_history_v8"
)
LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT = (
    "level3_gate_aperture_margin_2obs_local_history_v9"
)
LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT = (
    "level3_gate_corridor_aperture_margin_2obs_local_history_v10"
)
LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT = (
    "level3_gate_corridor_aperture_margin_minimal_2obs_local_history_v11"
)
DEFAULT_ACTION_RP_LIMIT_DEG = 90.0
DEFAULT_ACTION_LOWPASS_ALPHA = 1.0
POLICY_ARCH_MLP = "mlp_2x_tanh"
POLICY_ARCH_RECURRENT_ACTOR_GRU256 = "recurrent_actor_gru256"
SUPPORTED_POLICY_ARCHS = (POLICY_ARCH_MLP, POLICY_ARCH_RECURRENT_ACTOR_GRU256)

SUPPORTED_OBSERVATION_LAYOUTS = (
    WORLD_HISTORY_OBSERVATION_LAYOUT,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_NEXT_GATE_OBSERVATION_LAYOUT,
    LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
)
WORLD_HISTORY_OBSERVATION_LAYOUTS = (LEGACY_OBSERVATION_LAYOUT, WORLD_HISTORY_OBSERVATION_LAYOUT)
LOCAL_OBSTACLE_OBSERVATION_LAYOUTS = (
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_NEXT_GATE_OBSERVATION_LAYOUT,
    LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
)
LOCAL_NEXT_GATE_OBSERVATION_LAYOUTS = (LOCAL_NEXT_GATE_OBSERVATION_LAYOUT,)
LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUTS = (
    LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
)
LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUTS = (
    LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
)
LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUTS = (
    LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
)
LOCAL_GATE_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUTS = (
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
)


def infer_policy_arch(model_state_dict: dict[str, Any]) -> str:
    """Infer policy architecture from checkpoint parameter names."""
    if "actor_gru.weight_ih_l0" in model_state_dict:
        return POLICY_ARCH_RECURRENT_ACTOR_GRU256
    if "actor_mean.0.weight" in model_state_dict:
        return POLICY_ARCH_MLP
    raise ValueError("Cannot infer PPO policy architecture from checkpoint weights.")


def normalize_policy_arch(value: Any = POLICY_ARCH_MLP) -> str:
    """Return a validated policy architecture name."""
    policy_arch = POLICY_ARCH_MLP if value is None else str(value)
    if policy_arch not in SUPPORTED_POLICY_ARCHS:
        raise ValueError(f"Unsupported PPO policy_arch: {policy_arch}.")
    return policy_arch


def infer_hidden_dim(model_state_dict: dict[str, Any], policy_arch: str | None = None) -> int:
    """Infer the critic/shared hidden width from PPO weights."""
    policy_arch = normalize_policy_arch(policy_arch or infer_policy_arch(model_state_dict))
    key = "actor_mean.0.weight" if policy_arch == POLICY_ARCH_MLP else "critic.0.weight"
    try:
        hidden_dim = int(model_state_dict[key].shape[0])
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot infer PPO hidden_dim from {key}.") from exc
    if hidden_dim <= 0:
        raise ValueError(f"Invalid PPO hidden_dim inferred from checkpoint: {hidden_dim}.")
    return hidden_dim


def infer_recurrent_hidden_dim(model_state_dict: dict[str, Any]) -> int | None:
    """Infer GRU hidden width, or None for feed-forward policies."""
    if "actor_gru.weight_hh_l0" not in model_state_dict:
        return None
    try:
        recurrent_hidden_dim = int(model_state_dict["actor_gru.weight_hh_l0"].shape[1])
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("Cannot infer recurrent hidden_dim from actor_gru.weight_hh_l0.") from exc
    if recurrent_hidden_dim <= 0:
        raise ValueError(
            f"Invalid recurrent hidden_dim inferred from checkpoint: {recurrent_hidden_dim}."
        )
    return recurrent_hidden_dim


def checkpoint_policy_arch(
    checkpoint: Any, model_state_dict: dict[str, Any] | None = None
) -> str:
    """Return checkpoint policy architecture, defaulting old checkpoints to MLP."""
    if model_state_dict is None:
        model_state_dict, _ = unpack_checkpoint(checkpoint)
    inferred_policy_arch = infer_policy_arch(model_state_dict)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        metadata_policy_arch = checkpoint.get("policy_arch")
        if metadata_policy_arch is not None:
            metadata_policy_arch = normalize_policy_arch(metadata_policy_arch)
            if metadata_policy_arch != inferred_policy_arch:
                raise ValueError(
                    f"Checkpoint policy_arch metadata is {metadata_policy_arch}, "
                    f"but weights use {inferred_policy_arch}."
                )
    return inferred_policy_arch


def checkpoint_hidden_dim(checkpoint: Any, model_state_dict: dict[str, Any] | None = None) -> int:
    """Return checkpoint hidden width, validating metadata against the stored weights."""
    if model_state_dict is None:
        model_state_dict, _ = unpack_checkpoint(checkpoint)
    policy_arch = checkpoint_policy_arch(checkpoint, model_state_dict)
    inferred_hidden_dim = infer_hidden_dim(model_state_dict, policy_arch=policy_arch)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        metadata_hidden_dim = checkpoint.get("hidden_dim")
        if metadata_hidden_dim is not None and int(metadata_hidden_dim) != inferred_hidden_dim:
            raise ValueError(
                f"Checkpoint hidden_dim metadata is {metadata_hidden_dim}, "
                f"but actor weights use {inferred_hidden_dim}."
            )
    return inferred_hidden_dim


def checkpoint_recurrent_hidden_dim(
    checkpoint: Any, model_state_dict: dict[str, Any] | None = None
) -> int | None:
    """Return recurrent hidden width, validating metadata for recurrent policies."""
    if model_state_dict is None:
        model_state_dict, _ = unpack_checkpoint(checkpoint)
    inferred = infer_recurrent_hidden_dim(model_state_dict)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        metadata = checkpoint.get("recurrent_hidden_dim")
        if metadata is not None and inferred is not None and int(metadata) != inferred:
            raise ValueError(
                f"Checkpoint recurrent_hidden_dim metadata is {metadata}, "
                f"but GRU weights use {inferred}."
            )
    return inferred


def normalize_action_rp_limit_deg(value: Any = DEFAULT_ACTION_RP_LIMIT_DEG) -> float:
    """Return a validated roll/pitch command envelope in degrees."""
    if value is None:
        value = DEFAULT_ACTION_RP_LIMIT_DEG
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid action_rp_limit_deg metadata: {value!r}.") from exc
    if not math.isfinite(parsed) or parsed <= 0.0 or parsed > DEFAULT_ACTION_RP_LIMIT_DEG:
        raise ValueError(
            "action_rp_limit_deg must be finite and in "
            f"(0, {DEFAULT_ACTION_RP_LIMIT_DEG}], got {value!r}."
        )
    return parsed


def checkpoint_action_rp_limit_deg(checkpoint: Any) -> float:
    """Return checkpoint action-envelope metadata, defaulting old checkpoints to full range."""
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        return normalize_action_rp_limit_deg(
            checkpoint.get("action_rp_limit_deg", DEFAULT_ACTION_RP_LIMIT_DEG)
        )
    return DEFAULT_ACTION_RP_LIMIT_DEG


def normalize_action_lowpass_alpha(value: Any = DEFAULT_ACTION_LOWPASS_ALPHA) -> float:
    """Return a validated normalized-action low-pass factor."""
    if value is None:
        value = DEFAULT_ACTION_LOWPASS_ALPHA
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid action_lowpass_alpha metadata: {value!r}.") from exc
    if not math.isfinite(parsed) or parsed <= 0.0 or parsed > 1.0:
        raise ValueError(f"action_lowpass_alpha must be finite and in (0, 1], got {value!r}.")
    return parsed


def checkpoint_action_lowpass_alpha(checkpoint: Any) -> float:
    """Return checkpoint action low-pass metadata, defaulting old checkpoints to no filtering."""
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        return normalize_action_lowpass_alpha(
            checkpoint.get("action_lowpass_alpha", DEFAULT_ACTION_LOWPASS_ALPHA)
        )
    return DEFAULT_ACTION_LOWPASS_ALPHA


def make_checkpoint(
    model_state_dict: dict[str, Any],
    hidden_dim: int | None = None,
    observation_layout: str = WORLD_HISTORY_OBSERVATION_LAYOUT,
    action_rp_limit_deg: float = DEFAULT_ACTION_RP_LIMIT_DEG,
    action_lowpass_alpha: float = DEFAULT_ACTION_LOWPASS_ALPHA,
    policy_arch: str = POLICY_ARCH_MLP,
    recurrent_hidden_dim: int | None = None,
    recurrent_sequence_len: int | None = None,
) -> dict[str, Any]:
    """Package model weights with Level3 observation-layout and network-width metadata."""
    policy_arch = normalize_policy_arch(policy_arch)
    inferred_policy_arch = infer_policy_arch(model_state_dict)
    if inferred_policy_arch != policy_arch:
        raise ValueError(
            f"Requested policy_arch={policy_arch}, but weights use {inferred_policy_arch}."
        )
    inferred_hidden_dim = infer_hidden_dim(model_state_dict, policy_arch=policy_arch)
    if hidden_dim is not None and hidden_dim != inferred_hidden_dim:
        raise ValueError(
            f"Requested hidden_dim={hidden_dim}, but actor weights use {inferred_hidden_dim}."
        )
    inferred_recurrent_hidden_dim = infer_recurrent_hidden_dim(model_state_dict)
    if recurrent_hidden_dim is not None and inferred_recurrent_hidden_dim != recurrent_hidden_dim:
        raise ValueError(
            f"Requested recurrent_hidden_dim={recurrent_hidden_dim}, "
            f"but weights use {inferred_recurrent_hidden_dim}."
        )
    if observation_layout not in SUPPORTED_OBSERVATION_LAYOUTS:
        raise ValueError(f"Unsupported Level3 observation layout: {observation_layout}.")
    checkpoint = {
        "model_state_dict": model_state_dict,
        "observation_layout": observation_layout,
        "hidden_dim": inferred_hidden_dim,
        "policy_arch": policy_arch,
        "action_rp_limit_deg": normalize_action_rp_limit_deg(action_rp_limit_deg),
        "action_lowpass_alpha": normalize_action_lowpass_alpha(action_lowpass_alpha),
    }
    if inferred_recurrent_hidden_dim is not None:
        checkpoint["recurrent_hidden_dim"] = inferred_recurrent_hidden_dim
    if recurrent_sequence_len is not None:
        checkpoint["recurrent_sequence_len"] = int(recurrent_sequence_len)
    return checkpoint


def unpack_checkpoint(checkpoint: Any) -> tuple[dict[str, Any], str]:
    """Return model weights and layout, treating old raw state dicts as legacy."""
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        return checkpoint["model_state_dict"], checkpoint.get(
            "observation_layout", LEGACY_OBSERVATION_LAYOUT
        )
    return checkpoint, LEGACY_OBSERVATION_LAYOUT
