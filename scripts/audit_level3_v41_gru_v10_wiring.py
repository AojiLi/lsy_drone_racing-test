"""Run the v41 GRU/v10 Level3 wiring audit.

This script is diagnostic-only. It does not train, tune, or edit configs.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import gymnasium
import jax.numpy as jp
import numpy as np
import torch
from gymnasium.wrappers.jax_to_numpy import JaxToNumpy

from lsy_drone_racing.control import ppo_level3_inference
from lsy_drone_racing.control.ppo_level3_observation import (
    LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
    POLICY_ARCH_RECURRENT_ACTOR_GRU256,
    checkpoint_hidden_dim,
    checkpoint_policy_arch,
    checkpoint_recurrent_hidden_dim,
    unpack_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    NormalizeVectorActions,
    RecurrentActorAgent,
)
from lsy_drone_racing.utils import load_config
from scripts.check_level3_observation_event_parity import (
    flatten_training_obs,
    init_training_history,
    make_training_obs_probe,
    section_diffs,
)

ROOT = Path(__file__).parents[1]
DEFAULT_CHECKPOINT = (
    ROOT
    / "lsy_drone_racing/control/checkpoints/"
    "level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m/"
    "level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_step_003000000.ckpt"
)
DEFAULT_OUT = ROOT / "experiments/level3_ppo_loop/parity/2026-06-23_v41_gru_v10_wiring_audit.json"

REQUIRED_CHECKS = (
    "checkpoint_metadata",
    "observation_parity_and_sanity",
    "train_eval_action_scale_parity",
    "train_inference_recurrent_actor_parity",
    "zero_update_save_reload_parity",
    "hidden_state_reset_and_carry_parity",
    "recurrent_ppo_gradient_update_sanity",
)


def inject_checkpoint(checkpoint: Path) -> None:
    """Point ppo_level3_inference at an explicit checkpoint."""
    control_dir = Path(ppo_level3_inference.__file__).parent
    ppo_level3_inference.MODEL_NAME = str(checkpoint.resolve().relative_to(control_dir))


def make_env(config_name: str) -> tuple[Any, Any]:
    """Create a single Level3 environment without changing its track config."""
    config = load_config(ROOT / "config" / config_name)
    config.sim.render = False
    env = gymnasium.make(
        config.env.id,
        freq=config.env.freq,
        sim_config=config.sim,
        sensor_range=config.env.sensor_range,
        control_mode=config.env.control_mode,
        track=config.env.track,
        disturbances=config.env.get("disturbances"),
        randomizations=config.env.get("randomizations"),
        seed=config.env.seed,
    )
    return JaxToNumpy(env), config


def max_abs_diff(a: Any, b: Any) -> float:
    """Return max absolute difference between two arrays."""
    return float(np.max(np.abs(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64))))


def json_default(value: Any) -> Any:
    """Convert numpy scalars that can appear in audit reports."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def load_training_agent(
    checkpoint_path: Path,
    device: torch.device,
) -> tuple[RecurrentActorAgent, dict[str, Any]]:
    """Load the training-side recurrent Agent from a checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model_state_dict, observation_layout = unpack_checkpoint(checkpoint)
    hidden_dim = checkpoint_hidden_dim(checkpoint, model_state_dict)
    recurrent_hidden_dim = checkpoint_recurrent_hidden_dim(checkpoint, model_state_dict)
    obs_dim = int(model_state_dict["actor_pre.0.weight"].shape[1])
    action_dim = int(model_state_dict["actor_post.4.weight"].shape[0])
    agent = RecurrentActorAgent(
        (obs_dim,),
        (action_dim,),
        hidden_dim=hidden_dim,
        recurrent_hidden_dim=int(recurrent_hidden_dim or hidden_dim),
    ).to(device)
    agent.load_state_dict(model_state_dict)
    agent.eval()
    metadata = {
        "observation_layout": observation_layout,
        "policy_arch": checkpoint_policy_arch(checkpoint, model_state_dict),
        "hidden_dim": hidden_dim,
        "recurrent_hidden_dim": int(recurrent_hidden_dim or hidden_dim),
        "obs_dim": obs_dim,
        "action_dim": action_dim,
    }
    return agent, metadata


def tensor_diff(a: torch.Tensor, b: torch.Tensor) -> float:
    """Return max absolute diff for tensors."""
    return float(torch.max(torch.abs(a.detach().cpu() - b.detach().cpu())).item())


def check_checkpoint_metadata(metadata: dict[str, Any], checkpoint: Path) -> dict[str, Any]:
    """Validate the checkpoint is the intended v40 recurrent/v10 artifact."""
    clean = (
        metadata["policy_arch"] == POLICY_ARCH_RECURRENT_ACTOR_GRU256
        and metadata["observation_layout"] == LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT
        and metadata["obs_dim"] > 0
        and metadata["recurrent_hidden_dim"] == 256
    )
    return {
        "clean": clean,
        "checkpoint": str(checkpoint.relative_to(ROOT)),
        **metadata,
    }


def check_observation_parity_and_sanity(
    controller: Any,
    env: Any,
    config: Any,
    *,
    seeds: list[int],
    tolerance: float,
) -> dict[str, Any]:
    """Compare training v10 flattening with inference v10 flattening."""
    rows: list[dict[str, Any]] = []
    max_diff = 0.0
    all_finite = True
    section_max_abs: dict[str, float] = {}
    nonzero_sections: dict[str, bool] = {
        "phase_progress": False,
        "gate_corridor_obstacles": False,
        "gate_aperture_margin": False,
    }

    for seed in seeds:
        obs, _info = env.reset(seed=seed)
        controller.reset_episode_state(obs)
        probe = make_training_obs_probe(
            obs,
            ppo_level3_inference.N_HISTORY,
            controller.observation_layout,
            float(controller.action_lowpass_alpha),
        )
        history = init_training_history(probe, obs)
        last_action = np.zeros(controller.action_dim, dtype=np.float32)
        train_flat = flatten_training_obs(probe, obs, history, last_action)
        infer_flat = controller._obs_rl(obs)  # noqa: SLF001
        worst_name, worst_value, diffs = section_diffs(probe.layout, train_flat, infer_flat)
        max_diff = max(max_diff, worst_value)
        all_finite = all_finite and bool(np.isfinite(infer_flat).all()) and bool(
            np.isfinite(train_flat).all()
        )
        for name, value in diffs.items():
            section_max_abs[name] = max(section_max_abs.get(name, 0.0), float(value))
        for section in nonzero_sections:
            for name, slc in probe.layout:
                if name == section:
                    nonzero_sections[section] = nonzero_sections[section] or bool(
                        np.max(np.abs(train_flat[slc])) > 1e-6
                    )
        rows.append(
            {
                "seed": seed,
                "obs_dim": int(infer_flat.size),
                "worst_section": worst_name,
                "worst_section_max_abs_diff": worst_value,
                "infer_abs_max": float(np.max(np.abs(infer_flat))),
                "train_abs_max": float(np.max(np.abs(train_flat))),
            }
        )

    clean = all_finite and max_diff <= tolerance and all(nonzero_sections.values())
    return {
        "clean": clean,
        "tolerance": tolerance,
        "max_abs_diff": max_diff,
        "all_finite": all_finite,
        "nonzero_sections": nonzero_sections,
        "section_max_abs_diffs": section_max_abs,
        "rows": rows,
        "config_track_id": str(config.env.track),
    }


def check_action_scale_parity(
    controller: Any,
    env: Any,
    *,
    seed: int,
    samples: int,
    tolerance: float,
) -> dict[str, Any]:
    """Compare training NormalizeVectorActions with inference scaling."""
    rng = np.random.default_rng(seed)
    action_low = np.asarray(env.action_space.low, dtype=np.float32)
    action_high = np.asarray(env.action_space.high, dtype=np.float32)
    train_scale = (action_high - action_low) / 2.0
    train_mean = (action_high + action_low) / 2.0
    actions_norm = rng.uniform(-1.5, 1.5, size=(samples, controller.action_dim)).astype(np.float32)
    train_scaled = np.asarray(
        NormalizeVectorActions._scale_actions(
            jp.asarray(actions_norm), jp.asarray(train_scale), jp.asarray(train_mean)
        ),
        dtype=np.float32,
    )
    infer_scaled = np.stack(
        [controller._scale_action(action_norm) for action_norm in actions_norm],  # noqa: SLF001
        axis=0,
    ).astype(np.float32)
    diffs = {
        "action_low": max_abs_diff(action_low, controller.action_low),
        "action_high": max_abs_diff(action_high, controller.action_high),
        "action_scale": max_abs_diff(train_scale, controller.action_scale),
        "action_mean": max_abs_diff(train_mean, controller.action_mean),
        "scaled_samples": max_abs_diff(train_scaled, infer_scaled),
    }
    return {
        "clean": all(value <= tolerance for value in diffs.values()),
        "tolerance": tolerance,
        "samples": samples,
        "diffs": diffs,
    }


def recurrent_forward(
    agent: RecurrentActorAgent,
    obs_tensor: torch.Tensor,
    hidden: torch.Tensor,
    done: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Run deterministic recurrent forward for parity checks."""
    with torch.no_grad():
        return agent.get_action_and_value(obs_tensor, hidden, done, deterministic=True)


