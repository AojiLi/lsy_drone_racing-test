"""Tests for the Level3 v37 GRU transfer preflight lane."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from lsy_drone_racing.control.ppo_level3_observation import (
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
    checkpoint_hidden_dim,
    checkpoint_policy_arch,
    checkpoint_recurrent_hidden_dim,
    make_checkpoint,
)
from lsy_drone_racing.control.train_CleanRL_ppo_level3 import (
    Agent,
    Args,
    MLPResidualRecurrentActorAgent,
    V27OnlineTeacher,
    load_v27_online_teacher,
    transfer_mlp_checkpoint_to_residual_gru,
    v27_online_teacher_retention_loss,
)
from scripts import level3_ppo_loop


@pytest.mark.unit
def test_loop_registers_v37_residual_gru_transfer_lane() -> None:
    """v37 must be explicit, track-safe, and routed through residual-GRU transfer."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v37_gru_transfer_memory_structure_from_loop101"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["observation_layout"] == LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V37_GRU_TRANSFER_DECISION_PACKET
    )
    assert hypothesis["requires_training_support"] == "mlp_to_gru_transfer_support"
    assert "mlp_to_gru_transfer_support" in (
        level3_ppo_loop.SUPPORTED_TRAINING_STRUCTURES
    )

    architecture = hypothesis["architecture"]
    assert architecture["track_geometry_change"] == "forbidden"
    assert architecture["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert architecture["transfer"]["source_checkpoint"] == (
        level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    )
    assert architecture["transfer"]["target_policy_arch"] == (
        POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    )
    assert architecture["transfer"]["preflight_packet"] == (
        level3_ppo_loop.V37_GRU_TRANSFER_PREFLIGHT_PACKET
    )

    params = hypothesis["params"]
    assert params["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert params["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert params["track_generator_profile"] == "default"
    assert params["recurrent_hidden_dim"] == 256
    assert params["recurrent_sequence_len"] == hypothesis["num_steps"]


@pytest.mark.unit
def test_loop_registers_v37b_from_loop107_1m_not_final() -> None:
    """v37b must continue only from the useful loop107 1M checkpoint."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v37b_residual_gru_maturation_from_loop107_1m"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["observation_layout"] == LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP107_V37_1M_CHECKPOINT
    assert "final" not in hypothesis["initial_checkpoint"]
    assert hypothesis["train_timesteps"] == 2_000_000
    assert hypothesis["checkpoint_interval"] == 500_000
    assert hypothesis["eval_milestones_m"] == "0.5,1,1.5,2"
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V37B_LOOP107_1M_DECISION_PACKET
    )

    architecture = hypothesis["architecture"]
    assert architecture["track_geometry_change"] == "forbidden"
    assert architecture["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert architecture["transfer"]["source_checkpoint"] == (
        level3_ppo_loop.LOOP107_V37_1M_CHECKPOINT
    )

    params = hypothesis["params"]
    assert params["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert params["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert params["track_generator_profile"] == "default"
    assert params["recurrent_hidden_dim"] == 256
    assert params["recurrent_sequence_len"] == hypothesis["num_steps"]


@pytest.mark.unit
def test_loop_registers_v38_teacher_retention_as_runnable_lane() -> None:
    """v38 must be explicit, track-safe, and backed by retention support."""
    hypothesis = level3_ppo_loop.STRUCTURAL_HYPOTHESES[
        "v38_gru_teacher_retention_distillation_from_loop107_1m"
    ]

    assert hypothesis["config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["eval_config"] == level3_ppo_loop.TARGET_EVAL_CONFIG
    assert hypothesis["observation_layout"] == LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    assert hypothesis["initial_checkpoint"] == level3_ppo_loop.LOOP107_V37_1M_CHECKPOINT
    assert hypothesis["approved_hypothesis_packet"] == (
        level3_ppo_loop.V38_RETENTION_DECISION_PACKET
    )
    assert hypothesis["requires_training_support"] == (
        "residual_gru_teacher_retention_support"
    )
    assert "residual_gru_teacher_retention_support" in (
        level3_ppo_loop.SUPPORTED_TRAINING_STRUCTURES
    )
    assert level3_ppo_loop.structural_hypothesis_runnable(hypothesis)

    architecture = hypothesis["architecture"]
    assert architecture["track_geometry_change"] == "forbidden"
    assert architecture["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert architecture["teacher_retention"]["student_start_checkpoint"] == (
        level3_ppo_loop.LOOP107_V37_1M_CHECKPOINT
    )
    assert architecture["teacher_retention"]["teacher_checkpoint"] == (
        level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT
    )

    params = hypothesis["params"]
    assert params["policy_arch"] == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert params["critic_observation_mode"] == CRITIC_OBSERVATION_SAME_AS_ACTOR
    assert params["track_generator_profile"] == "default"
    assert params["v27_teacher_kl_beta"] > 0.0
    assert params["v27_teacher_model_name"] == level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT


@pytest.mark.unit
def test_residual_gru_args_allow_online_teacher_without_dataset() -> None:
    """v38 retention uses an online teacher checkpoint instead of an npz dataset."""
    args = Args.create(
        num_steps=128,
        recurrent_sequence_len=128,
        policy_arch=POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        v27_teacher_kl_beta=0.08,
        v27_teacher_model_name=level3_ppo_loop.LOOP101_V33_BEST_CHECKPOINT,
        v27_teacher_observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    )

    assert args.policy_arch == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert args.v27_retention_dataset_path is None


@pytest.mark.unit
def test_online_teacher_retention_loss_samples_recurrent_minibatch() -> None:
    """Teacher retention must be active and finite on residual-GRU sequences."""
    torch.manual_seed(38)
    obs_shape = (68,)
    action_shape = (4,)
    teacher = Agent(obs_shape, action_shape, hidden_dim=256)
    student = MLPResidualRecurrentActorAgent(
        obs_shape,
        action_shape,
        hidden_dim=256,
        recurrent_hidden_dim=256,
    )
    student.load_state_dict(transfer_mlp_checkpoint_to_residual_gru(teacher.state_dict(), student))
    with torch.no_grad():
        student.actor_residual_head.bias.fill_(0.05)

    teacher_source = V27OnlineTeacher(
        agent=teacher,
        model_path=level3_ppo_loop.ROOT / "synthetic_teacher.ckpt",
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        policy_arch="mlp_2x_tanh",
    )
    seq_len = 4
    batch_size = 3
    obs = torch.randn(seq_len, batch_size, obs_shape[0]) * 0.25
    done = torch.zeros(seq_len, batch_size)
    done[2, 1] = 1.0
    hidden = student.get_initial_state(batch_size, torch.device("cpu"))

    teacher_kl, teacher_action_mse, teacher_agreement, sampled = (
        v27_online_teacher_retention_loss(
            student,
            teacher_source,
            obs,
            hidden,
            done,
            batch_size=7,
        )
    )
    teacher_kl.backward()

    assert sampled == 7
    assert torch.isfinite(teacher_kl)
    assert torch.isfinite(teacher_action_mse)
    assert torch.isfinite(teacher_agreement)
    assert teacher_action_mse.item() > 0.0
    assert student.actor_residual_head.bias.grad is not None


@pytest.mark.unit
def test_load_v27_online_teacher_from_checkpoint(tmp_path: Path) -> None:
    """The v38 teacher loader must validate checkpoint metadata and freeze weights."""
    torch.manual_seed(39)
    teacher = Agent((68,), (4,), hidden_dim=256)
    checkpoint_path = tmp_path / "teacher.ckpt"
    torch.save(
        make_checkpoint(
            teacher.state_dict(),
            hidden_dim=256,
            observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            policy_arch="mlp_2x_tanh",
        ),
        checkpoint_path,
    )
    args = Args.create(
        num_steps=128,
        recurrent_sequence_len=128,
        policy_arch=POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        v27_teacher_kl_beta=0.08,
        v27_teacher_model_name=str(checkpoint_path),
        v27_teacher_observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
    )

    source = load_v27_online_teacher(
        args,
        obs_shape=(68,),
        action_shape=(4,),
        device=torch.device("cpu"),
    )

    assert source is not None
    assert source.model_path == checkpoint_path
    assert source.observation_layout == LOCAL_OBSTACLE_OBSERVATION_LAYOUT
    assert not any(parameter.requires_grad for parameter in source.agent.parameters())


@pytest.mark.unit
def test_residual_gru_transfer_preserves_mlp_deterministic_policy() -> None:
    """Zero residual init should preserve the source MLP action mean and value."""
    torch.manual_seed(37)
    obs_shape = (68,)
    action_shape = (4,)
    source = Agent(obs_shape, action_shape, hidden_dim=256)
    target = MLPResidualRecurrentActorAgent(
        obs_shape,
        action_shape,
        hidden_dim=256,
        recurrent_hidden_dim=256,
    )

    transferred = transfer_mlp_checkpoint_to_residual_gru(source.state_dict(), target)
    target.load_state_dict(transferred)

    obs = torch.randn(8, obs_shape[0]) * 0.25
    done = torch.zeros(obs.shape[0])
    hidden = target.get_initial_state(obs.shape[0], torch.device("cpu"))

    source_action, source_logprob, source_entropy, source_value = source.get_action_and_value(
        obs,
        deterministic=True,
    )
    target_action, target_logprob, target_entropy, target_value, _ = (
        target.get_action_and_value(
            obs,
            hidden,
            done,
            action=source_action,
            deterministic=True,
        )
    )

    assert torch.allclose(target_action, source_action, atol=1e-6)
    assert torch.allclose(target_value, source_value, atol=1e-6)
    assert torch.allclose(target_logprob, source_logprob, atol=1e-6)
    assert torch.allclose(target_entropy, source_entropy, atol=1e-6)
    assert torch.count_nonzero(target.actor_residual_head.weight).item() == 0
    assert torch.count_nonzero(target.actor_residual_head.bias).item() == 0


@pytest.mark.unit
def test_residual_gru_checkpoint_metadata_round_trip() -> None:
    """Residual-GRU checkpoints must be distinguishable from MLP and pure GRU."""
    target = MLPResidualRecurrentActorAgent(
        (68,),
        (4,),
        hidden_dim=256,
        recurrent_hidden_dim=256,
    )

    checkpoint = make_checkpoint(
        target.state_dict(),
        hidden_dim=256,
        observation_layout=LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        policy_arch=POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256,
        recurrent_hidden_dim=256,
        recurrent_sequence_len=128,
    )

    assert checkpoint_policy_arch(checkpoint) == POLICY_ARCH_MLP_RESIDUAL_RECURRENT_ACTOR_GRU256
    assert checkpoint_hidden_dim(checkpoint) == 256
    assert checkpoint_recurrent_hidden_dim(checkpoint) == 256
    assert checkpoint["recurrent_sequence_len"] == 128


@pytest.mark.unit
def test_residual_gru_done_mask_resets_hidden_state() -> None:
    """A done mask must make a nonzero hidden state behave like a fresh episode."""
    torch.manual_seed(38)
    agent = MLPResidualRecurrentActorAgent(
        (68,),
        (4,),
        hidden_dim=256,
        recurrent_hidden_dim=256,
    )
    torch.nn.init.normal_(agent.actor_residual_head.weight, mean=0.0, std=0.02)
    torch.nn.init.normal_(agent.actor_residual_head.bias, mean=0.0, std=0.02)

    obs = torch.randn(3, 68)
    hidden = torch.randn(1, 3, 256)
    zero_hidden = agent.get_initial_state(3, torch.device("cpu"))
    done_reset = torch.ones(3)
    done_fresh = torch.zeros(3)

    reset_action, _, _, _, reset_next_hidden = agent.get_action_and_value(
        obs,
        hidden,
        done_reset,
        deterministic=True,
    )
    fresh_action, _, _, _, fresh_next_hidden = agent.get_action_and_value(
        obs,
        zero_hidden,
        done_fresh,
        deterministic=True,
    )

    assert torch.allclose(reset_action, fresh_action, atol=1e-6)
    assert torch.allclose(reset_next_hidden, fresh_next_hidden, atol=1e-6)