def check_train_inference_recurrent_actor_parity(
    train_agent: RecurrentActorAgent,
    controller: Any,
    obs_rl: np.ndarray,
    *,
    tolerance: float,
) -> dict[str, Any]:
    """Compare train-side and inference-side recurrent networks."""
    device = controller.device
    obs_tensor = torch.tensor(obs_rl, dtype=torch.float32, device=device).unsqueeze(0)
    train_hidden = train_agent.get_initial_state(1, device)
    infer_hidden = controller.agent.get_initial_state(1, device)
    done = torch.zeros(1, dtype=torch.float32, device=device)
    train_action, train_logprob, train_entropy, train_value, train_next = recurrent_forward(
        train_agent, obs_tensor, train_hidden, done
    )
    with torch.no_grad():
        infer_action, infer_logprob, infer_entropy, infer_value, infer_next = (
            controller.agent.get_action_and_value(
                obs_tensor,
                infer_hidden,
                done,
                deterministic=True,
            )
        )
    diffs = {
        "action": tensor_diff(train_action, infer_action),
        "logprob": tensor_diff(train_logprob, infer_logprob),
        "entropy": tensor_diff(train_entropy, infer_entropy),
        "value": tensor_diff(train_value, infer_value),
        "next_hidden": tensor_diff(train_next, infer_next),
    }
    return {
        "clean": all(value <= tolerance for value in diffs.values()),
        "tolerance": tolerance,
        "diffs": diffs,
        "action_norm": train_action.squeeze(0).detach().cpu().tolist(),
        "next_hidden_norm": float(torch.linalg.vector_norm(train_next).detach().cpu().item()),
    }


def check_zero_update_save_reload_parity(
    checkpoint_path: Path,
    train_agent: RecurrentActorAgent,
    obs_rl: np.ndarray,
    *,
    tolerance: float,
) -> dict[str, Any]:
    """Save/reload a checkpoint and confirm deterministic outputs are unchanged."""
    device = next(train_agent.parameters()).device
    obs_tensor = torch.tensor(obs_rl, dtype=torch.float32, device=device).unsqueeze(0)
    hidden = train_agent.get_initial_state(1, device)
    done = torch.zeros(1, dtype=torch.float32, device=device)
    before = recurrent_forward(train_agent, obs_tensor, hidden, done)
    original = torch.load(checkpoint_path, map_location=device)
    with tempfile.TemporaryDirectory(prefix="v41_zero_update_") as tmpdir:
        temp_path = Path(tmpdir) / "zero_update.ckpt"
        torch.save(original, temp_path)
        reloaded_agent, _metadata = load_training_agent(temp_path, device)
        after = recurrent_forward(reloaded_agent, obs_tensor, hidden, done)
    names = ("action", "logprob", "entropy", "value", "next_hidden")
    diffs = {name: tensor_diff(left, right) for name, left, right in zip(names, before, after)}
    return {
        "clean": all(value <= tolerance for value in diffs.values()),
        "tolerance": tolerance,
        "diffs": diffs,
    }


def check_hidden_state_reset_and_carry(
    train_agent: RecurrentActorAgent,
    controller: Any,
    obs_rl: np.ndarray,
    *,
    tolerance: float,
) -> dict[str, Any]:
    """Check recurrent hidden carry and done-reset semantics."""
    device = controller.device
    base = torch.tensor(obs_rl, dtype=torch.float32, device=device)
    obs_seq = torch.stack([base, base * 0.97 + 0.01, base * 1.03 - 0.02], dim=0).unsqueeze(1)
    done_seq = torch.zeros((3, 1), dtype=torch.float32, device=device)
    hidden0 = train_agent.get_initial_state(1, device)

    with torch.no_grad():
        seq_action, _seq_logprob, _seq_entropy, _seq_value, seq_hidden = (
            train_agent.get_action_and_value(
                obs_seq,
                hidden0.clone(),
                done_seq,
                deterministic=True,
            )
        )
        step_hidden = hidden0.clone()
        step_actions = []
        for t in range(obs_seq.shape[0]):
            action, _logprob, _entropy, _value, step_hidden = train_agent.get_action_and_value(
                obs_seq[t],
                step_hidden,
                done_seq[t],
                deterministic=True,
            )
            step_actions.append(action)
        step_action = torch.cat(step_actions, dim=0)

        carried_hidden_norm = float(torch.linalg.vector_norm(step_hidden).cpu().item())
        reset_done = torch.ones(1, dtype=torch.float32, device=device)
        nonzero_hidden = step_hidden + 0.25
        reset_action, _a, _b, _c, reset_next = train_agent.get_action_and_value(
            obs_seq[0],
            nonzero_hidden,
            reset_done,
            deterministic=True,
        )
        zero_action, _a, _b, _c, zero_next = train_agent.get_action_and_value(
            obs_seq[0],
            hidden0,
            torch.zeros(1, dtype=torch.float32, device=device),
            deterministic=True,
        )

    controller._recurrent_hidden_state = controller.agent.get_initial_state(1, device)  # noqa: SLF001
    before_norm = float(torch.linalg.vector_norm(controller._recurrent_hidden_state).cpu().item())  # noqa: SLF001
    controller_hidden_action, _lp, _ent, _val, controller_next = (
        controller.agent.get_action_and_value(
            base.unsqueeze(0),
            controller._recurrent_hidden_state,  # noqa: SLF001
            torch.zeros(1, dtype=torch.float32, device=device),
            deterministic=True,
        )
    )
    controller._recurrent_hidden_state = controller_next  # noqa: SLF001
    carried_controller_norm = float(
        torch.linalg.vector_norm(controller._recurrent_hidden_state).cpu().item()  # noqa: SLF001
    )

    diffs = {
        "sequence_vs_step_action": tensor_diff(seq_action, step_action),
        "sequence_vs_step_hidden": tensor_diff(seq_hidden, step_hidden),
        "done_reset_action_vs_zero_hidden": tensor_diff(reset_action, zero_action),
        "done_reset_next_hidden_vs_zero_hidden": tensor_diff(reset_next, zero_next),
        "controller_direct_action_vs_train": tensor_diff(controller_hidden_action, zero_action),
    }
    return {
        "clean": (
            all(value <= tolerance for value in diffs.values())
            and carried_hidden_norm > 1e-6
            and before_norm == 0.0
            and carried_controller_norm > 1e-6
        ),
        "tolerance": tolerance,
        "diffs": diffs,
        "train_carried_hidden_norm": carried_hidden_norm,
        "controller_hidden_norm_before": before_norm,
        "controller_hidden_norm_after": carried_controller_norm,
    }


def check_recurrent_ppo_gradient_update_sanity(
    train_agent: RecurrentActorAgent,
    obs_rl: np.ndarray,
) -> dict[str, Any]:
    """Confirm recurrent Actor/log_std get gradients and one update moves actions."""
    device = next(train_agent.parameters()).device
    agent = RecurrentActorAgent(
        (train_agent.actor_pre[0].in_features,),
        (train_agent.actor_post[4].out_features,),
        hidden_dim=train_agent.hidden_dim,
        recurrent_hidden_dim=train_agent.recurrent_hidden_dim,
    ).to(device)
    agent.load_state_dict(train_agent.state_dict())
    agent.train()

    torch.manual_seed(410)
    base = torch.tensor(obs_rl, dtype=torch.float32, device=device)
    obs_seq = torch.stack(
        [base + 0.01 * torch.randn_like(base) for _ in range(4)],
        dim=0,
    ).unsqueeze(1)
    hidden = agent.get_initial_state(1, device)
    done = torch.zeros((4, 1), dtype=torch.float32, device=device)
    probe_action_before, _lp, _ent, _value, _hidden = agent.get_action_and_value(
        obs_seq,
        hidden,
        done,
        deterministic=True,
    )

    action = torch.tanh(torch.randn((4, 1, 4), dtype=torch.float32, device=device) * 0.5)
    advantages = torch.tensor([1.0, -0.5, 0.75, -1.25], dtype=torch.float32, device=device)
    returns = torch.linspace(-0.5, 0.5, 4, dtype=torch.float32, device=device)
    _sampled_action, logprob, entropy, value, _next_hidden = agent.get_action_and_value(
        obs_seq,
        hidden,
        done,
        action=action,
    )
    value = value.reshape(-1)
    loss = -(logprob * advantages).mean() + 0.25 * ((value - returns) ** 2).mean()
    loss = loss - 0.01 * entropy.mean()
    optimizer = torch.optim.Adam(agent.parameters(), lr=1e-3)
    optimizer.zero_grad()
    loss.backward()
    grad_norms = {
        "actor_pre": float(agent.actor_pre[0].weight.grad.norm().detach().cpu().item()),
        "actor_gru_ih": float(agent.actor_gru.weight_ih_l0.grad.norm().detach().cpu().item()),
        "actor_gru_hh": float(agent.actor_gru.weight_hh_l0.grad.norm().detach().cpu().item()),
        "actor_post": float(agent.actor_post[4].weight.grad.norm().detach().cpu().item()),
        "actor_logstd": float(agent.actor_logstd.grad.norm().detach().cpu().item()),
        "critic": float(agent.critic[0].weight.grad.norm().detach().cpu().item()),
    }
    optimizer.step()
    probe_action_after, _lp, _ent, _value, _hidden = agent.get_action_and_value(
        obs_seq,
        hidden,
        done,
        deterministic=True,
    )
    action_delta = tensor_diff(probe_action_before, probe_action_after)
    clean = all(value > 0.0 and np.isfinite(value) for value in grad_norms.values())
    clean = clean and action_delta > 1e-7 and np.isfinite(action_delta)
    return {
        "clean": clean,
        "loss": float(loss.detach().cpu().item()),
        "grad_norms": grad_norms,
        "deterministic_action_delta_after_one_update": action_delta,
    }


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    """Run all v41 checks and return a JSON-serializable report."""
    checkpoint = args.checkpoint.resolve()
    device = torch.device(args.device)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    inject_checkpoint(checkpoint)
    env, config = make_env(args.config)
    try:
        obs, info = env.reset(seed=args.seed)
        controller = ppo_level3_inference.PPOLevel2Inference(obs, info, config)
        train_agent, metadata = load_training_agent(checkpoint, device)
        train_agent.eval()
        controller.reset_episode_state(obs)
        obs_rl = controller._obs_rl(obs)  # noqa: SLF001

        seed_list = [args.seed + offset for offset in range(args.observation_seeds)]
        checks = {
            "checkpoint_metadata": check_checkpoint_metadata(metadata, checkpoint),
            "observation_parity_and_sanity": check_observation_parity_and_sanity(
                controller,
                env,
                config,
                seeds=seed_list,
                tolerance=args.tolerance,
            ),
            "train_eval_action_scale_parity": check_action_scale_parity(
                controller,
                env,
                seed=args.seed,
                samples=args.action_samples,
                tolerance=args.tolerance,
            ),
            "train_inference_recurrent_actor_parity": (
                check_train_inference_recurrent_actor_parity(
                    train_agent,
                    controller,
                    obs_rl,
                    tolerance=args.tolerance,
                )
            ),
            "zero_update_save_reload_parity": check_zero_update_save_reload_parity(
                checkpoint,
                train_agent,
                obs_rl,
                tolerance=args.tolerance,
            ),
            "hidden_state_reset_and_carry_parity": check_hidden_state_reset_and_carry(
                train_agent,
                controller,
                obs_rl,
                tolerance=args.tolerance,
            ),
            "recurrent_ppo_gradient_update_sanity": (
                check_recurrent_ppo_gradient_update_sanity(train_agent, obs_rl)
            ),
        }
        clean = all(check["clean"] for check in checks.values())
        return {
            "schema_version": 1,
            "audit": "v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity",
            "config": args.config,
            "track_geometry_modified": False,
            "training_launched": False,
            "required_checks": list(REQUIRED_CHECKS),
            "clean": clean,
            "checks": checks,
        }
    finally:
        env.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="level3.toml")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--observation-seeds", type=int, default=3)
    parser.add_argument("--action-samples", type=int, default=512)
    parser.add_argument("--tolerance", type=float, default=1e-5)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def main() -> None:
    """Run the audit and write its JSON report."""
    args = parse_args()
    report = run_audit(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    report_text = json.dumps(report, default=json_default, indent=2, sort_keys=True)
    args.out.write_text(report_text + "\n")
    print(report_text)
    if not report["clean"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
