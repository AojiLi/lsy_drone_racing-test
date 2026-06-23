"""Resumable train/evaluate/tune loop for the Level3 PPO controller."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shlex
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTROL_DIR = ROOT / "lsy_drone_racing" / "control"
CHECKPOINT_ROOT = CONTROL_DIR / "checkpoints"
LOOP_DIR = ROOT / "experiments" / "level3_ppo_loop"
DEFAULT_STATE_PATH = LOOP_DIR / "state.json"
SEED_MANIFEST_DIR = LOOP_DIR / "seed_manifests"
DEFAULT_DEV_SEED_FILE = SEED_MANIFEST_DIR / "dev_seen_1_20.txt"
DEFAULT_VALIDATION_SEED_FILE = SEED_MANIFEST_DIR / "validation_unseen_101_200.txt"
DEFAULT_FINAL_SEED_FILE = SEED_MANIFEST_DIR / "final_locked_1001_1200.txt"
DEFAULT_INITIAL_DIR = CHECKPOINT_ROOT / "level3_DR_initial"
MAX_RESEARCH_CHARS = 12_000
TARGET_EVAL_CONFIG = "level3.toml"
DOMAIN_RANDOMIZED_TRAIN_CONFIG = "level3_dr.toml"
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
CRITIC_OBSERVATION_SAME_AS_ACTOR = "same_as_actor"
CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1 = "level3_full_state_v1"
CRITIC_OBSERVATION_MODE_CHOICES = {
    CRITIC_OBSERVATION_SAME_AS_ACTOR,
    CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
}
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

TARGET_SUCCESS_RATE = 0.60
TARGET_TIME_S = 7.0
DEFAULT_TRAIN_TIMESTEPS = 20_000_000
DEFAULT_CHECKPOINT_INTERVAL = 5_000_000
LONG_RUN_TIMESTEP_THRESHOLD = 30_000_000
SCREENING_TIMESTEPS = 30_000_000
MATURATION_TIMESTEPS = 60_000_000
CONFIRMATION_TIMESTEPS = 90_000_000
PROMISING_SUCCESS_RATE = 0.01
PROMISING_MEAN_GATES = 0.75
DEFAULT_EVAL_MILESTONES_M = "30,60,90,120,150"
DEFAULT_VALIDATION_PROMOTION_THRESHOLD = 0.20
DEFAULT_VALIDATION_PROMOTION_SECONDARY_SUCCESS = 0.15
DEFAULT_VALIDATION_PROMOTION_MEAN_GATES = 1.70
LEVEL2_STEP_CURVE_PACKET = (
    "experiments/level3_ppo_loop/analysis/2026-06-18_level2_checkpoint_step_curve.md"
)
STRUCTURAL_SEARCH_APPROVAL_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-19_user_approves_structural_search.md"
)
STATEIRVING_LEVEL3_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md"
)
LOOP031_CURRICULUM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop031_launch_v5_curriculum_lane.md"
)
LEGACY_CENTERLINE_SAFETY_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_legacy_centerline_safety_recovery_after_gate_potential.md"
)
LOOP032_SATURATION_DIAGNOSIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop032_domain_gap_saturation_diagnosis.md"
)
LOOP032_PPO_UPDATE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop032_launch_v5_ppo_update_pressure_lane.md"
)
LOOP033_MILD_LOWPASS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop033_launch_v5_mild_lowpass_pass_conversion_lane.md"
)
LOOP034_FRAME_CLEARANCE_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop034_frame_clearance_pass_conversion_synthesis.md"
)
LOOP034_FRAME_CLEARANCE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop034_launch_v5_frame_clearance_pass_conversion_lane.md"
)
LOOP035_DECOUPLED_FRAME_CLEARANCE_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop035_decoupled_frame_clearance_synthesis.md"
)
LOOP035_DECOUPLED_FRAME_CLEARANCE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop035_launch_v5_decoupled_frame_clearance_lane.md"
)
LOOP039_DIRECT_APERTURE_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop038_direct_aperture_synthesis.md"
)
LOOP039_DIRECT_APERTURE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop038_launch_direct_aperture_lane.md"
)
LOOP040_SOFT_FOLLOWTHROUGH_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop039_soft_centerline_followthrough_synthesis.md"
)
LOOP040_SOFT_FOLLOWTHROUGH_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop039_launch_soft_centerline_followthrough_lane.md"
)
LOOP042_SATURATION_GUARD_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop041_soft_centerline_saturation_guard_synthesis.md"
)
LOOP042_SATURATION_GUARD_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop041_launch_soft_centerline_saturation_guard_lane.md"
)
LOOP043_NEXT_GATE_OBS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop042_next_gate_observation_synthesis.md"
)
LOOP043_NEXT_GATE_OBS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop042_launch_next_gate_observation_lane.md"
)
LOOP044_PHASE_PROGRESS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-20_loop043_phase_progress_observation_synthesis.md"
)
LOOP044_PHASE_PROGRESS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-20_loop043_launch_phase_progress_observation_lane.md"
)
LOOP056_GATE_CORRIDOR_OBS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop056_gate_corridor_obstacle_observation_synthesis.md"
)
LOOP056_GATE_CORRIDOR_OBS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop056_launch_gate_corridor_obstacle_observation_lane.md"
)
LOOP052_BEST_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/"
    "level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt"
)
LOOP058_LOW_ENTROPY_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop058_low_entropy_exploitation_synthesis.md"
)
LOOP058_LOW_ENTROPY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop058_launch_low_entropy_exploitation_from_loop052.md"
)
LOOP059_GATE_APERTURE_MARGIN_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop059_gate_aperture_margin_observation_synthesis.md"
)
LOOP059_GATE_APERTURE_MARGIN_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop059_launch_gate_aperture_margin_observation_lane.md"
)
LOOP060_HIDDEN512_CAPACITY_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop060_hidden512_capacity_synthesis.md"
)
LOOP060_HIDDEN512_CAPACITY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop060_launch_hidden512_capacity_lane.md"
)
LOOP061_RECURRENT_ACTOR_GRU_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_recurrent_actor_gru256_strategy.md"
)
LOOP061_RECURRENT_ACTOR_GRU_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_launch_recurrent_actor_gru256_lane.md"
)
LOOP062_MLP_CONSTANT_LR_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop062_mlp_constant_lr_update_pressure.md"
)
LOOP062_MLP_CONSTANT_LR_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop062_reject_gru_launch_mlp_constant_lr.md"
)
LOOP064_GATE_ACQUISITION_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop064_gate_acquisition_reward_numbers.md"
)
LOOP064_GATE_ACQUISITION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop064_reject_v12_launch_gate_acquisition_reward_numbers.md"
)
LOOP065_DIRECTIONAL_PASS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop065_directional_pass_conversion_guard.md"
)
LOOP065_DIRECTIONAL_PASS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop065_reject_v13_launch_directional_pass_conversion_guard.md"
)
LOOP066_TRACE_AXIS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/2026-06-21_loop066_trace_axis_synthesis.md"
)
LOOP066_SENSOR15_CURRICULUM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop066_launch_sensor15_curriculum_from_loop052.md"
)
LOOP067_SENSOR15_CURRICULUM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/2026-06-21_loop067_continue_sensor15_curriculum_to_60m.md"
)
LOOP068_TARGETED_GEOMETRY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-21_loop068_launch_first_gate_hard_corridor_sampler.md"
)
LOOP069_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-21_loop069_continue_first_gate_hard_corridor_sampler_to_60m.md"
)
LOOP070_V17_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-21_loop070_reject_v16_launch_trace_mixed_corridor_sampler.md"
)
LOOP071_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-21_loop071_continue_trace_mixed_corridor_to_60m.md"
)
LOOP072_TRACE_SEED_REPLAY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-21_loop072_reject_v17_maturation_prepare_trace_seed_replay.md"
)
LOOP073_LOWPROB_REPLAY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop073_reject_v18_launch_lowprob_replay_success_retention.md"
)
LOOP074_V19_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop074_continue_v19_lowprob_replay_to_60m.md"
)
LOOP075_TRACE_DIAGNOSTIC_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop075_v19_trace_diagnostic_synthesis.md"
)
LOOP075_V20_DEFAULT_RECOVERY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop075_trace_diagnostic_launch_v20_default_recovery.md"
)
LOOP076_V21_GATE_ACQUISITION_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/research/"
    "2026-06-22_loop076_v21_gate_acquisition_reward_synthesis.md"
)
LOOP076_V21_GATE_ACQUISITION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop076_launch_v21_gate_acquisition_reward_from_loop071.md"
)
LOOP077_V22_GATE_CORRIDOR_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop077_v21_trace_diagnostic_synthesis.md"
)
LOOP077_V22_GATE_CORRIDOR_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop077_launch_v22_gate_corridor_obs_from_loop071.md"
)
LOOP078_V22_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop078_continue_v22_gate_corridor_obs_to_60m.md"
)
LOOP078_ANALYSIS_PACKET = (
    "experiments/level3_ppo_loop/analysis/"
    "level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_analysis.md"
)
LOOP079_V23_FRAME_OBSTACLE_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop079_v22_maturation_regression_synthesis.md"
)
LOOP079_V23_FRAME_OBSTACLE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop079_trace_diagnostic_launch_v23_frame_obstacle_retention.md"
)
LOOP080_V24_HYBRID_OBS_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop080_v24_hybrid_aperture_corridor_synthesis.md"
)
LOOP080_V24_HYBRID_OBS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop080_reject_v23_launch_v24_hybrid_aperture_corridor_obs.md"
)
LOOP081_V25_MINIMAL_APERTURE_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop081_v25_minimal_aperture_ablation_synthesis.md"
)
LOOP081_V25_MINIMAL_APERTURE_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop081_reject_v24_launch_v25_minimal_aperture_ablation_obs.md"
)
LOOP082_V26_SUCCESS_REPLAY_SYNTHESIS_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_loop082_v26_v23_10m_success_replay_retention_synthesis.md"
)
LOOP082_V26_SUCCESS_REPLAY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop082_launch_v26_v23_10m_success_replay_retention.md"
)
LOOP083_V26_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop083_continue_v26_success_replay_maturation_to_60m.md"
)
LOOP067_10M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m/"
    "level3_loop_067_structural_v15_loop052_sensor15_curriculum_nominal_reward_20m_step_010000000.ckpt"
)
LOOP069_25M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/"
    "level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt"
)
LOOP071_20M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m/"
    "level3_loop_071_structural_v17_trace_mixed_corridor_from_loop069_25m_30m_step_020000000.ckpt"
)
LOOP074_20M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m/"
    "level3_loop_074_structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m_step_020000000.ckpt"
)
LOOP078_FINAL_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m/"
    "level3_loop_078_structural_v22_loop071_gate_corridor_obstacle_obs_default_20m_final.ckpt"
)
LOOP087_FINAL_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_087_structural_v27_teacher_retention_beta010_5m/"
    "level3_loop_087_structural_v27_teacher_retention_beta010_5m_final.ckpt"
)
LOOP088_4M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_088_structural_v28_success24_retention_bounds_replay_5m/"
    "level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt"
)
LOOP089_2M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m/"
    "level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_step_002000000.ckpt"
)
LOOP080_V23_10M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m/"
    "level3_loop_080_structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m_step_010000000.ckpt"
)
LOOP083_V26_15M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_083_structural_v26_v23_10m_success_replay_retention_20m/"
    "level3_loop_083_structural_v26_v23_10m_success_replay_retention_20m_step_015000000.ckpt"
)
V27_TEACHER_RETENTION_SPEC_PACKET = (
    "experiments/level3_ppo_loop/research/"
    "2026-06-22_v27_teacher_anchored_failure_correction_spec.md"
)
V27_EVAL_PROTOCOL_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_eval_protocol_closed_next_v27_implementation.md"
)
V27_BETA0_CONTROL_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v27_beta0_control_5m.md"
)
V27_BETA003_TEACHER_KL_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v27_beta003_teacher_kl_5m.md"
)
V27_RETENTION_DATASET_PATH = (
    "experiments/level3_ppo_loop/retention_datasets/"
    "v27_loop052_train_pool_success_v5_teacher_v8_student.npz"
)
V28_SUCCESS24_RETENTION_DATASET_PATH = (
    "experiments/level3_ppo_loop/retention_datasets/"
    "v27_loop052_train_pool_success24_v5_teacher_v8_student.npz"
)
V28_FAILURE_TRAJECTORY_DATASET_PATH = (
    "experiments/level3_ppo_loop/failure_datasets/"
    "v28_loop087_train_pool_selected_bounds_failure_trajectories.npz"
)
V28_RETENTION_DATA_AUDIT_PACKET = (
    "experiments/level3_ppo_loop/research/"
    "2026-06-22_v27_retention_data_audit_success24.md"
)
V28_SUCCESS24_BOUNDS_REPLAY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v28_success24_retention_bounds_replay_5m.md"
)
V29_TRAIN_POOL_SUCCESS_CHURN_PACKET = (
    "experiments/level3_ppo_loop/diagnostics/"
    "2026-06-22_v29_train_pool_success_churn_probe.md"
)
V29_REVERT_REWARD_SUCCESS_CHURN_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v29_revert_reward_success_churn_replay_5m.md"
)
V30_SEMANTICS_AUDIT_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_v30_semantics_audit_approved.md"
)
V30_CORRECTED_SEMANTICS_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v30_end_to_end_ppo_corrected_action_and_episode_semantics.md"
)
LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET = (
    "experiments/level3_ppo_loop/research/"
    "2026-06-22_level3_framework_structural_training_plan.md"
)
V31A_LONGER_ROLLOUT_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_launch_v31a_longer_rollout_clean_ppo.md"
)
V31B_OBS_RETURN_NORM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop094_launch_v31b_obs_return_norm.md"
)
LOOP094_BEST_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/"
    "level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt"
)
V31C_IDENTITY_NORM_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_094_v31a_4m_identity_norm_warmstart/"
    "level3_loop_094_v31a_4m_identity_norm_warmstart.ckpt"
)
V31C_IDENTITY_NORM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop095_reject_v31b_launch_v31c_identity_norm_warmstart.md"
)
V31D_V31A_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop096_reject_v31c_continue_v31a_maturation.md"
)
LOOP097_BEST_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/"
    "level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt"
)
V31D_TO_30M_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop097_continue_v31d_to_30m.md"
)
V32_PRIVILEGED_CRITIC_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-22_loop098_reject_v31d_launch_v32_privileged_critic_support.md"
)
LOOP099_V32_BEST_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m/"
    "level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_step_003000000.ckpt"
)
V32_MATURATION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop099_continue_v32_privileged_critic_maturation.md"
)
V33_GATE_PHASE_RESET_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop100_reject_v32_launch_v33_gate_phase_reset_curriculum.md"
)
LOOP101_V33_BEST_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/"
    "level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt"
)
V34_TRAIN_POOL_PLR_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop101_reject_v33_launch_v34_train_pool_plr.md"
)
V35_COMPETENCE_GATED_CURRICULUM_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop102_reject_v34_launch_v35_competence_gated_curriculum.md"
)
V36_ONLINE_LEVEL_REPLAY_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop103_reject_v35_launch_v36_online_level_replay.md"
)
V37_GRU_TRANSFER_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop106_reject_v36_prepare_v37_gru_transfer.md"
)
V37_GRU_TRANSFER_PREFLIGHT_PACKET = (
    "experiments/level3_ppo_loop/parity/"
    "2026-06-23_v37_residual_gru_transfer_preflight.md"
)
V37B_LOOP107_1M_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop107_continue_v37b_from_1m.md"
)
V38_RETENTION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop108_reject_plain_v37_prepare_v38_retention.md"
)
V39_GATE_ACQUISITION_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop109_reject_v38_launch_v39_gate_acquisition.md"
)
V39B_LOOP110_3M_DECISION_PACKET = (
    "experiments/level3_ppo_loop/decisions/"
    "2026-06-23_loop110_continue_v39b_from_3m.md"
)
LOOP107_V37_1M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/"
    "level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt"
)
LOOP110_V39_3M_CHECKPOINT = (
    "lsy_drone_racing/control/checkpoints/"
    "level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/"
    "level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt"
)
SUPPORTED_TRAINING_STRUCTURES = {
    "mlp_2x_tanh",
    "recurrent_actor_gru256",
    "teacher_retention_kl",
    "v30_episode_semantics",
    "observation_return_normalization_support",
    "asymmetric_privileged_critic_support",
    "gate_phase_reset_curriculum_support",
    "offline_train_pool_plr_support",
    "competence_gated_gate_phase_curriculum_support",
    "online_competence_gated_level_replay_support",
    "mlp_to_gru_transfer_support",
    "residual_gru_teacher_retention_support",
}
MIN_MEAN_GATES_IMPROVEMENT = 0.05
DEFAULT_PLATEAU_TRIAL_LIMIT = 2
DEFAULT_ESCALATION_MIN_EVALUATED_TRIALS = 6
DEFAULT_ESCALATION_MIN_DISTINCT_REWARD_HYPOTHESES = 4
DEFAULT_ESCALATION_MIN_TOTAL_TIMESTEPS = 120_000_000
DEFAULT_ESCALATION_MIN_PLATEAU_TRIALS = 4
POST_RUN_REVIEW_ROLES = [
    "evaluator_metrics",
    "wandb_ppo_diagnostics",
    "structure_research_synthesis",
]
POST_RUN_DECISION_OPTIONS = [
    "stop_target_met",
    "hold_for_more_analysis",
    "continue_same_hypothesis",
    "change_reward_or_training_numbers",
    "launch_named_structural_lane",
]
POST_RUN_TRAINING_DECISION_OPTIONS = {
    "continue_same_hypothesis",
    "change_reward_or_training_numbers",
    "launch_named_structural_lane",
}
POST_RUN_DECISION_PROTOCOL: dict[str, Any] = {
    "required": True,
    "required_review_roles": POST_RUN_REVIEW_ROLES,
    "allowed_decisions": POST_RUN_DECISION_OPTIONS,
    "decision_packet_dir": "experiments/level3_ppo_loop/decisions",
    "requires_main_agent_packet_before_next_training": True,
    "hard_eval_config": f"config/{TARGET_EVAL_CONFIG}",
    "do_not_modify_level3_track": True,
}
DEFAULT_AUTONOMY_POLICY: dict[str, Any] = {
    "mode": "codex_supervised_unattended",
    "standing_user_authorization": True,
    "may_spawn_analysis_subagents": True,
    "may_spawn_research_subagents": True,
    "may_use_source_backed_external_research": True,
    "may_choose_reward_only_next_run_without_per_run_user_confirmation": True,
    "may_choose_structural_next_run_without_per_run_user_confirmation": True,
    "reward_only_first": False,
    "structural_changes_stage": "active_structural_search",
    "structural_changes_require_detailed_escalation_packet": False,
    "immutable_target_eval_config": f"config/{TARGET_EVAL_CONFIG}",
    "domain_randomized_train_config": f"config/{DOMAIN_RANDOMIZED_TRAIN_CONFIG}",
    "do_not_modify_level3_track": True,
    "approved_structural_observation_screen": (
        "Observation-layout experiments are open. Keep each structural lane "
        f"named, source-backed, and hard-evaluated on config/{TARGET_EVAL_CONFIG}."
    ),
    "must_run_post_iteration_analysis": True,
    "post_run_multi_agent_decision_required": True,
    "required_post_run_review_roles": POST_RUN_REVIEW_ROLES,
    "allowed_post_run_decisions": POST_RUN_DECISION_OPTIONS,
    "main_agent_decision_packet_required_before_next_training": True,
    "step_curve_policy": {
        "source": LEVEL2_STEP_CURVE_PACKET,
        "screening_timesteps": SCREENING_TIMESTEPS,
        "maturation_timesteps": MATURATION_TIMESTEPS,
        "confirmation_timesteps": CONFIRMATION_TIMESTEPS,
        "rule": (
            "Treat 30M as a screening/debug chunk. If a branch has non-zero "
            "hard-eval success or meaningful gate progress, mature the same "
            "hypothesis to 60M-90M before rejecting it. Always select among "
            "intermediate checkpoints; final is not assumed best."
        ),
    },
    "escalation_min_evaluated_reward_trials": DEFAULT_ESCALATION_MIN_EVALUATED_TRIALS,
    "escalation_min_distinct_reward_hypotheses": (
        DEFAULT_ESCALATION_MIN_DISTINCT_REWARD_HYPOTHESES
    ),
    "escalation_min_total_timesteps": DEFAULT_ESCALATION_MIN_TOTAL_TIMESTEPS,
    "escalation_min_plateau_trials": DEFAULT_ESCALATION_MIN_PLATEAU_TRIALS,
    "script_boundary": (
        "The Python orchestrator runs train/evaluate chunks. The supervising "
        "Codex main agent owns subagent analysis, research synthesis, and the "
        "next structural or reward decision between script invocations."
    ),
    "framework_structural_plan_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
    "framework_stage_priority": [
        "ppo_correctness_and_semantics",
        "clean_feedforward_baseline_with_longer_rollout",
        "observation_return_normalization_support",
        "asymmetric_privileged_critic",
        "gate_phase_reset_curriculum",
        "prioritized_level_replay",
        "recurrent_actor_gru256_after_reset_semantics",
        "reward_numbers",
        "speed_optimization_after_success_near_50_percent",
    ],
    "reward_scope": (
        "structural search is allowed; do not change level3 track geometry "
        f"or accept any metric outside hard eval on config/{TARGET_EVAL_CONFIG}"
    ),
}

BASE_PARAMS: dict[str, Any] = {
    "seed": 42,
    "learning_rate": 3e-4,
    "anneal_lr": True,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "update_epochs": 5,
    "num_minibatches": 8,
    "clip_coef": 0.26,
    "clip_vloss": True,
    "ent_coef": 0.02,
    "vf_coef": 0.7,
    "max_grad_norm": 1.5,
    "target_kl": 0.03,
    "hidden_dim": 256,
    "policy_arch": "mlp_2x_tanh",
    "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
    "recurrent_hidden_dim": 256,
    "recurrent_sequence_len": 32,
    "n_obs": 2,
    "action_rp_limit_deg": 90.0,
    "action_lowpass_alpha": 1.0,
    "reward_structure": "legacy_staged",
    "track_generator_profile": "default",
    "online_level_replay_profile": "none",
    "online_level_replay_prob": 0.0,
    "online_level_replay_competence_enabled": False,
    "online_level_replay_competence_start_prob": 0.03,
    "online_level_replay_competence_step_prob": 0.01,
    "online_level_replay_competence_min_passed_gate_rate": 0.0065,
    "online_level_replay_competence_min_finished_rate": 0.0005,
    "online_level_replay_competence_max_crashed_rate": 0.0082,
    "gate_phase_reset_prob": 0.0,
    "gate_phase_reset_x_min": -1.05,
    "gate_phase_reset_x_max": -0.18,
    "gate_phase_reset_yz_max": 0.16,
    "gate_phase_reset_speed_min": 0.15,
    "gate_phase_reset_speed_max": 1.20,
    "gate_phase_reset_competence_enabled": False,
    "gate_phase_reset_competence_start_prob": 0.12,
    "gate_phase_reset_competence_step_prob": 0.02,
    "gate_phase_reset_competence_min_passed_gate_rate": 0.0068,
    "gate_phase_reset_competence_min_finished_rate": 0.0007,
    "gate_phase_reset_competence_max_crashed_rate": 0.0082,
    "obs_norm_enabled": False,
    "obs_norm_clip": 10.0,
    "return_norm_enabled": False,
    "return_norm_clip": 10.0,
    "progress_coef": 0.0,
    "gate_stage_coef": 10.0,
    "gate_axis_coef": 20.0,
    "near_gate_coef": 0.0,
    "gate_bonus": 180.0,
    "gate_front_bonus": 4.0,
    "gate_plane_bonus": 0.0,
    "gate_back_bonus": 30.0,
    "finish_bonus": 160.0,
    "missed_gate_penalty": 0.0,
    "gate_frame_pressure_coef": 0.0,
    "wrong_side_penalty": 6.0,
    "crash_penalty": 50.0,
    "obstacle_coef": 5.0,
    "obstacle_margin": 0.2,
    "obstacle_clearance_coef": 0.0,
    "timeout_penalty": 80.0,
    "time_penalty": 0.03,
    "act_coef": 0.015,
    "d_act_th_coef": 0.07,
    "d_act_xy_coef": 0.07,
    "cmd_tilt_coef": 0.7,
    "rpy_coef": 0.7,
    "tilt_limit_deg": 40.0,
    "tilt_excess_coef": 12.0,
}

LOOP052_REMOTE_NOMINAL_PARAMS: dict[str, Any] = {
    **BASE_PARAMS,
    "seed": 42,
    "learning_rate": 5e-5,
    "anneal_lr": True,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "update_epochs": 5,
    "num_minibatches": 8,
    "clip_coef": 0.26,
    "clip_vloss": True,
    "ent_coef": 0.02,
    "vf_coef": 0.7,
    "max_grad_norm": 1.5,
    "target_kl": 0.03,
    "hidden_dim": 256,
    "policy_arch": "mlp_2x_tanh",
    "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
    "recurrent_hidden_dim": 256,
    "recurrent_sequence_len": 32,
    "n_obs": 2,
    "action_rp_limit_deg": 90.0,
    "action_lowpass_alpha": 1.0,
    "reward_structure": "legacy_staged",
    "track_generator_profile": "default",
    "v27_teacher_kl_beta": 0.0,
    "progress_coef": 0.0,
    "gate_stage_coef": 10.0,
    "gate_axis_coef": 12.0,
    "near_gate_coef": 0.0,
    "gate_bonus": 90.0,
    "gate_front_bonus": 0.0,
    "gate_plane_bonus": 0.0,
    "gate_back_bonus": 12.0,
    "finish_bonus": 160.0,
    "missed_gate_penalty": 0.0,
    "gate_frame_pressure_coef": 0.0,
    "wrong_side_penalty": 8.0,
    "crash_penalty": 100.0,
    "obstacle_coef": 8.0,
    "obstacle_margin": 0.4,
    "obstacle_clearance_coef": 6.0,
    "timeout_penalty": 80.0,
    "time_penalty": 0.03,
    "act_coef": 0.03,
    "d_act_th_coef": 0.10,
    "d_act_xy_coef": 0.10,
    "cmd_tilt_coef": 1.0,
    "rpy_coef": 1.0,
    "tilt_limit_deg": 40.0,
    "tilt_excess_coef": 15.0,
}

PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "gate_stage_coef": (4.0, 28.0),
    "gate_axis_coef": (6.0, 40.0),
    "gate_bonus": (80.0, 260.0),
    "gate_front_bonus": (0.0, 80.0),
    "gate_back_bonus": (10.0, 80.0),
    "finish_bonus": (80.0, 260.0),
    "wrong_side_penalty": (3.0, 16.0),
    "gate_frame_pressure_coef": (0.0, 8.0),
    "crash_penalty": (35.0, 120.0),
    "obstacle_coef": (1.0, 12.0),
    "obstacle_margin": (0.15, 0.45),
    "timeout_penalty": (20.0, 140.0),
    "time_penalty": (0.0, 0.12),
    "act_coef": (0.003, 0.04),
    "d_act_th_coef": (0.02, 0.18),
    "d_act_xy_coef": (0.02, 0.18),
    "cmd_tilt_coef": (0.3, 1.6),
    "rpy_coef": (0.3, 1.6),
    "tilt_limit_deg": (28.0, 45.0),
    "tilt_excess_coef": (6.0, 24.0),
    "action_rp_limit_deg": (45.0, 90.0),
    "action_lowpass_alpha": (0.2, 1.0),
    "clip_coef": (0.10, 0.50),
    "vf_coef": (0.20, 1.20),
    "max_grad_norm": (0.30, 3.00),
}

BOOL_PARAM_KEYS = {
    "anneal_lr",
    "clip_vloss",
    "obs_norm_enabled",
    "return_norm_enabled",
    "online_level_replay_competence_enabled",
    "gate_phase_reset_competence_enabled",
}
REWARD_STRUCTURE_CHOICES = {
    "legacy_staged",
    "gate_potential",
    "legacy_frame_clearance",
    "decoupled_frame_clearance",
    "direct_aperture",
    "soft_centerline_followthrough",
}
TRACK_GENERATOR_PROFILE_CHOICES = {
    "default",
    "first_gate_hard_corridor",
    "loop078_v23_success_replay_lowprob",
    "trace_seed_replay_default_retention",
    "trace_seed_replay_lowprob_success_retention",
    "trace_mixed_corridor",
    "v28_train_pool_bounds_failure_replay",
    "v29_train_pool_success_churn_replay",
    "v34_lowprob_train_pool_bounds_plr",
}
ONLINE_LEVEL_REPLAY_PROFILE_CHOICES = {
    "none",
    "v36_train_pool_bounds_gate0_gate2",
}
STRING_PARAM_CHOICES = {
    "critic_observation_mode": CRITIC_OBSERVATION_MODE_CHOICES,
    "reward_structure": REWARD_STRUCTURE_CHOICES,
    "track_generator_profile": TRACK_GENERATOR_PROFILE_CHOICES,
    "online_level_replay_profile": ONLINE_LEVEL_REPLAY_PROFILE_CHOICES,
}
STRING_PARAM_KEYS = set(STRING_PARAM_CHOICES)

RELAXED_PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "gate_stage_coef": (2.0, 40.0),
    "gate_axis_coef": (4.0, 60.0),
    "gate_bonus": (50.0, 360.0),
    "gate_front_bonus": (0.0, 140.0),
    "gate_back_bonus": (5.0, 140.0),
    "finish_bonus": (50.0, 380.0),
    "wrong_side_penalty": (0.0, 32.0),
    "gate_frame_pressure_coef": (0.0, 20.0),
    "crash_penalty": (20.0, 180.0),
    "obstacle_coef": (0.5, 20.0),
    "obstacle_margin": (0.10, 0.65),
    "timeout_penalty": (10.0, 220.0),
    "time_penalty": (0.0, 0.20),
    "act_coef": (0.001, 0.08),
    "d_act_th_coef": (0.01, 0.30),
    "d_act_xy_coef": (0.01, 0.30),
    "cmd_tilt_coef": (0.15, 2.50),
    "rpy_coef": (0.15, 2.50),
    "tilt_limit_deg": (24.0, 50.0),
    "tilt_excess_coef": (3.0, 40.0),
    "action_rp_limit_deg": (30.0, 90.0),
    "action_lowpass_alpha": (0.1, 1.0),
    "clip_coef": (0.05, 0.80),
    "vf_coef": (0.10, 1.50),
    "max_grad_norm": (0.20, 5.00),
}

AUTO_REWARD_HYPOTHESES: list[dict[str, Any]] = [
    {
        "name": "auto_precision_low_pressure",
        "params": {
            "gate_stage_coef": 12.0,
            "gate_axis_coef": 26.0,
            "gate_front_bonus": 18.0,
            "gate_bonus": 210.0,
            "gate_back_bonus": 55.0,
            "finish_bonus": 220.0,
            "wrong_side_penalty": 12.0,
            "crash_penalty": 45.0,
            "obstacle_coef": 4.5,
            "time_penalty": 0.0,
            "act_coef": 0.012,
            "d_act_xy_coef": 0.06,
            "d_act_th_coef": 0.06,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "Reset away from the gate+safety escalation loop: low speed pressure, "
            "larger front/back completion events, and moderate safety."
        ),
    },
    {
        "name": "auto_completion_backloaded",
        "params": {
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "gate_front_bonus": 22.0,
            "gate_bonus": 180.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_xy_coef": 0.055,
            "d_act_th_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "Make completed gate traversal much more valuable than partial shaped "
            "progress, while keeping speed pressure almost off."
        ),
    },
    {
        "name": "auto_stability_first",
        "params": {
            "gate_stage_coef": 7.0,
            "gate_axis_coef": 16.0,
            "gate_front_bonus": 6.0,
            "gate_bonus": 135.0,
            "gate_back_bonus": 25.0,
            "finish_bonus": 150.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 105.0,
            "obstacle_coef": 10.0,
            "time_penalty": 0.0,
            "act_coef": 0.03,
            "d_act_xy_coef": 0.14,
            "d_act_th_coef": 0.14,
            "cmd_tilt_coef": 1.35,
            "rpy_coef": 1.20,
            "tilt_limit_deg": 35.0,
            "tilt_excess_coef": 22.0,
        },
        "rationale": (
            "If every evaluator episode crashes, first test whether a calmer policy "
            "can survive long enough for gate reward to matter."
        ),
    },
    {
        "name": "auto_axis_aggressive",
        "params": {
            "gate_stage_coef": 22.0,
            "gate_axis_coef": 48.0,
            "gate_front_bonus": 8.0,
            "gate_bonus": 300.0,
            "gate_back_bonus": 45.0,
            "finish_bonus": 220.0,
            "wrong_side_penalty": 6.0,
            "crash_penalty": 40.0,
            "obstacle_coef": 3.0,
            "time_penalty": 0.0,
            "act_coef": 0.008,
            "d_act_xy_coef": 0.045,
            "d_act_th_coef": 0.045,
            "cmd_tilt_coef": 0.55,
            "rpy_coef": 0.50,
            "tilt_limit_deg": 45.0,
            "tilt_excess_coef": 8.0,
        },
        "rationale": (
            "Temporarily privilege axis alignment and gate acquisition to test "
            "whether the policy is under-incentivized to approach the first gate."
        ),
    },
]

STRUCTURAL_HYPOTHESES: dict[str, dict[str, Any]] = {
    "v5_localobs_remote_reward": {
        "name": "v5_localobs_remote_reward",
        "proposal_name": "structural_v5_localobs_remote_reward_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": True,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "progress_coef": 0.0,
            "gate_stage_coef": 15.0,
            "gate_axis_coef": 15.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 120.0,
            "gate_front_bonus": 4.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 20.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 6.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 5.0,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Remote stateirving hard eval showed the local-obstacle v5 layout "
            "outperforming the current original-observation best, while v4/all-gates "
            "remained weak. Start with the remote 300M recipe as a 30M screening "
            "branch on the unchanged level3_dr target."
        ),
    },
    "v5_localobs_action_envelope_60deg": {
        "name": "v5_localobs_action_envelope_60deg",
        "proposal_name": "structural_v5_localobs_action_envelope_60deg_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 60.0,
            "action_lowpass_alpha": 1.0,
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "Loop020 produced the best local v5 hard-eval progress but relied on "
            "high roll/pitch command saturation. Train and hard-evaluate a matched "
            "60-degree roll/pitch action envelope, while keeping level3_dr.toml, "
            "v5 observations, PPO structure, and loop020 completion-backloaded "
            "reward numbers fixed."
        ),
    },
    "v5_localobs_action_envelope_75deg": {
        "name": "v5_localobs_action_envelope_75deg",
        "proposal_name": "structural_v5_localobs_action_envelope_75deg_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 75.0,
            "action_lowpass_alpha": 1.0,
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "The 60-degree envelope reduced command tilt but over-constrained "
            "gate acquisition. Test a less restrictive 75-degree matched "
            "roll/pitch action envelope from the loop020 global-best checkpoint, "
            "while keeping level3_dr.toml, v5 observations, PPO structure, and "
            "loop020 completion-backloaded reward numbers fixed."
        ),
    },
    "v5_localobs_action_lowpass_90deg": {
        "name": "v5_localobs_action_lowpass_90deg",
        "proposal_name": "structural_v5_localobs_action_lowpass_90deg_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 0.35,
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "The 60-degree and 75-degree action-envelope ablations reduced useful "
            "authority and regressed hard-eval gate progress. Keep the full "
            "90-degree roll/pitch envelope but apply checkpointed normalized-action "
            "low-pass filtering before reward and simulator stepping, preserving "
            "train/eval parity and loop020 reward/PPO settings."
        ),
    },
    "v5_localobs_gate_potential_30m": {
        "name": "v5_localobs_gate_potential_30m",
        "proposal_name": "structural_v5_localobs_gate_potential_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "gate_potential",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 14.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 160.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 0.0,
            "finish_bonus": 200.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 10.0,
            "crash_penalty": 60.0,
            "obstacle_coef": 5.0,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.02,
            "act_coef": 0.015,
            "d_act_th_coef": 0.08,
            "d_act_xy_coef": 0.08,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 0.8,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Loop027 regressed while increasing direct gate bonuses and showed "
            "command-tilt saturation without gate conversion. Replace the "
            "overlapping dense gate rewards with a gate-coordinate potential "
            "term gamma*phi(s')-phi(s), while keeping true gate pass, finish, "
            "crash, obstacle, time, and smoothness terms explicit. The Level3 "
            "track remains unchanged and hard eval stays on level3_dr.toml."
        ),
    },
    "v5_localobs_gate_potential_pass_conversion_30m": {
        "name": "v5_localobs_gate_potential_pass_conversion_30m",
        "proposal_name": "structural_v5_localobs_gate_potential_pass_conversion_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": STATEIRVING_LEVEL3_PACKET,
        "approved_hypothesis_packet": STRUCTURAL_SEARCH_APPROVAL_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "gate_potential",
            "progress_coef": 0.0,
            "gate_stage_coef": 7.0,
            "gate_axis_coef": 10.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 260.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 0.0,
            "finish_bonus": 320.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 12.0,
            "crash_penalty": 60.0,
            "obstacle_coef": 5.0,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.015,
            "act_coef": 0.012,
            "d_act_th_coef": 0.06,
            "d_act_xy_coef": 0.06,
            "cmd_tilt_coef": 0.9,
            "rpy_coef": 0.7,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 13.0,
        },
        "rationale": (
            "Loop029 showed the gate-potential lane learning approach proxies "
            "without converting them into hard-eval gate passes: success fell "
            "to zero and mean gates decayed after the 30M checkpoint. Keep the "
            "v5 observation, controller, PPO settings, and gate-potential "
            "reward structure fixed, but reduce dense potential weight and "
            "increase true gate-pass/finish rewards to test pass conversion "
            "from the loop028 25M checkpoint. The Level3 track remains "
            "unchanged and hard eval stays on level3_dr.toml."
        ),
    },
    "v5_curriculum_gate_obstacle_staged_training": {
        "name": "v5_curriculum_gate_obstacle_staged_training",
        "proposal_name": "structural_v5_curriculum_gate_obstacle_staged_training_30m",
        "config": "level3_dr_stage2_no_train_wrappers.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LEGACY_CENTERLINE_SAFETY_PACKET,
        "approved_hypothesis_packet": LOOP031_CURRICULUM_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "Loop031 regressed from the loop020 v5 global-best checkpoint while "
            "trying another reward-number repair on the full train-only robustness "
            "stack. Test a named curriculum lane that keeps v5 observations, the "
            "loop020 completion-backloaded reward/PPO settings, and hard eval on "
            "level3_dr.toml, but trains one 30M chunk on the existing "
            "level3_dr_stage2_no_train_wrappers.toml training-only config to reduce "
            "latency/noise/thrust wrapper pressure while checking whether gate-pass "
            "and obstacle-avoidance conversion improves."
        ),
    },
    "v5_ppo_pressure_entropy_saturation_guard": {
        "name": "v5_ppo_pressure_entropy_saturation_guard",
        "proposal_name": "structural_v5_ppo_pressure_entropy_saturation_guard_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP032_SATURATION_DIAGNOSIS_PACKET,
        "approved_hypothesis_packet": LOOP032_PPO_UPDATE_DECISION_PACKET,
        "params": {
            "learning_rate": 4e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 6,
            "num_minibatches": 8,
            "ent_coef": 0.01,
            "target_kl": 0.04,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop032 and earlier v5 branches show low KL, near-zero clip "
            "fraction, tiny policy loss, high entropy, and worsening command "
            "saturation while gate-stage proxies fail to convert into true "
            "passes. Keep the loop020 reward scale, v5 observation, and hard "
            "Level3 track fixed, but run a bounded training-structure screen "
            "from the loop020 checkpoint with slightly higher learning rate, "
            "more PPO update epochs, lower entropy pressure, and a higher KL "
            "guard to test whether effective policy movement improves gate-pass "
            "conversion without changing the track or reward numbers."
        ),
    },
    "v5_mild_lowpass_pass_conversion_controller": {
        "name": "v5_mild_lowpass_pass_conversion_controller",
        "proposal_name": "structural_v5_mild_lowpass_pass_conversion_controller_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP032_SATURATION_DIAGNOSIS_PACKET,
        "approved_hypothesis_packet": LOOP033_MILD_LOWPASS_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 0.65,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop033 proved that lower entropy and stronger PPO pressure can "
            "reduce command saturation but did not preserve gate-pass conversion. "
            "loop025 showed that a strong low-pass alpha of 0.35 was too "
            "restrictive. Test a milder checkpointed controller low-pass of "
            "0.65 from the loop020 global-best checkpoint, keeping loop020 reward "
            "numbers, PPO settings, v5 observation, full 90-degree authority, and "
            "hard eval on the unchanged Level3 track fixed."
        ),
    },
    "v5_frame_clearance_pass_conversion_reward": {
        "name": "v5_frame_clearance_pass_conversion_reward",
        "proposal_name": "structural_v5_frame_clearance_pass_conversion_reward_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP034_FRAME_CLEARANCE_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP034_FRAME_CLEARANCE_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_frame_clearance",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 35.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 18.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 6.0,
            "obstacle_margin": 0.35,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop027 reward rebalance, loop033 PPO pressure, and loop034 "
            "controller low-pass all failed to beat loop020. The 40-seed crash "
            "taxonomy shows early crashes around gate frames and nearby "
            "obstacles. Keep loop020's v5 observation, action authority, PPO "
            "settings, and completion-backloaded event rewards, but switch to "
            "a legacy_frame_clearance reward structure that adds a centered "
            "gate-plane crossing bonus and a near-plane frame-clearance penalty "
            "before collision. Hard eval remains on the unchanged Level3 track."
        ),
    },
    "v5_decoupled_frame_clearance_low_pressure_reward": {
        "name": "v5_decoupled_frame_clearance_low_pressure_reward",
        "proposal_name": "structural_v5_decoupled_frame_clearance_low_pressure_reward_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP035_DECOUPLED_FRAME_CLEARANCE_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP035_DECOUPLED_FRAME_CLEARANCE_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "decoupled_frame_clearance",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 18.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 8.0,
            "gate_frame_pressure_coef": 1.5,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop035 proved that coupling dense near-plane frame pressure to "
            "missed_gate_penalty creates a large negative reward term, raises "
            "wrong-side approaches, and collapses gate-pass conversion. Keep "
            "the loop020 v5 observation, full action authority, PPO settings, "
            "and completion-backloaded event rewards, but use a decoupled "
            "frame-clearance reward structure with a small continuous frame "
            "pressure coefficient, discrete missed-gate penalty, restored "
            "loop020 obstacle settings, and unchanged hard eval on level3_dr.toml."
        ),
    },
    "v5_direct_aperture_crossing_pass_conversion": {
        "name": "v5_direct_aperture_crossing_pass_conversion",
        "proposal_name": "structural_v5_direct_aperture_crossing_pass_conversion_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP039_DIRECT_APERTURE_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP039_DIRECT_APERTURE_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "direct_aperture",
            "progress_coef": 0.0,
            "gate_stage_coef": 8.0,
            "gate_axis_coef": 18.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 240.0,
            "gate_front_bonus": 12.0,
            "gate_plane_bonus": 90.0,
            "gate_back_bonus": 105.0,
            "finish_bonus": 320.0,
            "missed_gate_penalty": 16.0,
            "gate_frame_pressure_coef": 2.0,
            "wrong_side_penalty": 18.0,
            "crash_penalty": 55.0,
            "obstacle_coef": 5.0,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 90.0,
            "time_penalty": 0.003,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop037 and loop038 show that frame-clearance pressure and small "
            "event-number retunes can restore some approach behavior but do not "
            "beat the loop020 hard-eval frontier. Keep the loop020 v5 "
            "observation, full action authority, PPO settings, and hard eval on "
            "the unchanged level3_dr.toml track, but switch to a direct_aperture "
            "reward structure that rewards centered gate-plane crossing and "
            "stage-valid gate pass events more directly while penalizing "
            "missed-plane and wrong-side approaches."
        ),
    },
    "v5_soft_centerline_followthrough_pass_conversion": {
        "name": "v5_soft_centerline_followthrough_pass_conversion",
        "proposal_name": "structural_v5_soft_centerline_followthrough_pass_conversion_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP040_SOFT_FOLLOWTHROUGH_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP040_SOFT_FOLLOWTHROUGH_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "soft_centerline_followthrough",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 190.0,
            "gate_front_bonus": 8.0,
            "gate_plane_bonus": 28.0,
            "gate_back_bonus": 85.0,
            "finish_bonus": 280.0,
            "missed_gate_penalty": 6.0,
            "gate_frame_pressure_coef": 0.5,
            "wrong_side_penalty": 12.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop039 direct-aperture made the pass target literal but too sparse "
            "and punitive: centered/pass hit rates collapsed while wrong-side "
            "and frame-pressure signals rose. Keep loop020's v5 observation, "
            "full action authority, PPO settings, normal passed-gate reward, "
            "and followthrough/back reward, but use a softer centerline-weighted "
            "axis progress term plus a modest centered plane-crossing bonus and "
            "small missed-plane/frame-pressure penalties. Hard eval remains on "
            "the unchanged level3_dr.toml track."
        ),
    },
    "v5_soft_centerline_saturation_guard_pass_conversion": {
        "name": "v5_soft_centerline_saturation_guard_pass_conversion",
        "proposal_name": "structural_v5_soft_centerline_saturation_guard_pass_conversion_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP042_SATURATION_GUARD_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP042_SATURATION_GUARD_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "ent_coef": 0.02,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 0.65,
            "reward_structure": "soft_centerline_followthrough",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 190.0,
            "gate_front_bonus": 8.0,
            "gate_plane_bonus": 28.0,
            "gate_back_bonus": 85.0,
            "finish_bonus": 280.0,
            "missed_gate_penalty": 6.0,
            "gate_frame_pressure_coef": 0.5,
            "wrong_side_penalty": 12.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop041 showed that stronger soft-centerline gate-acquisition "
            "numbers worsened hard eval and amplified command saturation: "
            "success fell, mean gates fell, and cmd-tilt over-limit rose. Keep "
            "the loop040 soft-centerline reward balance, v5 observation, PPO "
            "settings, and full 90-degree action authority, but add a mild "
            "controller low-pass alpha of 0.65 to test whether saturation "
            "guarding can preserve pass conversion while reducing crash-prone "
            "action spikes. Hard eval remains on the unchanged level3_dr.toml "
            "track."
        ),
    },
    "v6_next_gate_localobs_warmstart": {
        "name": "v6_next_gate_localobs_warmstart",
        "proposal_name": "structural_v6_next_gate_localobs_warmstart_from_loop020_30m",
        "observation_layout": LOCAL_NEXT_GATE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP043_NEXT_GATE_OBS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP043_NEXT_GATE_OBS_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop040-loop042 showed that v5 reward/controller tweaks reduce "
            "saturation or recover small non-zero success but do not convert "
            "passes beyond the loop020 frontier. The v5 observation gives the "
            "current gate plus the nearest non-target gate, which can be a "
            "geometric distractor on Level3. Keep the same 68-dimensional local "
            "observation family and loop020 reward/PPO frontier, but replace "
            "the second gate block with the race-order next gate. Warm-start "
            "from loop020 v5 weights because the input dimension is unchanged. "
            "Hard eval remains on the unchanged level3_dr.toml track."
        ),
    },
    "v7_explicit_phase_progress_localobs": {
        "name": "v7_explicit_phase_progress_localobs",
        "proposal_name": "structural_v7_explicit_phase_progress_localobs_from_loop020_30m",
        "observation_layout": LOCAL_PHASE_PROGRESS_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "research_packet": LOOP044_PHASE_PROGRESS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP044_PHASE_PROGRESS_DECISION_PACKET,
        "params": {
            "learning_rate": 3e-4,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 9.0,
            "gate_axis_coef": 22.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 180.0,
            "gate_front_bonus": 22.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 95.0,
            "finish_bonus": 300.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 50.0,
            "obstacle_coef": 4.5,
            "obstacle_margin": 0.3,
            "obstacle_clearance_coef": 0.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.005,
            "act_coef": 0.012,
            "d_act_th_coef": 0.055,
            "d_act_xy_coef": 0.055,
            "cmd_tilt_coef": 0.75,
            "rpy_coef": 0.65,
            "tilt_limit_deg": 42.0,
            "tilt_excess_coef": 10.0,
        },
        "rationale": (
            "loop043 showed that replacing v5's nearest-other gate with the "
            "race-order next gate did not beat loop020 and increased command "
            "saturation. The next structural test keeps the loop020 v5 local "
            "observation order intact and appends explicit race phase/progress "
            "features: target progress plus current gate-frame x/y/z. "
            "Warm-start from loop020 by zero-padding the appended input weights, "
            "so old behavior is preserved initially while the policy can learn "
            "the new phase/progress features. Hard eval remains on unchanged "
            "level3_dr.toml."
        ),
    },
    "v8_gate_corridor_obstacle_relative_obs_from_loop052": {
        "name": "v8_gate_corridor_obstacle_relative_obs_from_loop052",
        "proposal_name": "structural_v8_gate_corridor_obstacle_relative_obs_from_loop052_30m",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP056_GATE_CORRIDOR_OBS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP056_GATE_CORRIDOR_OBS_DECISION_PACKET,
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Loop053-loop056 falsified more nominal steps, mild gate pressure, "
            "PPO update pressure, and light soft-centerline shaping from the "
            "loop052 checkpoint. Keep loop052 reward/PPO/controller settings "
            "fixed, but append current-gate-frame progress and nearest-obstacle "
            "gate-corridor geometry to the v5 observation. Warm-start from "
            "loop052 by zero-padding appended input weights. Hard eval remains "
            "on unchanged level3_dr.toml."
        ),
    },
    "v5_loop052_low_entropy_exploitation": {
        "name": "v5_loop052_low_entropy_exploitation",
        "proposal_name": "structural_v5_loop052_low_entropy_exploitation_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP058_LOW_ENTROPY_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP058_LOW_ENTROPY_DECISION_PACKET,
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.005,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop058 rejected the v8 observation maturation, while loop052 "
            "remains the global-best hard-eval checkpoint. Keep loop052's v5 "
            "observation, reward numbers, controller settings, learning rate, "
            "update epochs, target KL, and network fixed, but reduce entropy "
            "pressure from 0.02 to 0.005 to test whether late fine-tuning can "
            "exploit the loop052 policy neighborhood. Hard eval remains on "
            "unchanged level3_dr.toml."
        ),
    },
    "v9_gate_aperture_margin_obs_from_loop052": {
        "name": "v9_gate_aperture_margin_obs_from_loop052",
        "proposal_name": "structural_v9_gate_aperture_margin_obs_from_loop052_30m",
        "observation_layout": LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP059_GATE_APERTURE_MARGIN_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP059_GATE_APERTURE_MARGIN_DECISION_PACKET,
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop059 rejected low-entropy exploitation and its crash taxonomy "
            "showed a concentrated right-side gate-frame failure mode. Keep "
            "loop052 reward/PPO/controller settings fixed, but append explicit "
            "current-gate aperture margin features to the v5 local observation. "
            "Warm-start from loop052 by zero-padding appended input weights. "
            "Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v10_hidden512_warmstart_capacity_from_loop052": {
        "name": "v10_hidden512_warmstart_capacity_from_loop052",
        "proposal_name": "structural_v10_hidden512_warmstart_capacity_from_loop052_30m",
        "observation_layout": LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "allow_hidden_dim_warmstart": True,
        "research_packet": LOOP060_HIDDEN512_CAPACITY_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP060_HIDDEN512_CAPACITY_DECISION_PACKET,
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 512,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop060 showed that appending explicit gate-aperture margin features "
            "did not beat loop052 with the existing 2x256 MLP. Test network "
            "capacity as a single named training-structure variable by keeping "
            "the v9 observation, reward scale, controller settings, PPO settings, "
            "and loop052 initialization fixed while widening the actor and critic "
            "2-layer Tanh MLP from hidden_dim=256 to hidden_dim=512 via explicit "
            "block-copy warm-start. Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v10_hidden512_reward_search_from_best": {
        "name": "v10_hidden512_reward_search_from_best",
        "proposal_name": "structural_v10_hidden512_reward_search_from_best_20m",
        "observation_layout": LOCAL_GATE_APERTURE_MARGIN_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "allow_hidden_dim_warmstart": False,
        "research_packet": LOOP060_HIDDEN512_CAPACITY_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP060_HIDDEN512_CAPACITY_DECISION_PACKET,
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 512,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Continue the hidden512/v9 capacity lane after its first screening "
            "run by selecting the best evaluated checkpoint with the same "
            "observation layout and hidden_dim=512, then allowing reward-number "
            "or bounded PPO/reward hyperparameter changes on top of that larger "
            "network. This lane exists so reward tuning stays inside the new "
            "network-size regime instead of falling back to hidden_dim=256."
        ),
    },
    "v11_recurrent_actor_gru256_screen_from_scratch": {
        "name": "v11_recurrent_actor_gru256_screen_from_scratch",
        "proposal_name": "structural_v11_recurrent_actor_gru256_screen_30m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": True,
        "requires_training_support": "recurrent_actor_gru256",
        "research_packet": LOOP061_RECURRENT_ACTOR_GRU_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP061_RECURRENT_ACTOR_GRU_DECISION_PACKET,
        "architecture": {
            "policy_arch": "recurrent_actor_gru256",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": {
                "pre_mlp": [128, 128],
                "recurrent": "gru",
                "recurrent_hidden_dim": 256,
                "post_mlp": [192, 96],
                "action_head": 4,
                "action_activation": "tanh",
                "learned_log_std": True,
            },
            "critic": {
                "critic_obs": "same_as_actor_obs",
                "mlp": [256, 256],
                "privileged_state": False,
            },
            "sequence_len": 32,
            "reset_hidden_on_done": True,
            "privileged_critic_followup": (
                "Only launch a later privileged-critic lane after this same-observation "
                "GRU Actor lane shows non-zero hard-eval success or meaningful mean_gates "
                "improvement."
            ),
        },
        "params": {
            "learning_rate": 5e-5,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "recurrent_actor_gru256",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Level3 is a local-observation, partially observable randomized "
            "obstacle-racing problem. After retaining the 2x256 MLP baseline and "
            "using hidden512 only as a cheap capacity ablation, the next higher-value "
            "structural test is a recurrent Actor with GRU-256 memory. The first "
            "GRU lane intentionally keeps the v5 68-dim local observation, the "
            "loop052 reward/controller/PPO scale, and a same-observation 2x256 "
            "Critic so the experiment isolates temporal memory before adding a "
            "privileged Critic. Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v12_mlp_loop052_constant_lr_nominal_reward": {
        "name": "v12_mlp_loop052_constant_lr_nominal_reward",
        "proposal_name": "structural_v12_mlp_loop052_constant_lr_nominal_reward_20m",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP062_MLP_CONSTANT_LR_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP062_MLP_CONSTANT_LR_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["anneal_lr"],
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop062 rejected the first GRU screen: hard eval stayed at 0% "
            "success with only 0.1 mean_gates, and W&B showed no pass/finish "
            "conversion plus near-zero KL/clipfrac. Do not mature that GRU "
            "lane. Return to the global-best loop052 MLP/v5 checkpoint and "
            "isolate one training-number variable that previous loop052 "
            "fine-tunes did not test: keep the nominal reward, observation, "
            "controller, MLP size, learning rate, epochs, entropy, and target "
            "KL fixed, but disable learning-rate annealing so update pressure "
            "does not decay to zero during a short 20M fine-tune. Hard eval "
            "remains on unchanged level3_dr.toml."
        ),
    },
    "v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety": {
        "name": "v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety",
        "proposal_name": (
            "structural_v13_mlp_loop052_constant_lr_gate_acquisition_"
            "nominal_safety_20m"
        ),
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP064_GATE_ACQUISITION_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP064_GATE_ACQUISITION_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_reward_numbers": [
                "gate_stage_coef",
                "gate_axis_coef",
                "gate_front_bonus",
                "gate_bonus",
                "gate_back_bonus",
                "finish_bonus",
                "time_penalty",
            ],
            "changed_training_numbers": ["anneal_lr"],
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 13.0,
            "gate_axis_coef": 24.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 200.0,
            "gate_front_bonus": 5.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 35.0,
            "finish_bonus": 175.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.02,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop064 confirmed that disabling learning-rate annealing restores "
            "nonzero PPO update pressure, but nominal loop052 reward numbers did "
            "not convert into better hard-eval gate acquisition or success. Keep "
            "the global-best loop052 checkpoint, v5 local-obstacle observation, "
            "2x256 MLP, constant 5e-5 learning rate, and loop052 nominal safety "
            "scale, while testing a bounded gate-acquisition reward-number "
            "increase. Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v14_mlp_loop052_constant_lr_directional_pass_conversion_guard": {
        "name": "v14_mlp_loop052_constant_lr_directional_pass_conversion_guard",
        "proposal_name": (
            "structural_v14_mlp_loop052_constant_lr_directional_pass_"
            "conversion_guard_20m"
        ),
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP065_DIRECTIONAL_PASS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP065_DIRECTIONAL_PASS_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_reward_numbers": [
                "gate_stage_coef",
                "gate_axis_coef",
                "gate_front_bonus",
                "gate_bonus",
                "gate_back_bonus",
                "finish_bonus",
                "wrong_side_penalty",
                "time_penalty",
            ],
            "changed_training_numbers": ["anneal_lr"],
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 12.0,
            "gate_axis_coef": 18.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 150.0,
            "gate_front_bonus": 14.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 55.0,
            "finish_bonus": 220.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 14.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.0,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop065/v13 increased raw gate-acquisition pressure but did not "
            "improve hard-eval success, mean gates, or crash versus loop052; W&B "
            "pass, finish, and gate-plane crossing rates stayed flat. Keep "
            "loop052 initialization, v5 local-obstacle observation, 2x256 MLP, "
            "constant 5e-5 learning rate, and nominal safety scale, but reduce "
            "raw gate_bonus pressure and move reward weight toward directional "
            "front/back pass conversion plus wrong-side guarding. Hard eval "
            "remains on unchanged level3_dr.toml."
        ),
    },
    "v15_loop052_sensor15_curriculum_nominal_reward": {
        "name": "v15_loop052_sensor15_curriculum_nominal_reward",
        "proposal_name": (
            "structural_v15_loop052_sensor15_curriculum_nominal_reward_20m"
        ),
        "config": "level3_dr_stage2_gate0_sensor15.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP066_SENSOR15_CURRICULUM_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["train_sensor_range", "anneal_lr"],
            "changed_reward_numbers": [],
            "train_config": "level3_dr_stage2_gate0_sensor15.toml",
            "hard_eval_config": "level3_dr.toml",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop066 trace analysis rejected another v14 continuation, hidden512, "
            "GRU maturation, and simple reward-number repeats. The remaining "
            "near-term bottleneck is geometry-conditioned route learning on "
            "specific gate/obstacle corridors. Start from the loop052 global-best "
            "checkpoint, keep the v5 local-obstacle observation, 2x256 MLP, "
            "loop052 nominal reward numbers, and deploy train wrappers, but use "
            "the existing training-only sensor_range=1.5 config to expose local "
            "gate/obstacle geometry earlier. Hard eval remains on unchanged "
            "level3_dr.toml."
        ),
    },
    "v15_sensor15_curriculum_maturation_from_loop067_10m": {
        "name": "v15_sensor15_curriculum_maturation_from_loop067_10m",
        "proposal_name": (
            "structural_v15_sensor15_curriculum_maturation_from_loop067_10m_to_60m"
        ),
        "config": "level3_dr_stage2_gate0_sensor15.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 50_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP067_10M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP067_SENSOR15_CURRICULUM_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["train_sensor_range", "anneal_lr"],
            "changed_reward_numbers": [],
            "train_config": "level3_dr_stage2_gate0_sensor15.toml",
            "hard_eval_config": "level3_dr.toml",
            "continuation_anchor": "loop067:10M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop067's 10M checkpoint matched loop052 success, improved mean "
            "gates from 1.40 to 1.60, and did not worsen crash rate, satisfying "
            "the v15 promotion rule. Continue the same sensor15 curriculum from "
            "that 10M checkpoint toward a 60M-level maturation decision. Do not "
            "continue from loop067 final, do not apply the analyzer's generic "
            "gate-acquisition reward bump, and keep hard eval on unchanged "
            "level3_dr.toml."
        ),
    },
    "v16_first_gate_hard_corridor_sampler_from_loop052": {
        "name": "v16_first_gate_hard_corridor_sampler_from_loop052",
        "proposal_name": "structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP068_TARGETED_GEOMETRY_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "first_gate_hard_corridor",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop052:final",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "first_gate_hard_corridor",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop068 rejected the v15 sensor15 maturation: best success stayed "
            "at 0.20, mean gates regressed to 1.25, and final crashed to 0.00 "
            "success. The next targeted structural lane keeps the unchanged "
            "Level3 hard-eval config, loop052 checkpoint, v5 local-obstacle "
            "observation, 2x256 MLP, and nominal loop052 reward numbers, but "
            "uses a training-only random-track generator profile that samples "
            "a tighter first-obstacle corridor and wider first-gate yaw range. "
            "This tests whether repeated exposure to the dominant first-gate/"
            "first-obstacle geometry failure mode transfers to hard eval."
        ),
    },
    "v16_first_gate_hard_corridor_sampler_maturation_from_loop069_25m": {
        "name": "v16_first_gate_hard_corridor_sampler_maturation_from_loop069_25m",
        "proposal_name": "structural_v16_hard_corridor_mature_loop069_25m_to_60m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 35_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP069_25M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP069_MATURATION_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "first_gate_hard_corridor",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "continuation_anchor": "loop069:25M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "first_gate_hard_corridor",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop069's 25M checkpoint narrowly satisfies the v16 promotion "
            "rule: success matches loop052 at 0.20, crash stays at 0.80, mean "
            "gates improves to 1.45, and mean successful time improves to "
            "6.675s. All three post-run reviewers recommended cautious "
            "maturation from the 25M checkpoint rather than from final. Keep "
            "the same v16 sampler, v5 observation, 2x256 MLP, constant 5e-5 "
            "learning rate, and nominal loop052 reward numbers; train 35M "
            "additional steps to reach a 60M-level decision horizon. Hard eval "
            "remains on unchanged level3_dr.toml."
        ),
    },
    "v17_trace_conditioned_mixed_corridor_sampler_from_loop069_25m": {
        "name": "v17_trace_conditioned_mixed_corridor_sampler_from_loop069_25m",
        "proposal_name": "structural_v17_trace_mixed_corridor_from_loop069_25m_30m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP069_25M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP070_V17_DECISION_PACKET,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "trace_mixed_corridor",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop069:25M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "trace_mixed_corridor",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop070 exhausted same-hypothesis v16 maturation: all 60M-style "
            "milestones regressed below the loop069 25M anchor and missed the "
            "rollback rule. The next lane keeps loop069 25M, v5 observation, "
            "2x256 MLP, nominal reward numbers, and constant 5e-5 LR, but "
            "replaces the one-mode hard-corridor sampler with a mixed "
            "trace-conditioned training sampler. Most episodes stay on the "
            "default Level3 generator while a minority sample first-gate hard "
            "corridor/yaw cases. This tests whether retaining the base "
            "distribution while injecting trace-derived early corridor cases "
            "transfers better than v16's always-hard first-gate profile. Hard "
            "eval remains on unchanged level3_dr.toml."
        ),
    },
    "v17_trace_mixed_corridor_maturation_from_loop071_20m": {
        "name": "v17_trace_mixed_corridor_maturation_from_loop071_20m",
        "proposal_name": "structural_v17_trace_mixed_mature_loop071_20m_to_60m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 40_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP071_20M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP071_MATURATION_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["train_timesteps", "initial_checkpoint"],
            "changed_reward_numbers": [],
            "track_generator_profile": "trace_mixed_corridor",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop071:20M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "trace_mixed_corridor",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop071 found a checkpoint-local v17 improvement at 20M: 0.25 "
            "success, 2.00 mean gates, 0.75 crash, and 8.524s mean successful "
            "time on hard eval. That beats the v17 screen's promotion rule "
            "on success, gate progress, and crash rate, while the final "
            "checkpoint regressed. Continue from the 20M checkpoint for 40M "
            "additional steps to reach a 60M-level maturation horizon. Keep "
            "v5 observation, 2x256 MLP, trace_mixed_corridor training sampler, "
            "constant 5e-5 learning rate, and loop052 nominal reward numbers. "
            "Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v18_trace_seed_replay_default_retention_from_loop069_25m": {
        "name": "v18_trace_seed_replay_default_retention_from_loop069_25m",
        "proposal_name": "structural_v18_trace_seed_replay_from_loop069_25m_30m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP069_25M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP072_TRACE_SEED_REPLAY_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "trace_seed_replay_default_retention",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop069:25M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "trace_seed_replay_default_retention",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop072 failed v17 maturation: best success regressed to 0.20, "
            "mean gates to 1.60, crash to 0.80, and later milestones fell to "
            "0.10 success. W&B/PPO diagnostics showed stable optimization but "
            "no hard-eval conversion, so continuing v17 or adding time pressure "
            "is unsupported. This lane returns to the loop069 25M hard-eval "
            "global-best anchor, keeps v5 observation, 2x256 MLP, constant "
            "5e-5 LR, and loop052 nominal reward numbers, but replaces v17's "
            "broad hard-corridor sampler with a training-only seed-replay "
            "sampler. The sampler mixes 25% hard/frontier eval seed track "
            "layouts with 75% default Level3 random layouts. Hard eval remains "
            "on unchanged level3_dr.toml."
        ),
    },
    "v19_trace_seed_replay_lowprob_success_retention_from_loop069_25m": {
        "name": "v19_trace_seed_replay_lowprob_success_retention_from_loop069_25m",
        "proposal_name": "structural_v19_lowprob_replay_success_retention_from_loop069_25m_30m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": SCREENING_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP069_25M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP073_LOWPROB_REPLAY_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "trace_seed_replay_lowprob_success_retention",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop069:25M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "trace_seed_replay_lowprob_success_retention",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop073 rejected v18 seed replay because 25% hard-seed replay "
            "regressed success to 0.15 and crash to 0.85, while targeted "
            "replay seeds only reached 1/10 success and the lane traded away "
            "loop069 retention successes. This lane keeps the same loop069 "
            "25M anchor, v5 observation, 2x256 MLP, constant 5e-5 LR, and "
            "loop052 nominal reward numbers, but lowers replay probability "
            "to 0.12 and balances the seed set between loop069 retention "
            "successes, v17/v18 frontier successes, and hard-progress seeds. "
            "Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v19_trace_seed_replay_lowprob_success_retention_maturation_from_loop074_20m": {
        "name": "v19_trace_seed_replay_lowprob_success_retention_maturation_from_loop074_20m",
        "proposal_name": "structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 40_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP074_20M_CHECKPOINT,
        "research_packet": LOOP066_TRACE_AXIS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP074_V19_MATURATION_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile", "anneal_lr"],
            "changed_reward_numbers": [],
            "track_generator_profile": "trace_seed_replay_lowprob_success_retention",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop074:20M",
            "continuation_anchor": "loop074:20M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "trace_seed_replay_lowprob_success_retention",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop074 restored the v19 rollback floor from the loop074 20M "
            "checkpoint: 0.20 success, 0.80 crash, 1.60 mean gates, and "
            "partial success-seed retention, but it did not recover loop071's "
            "0.25 success or 2.00 mean-gates diagnostic frontier. All three "
            "post-run reviewers recommended continuing the same low-probability "
            "seed-replay hypothesis from loop074 20M instead of changing reward "
            "numbers or switching structure. This lane matures that exact "
            "hypothesis toward a 60M-level decision while keeping hard eval on "
            "unchanged level3_dr.toml."
        ),
    },
    "v20_loop071_default_distribution_recovery_20m": {
        "name": "v20_loop071_default_distribution_recovery_20m",
        "proposal_name": "structural_v20_loop071_default_distribution_recovery_20m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP071_20M_CHECKPOINT,
        "research_packet": LOOP075_TRACE_DIAGNOSTIC_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP075_V20_DEFAULT_RECOVERY_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile"],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop071:20M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "The loop075 trace diagnostic rejects the seed-replay family: "
            "loop074 and loop075 retained success only on replay seeds, while "
            "loop071 20M is the only compared checkpoint with non-replay "
            "successes and the best diagnostic frontier at 0.25 success and "
            "2.00 mean gates. Start from loop071 20M and return training to "
            "the default Level3 distribution for one 20M screen, keeping v5 "
            "observation, the 2x256 MLP, constant 5e-5 learning rate, loop052 "
            "nominal reward numbers, and hard eval on unchanged level3_dr.toml."
        ),
    },
    "v21_default_gate_obstacle_frame_recovery_from_loop071_20m": {
        "name": "v21_default_gate_obstacle_frame_recovery_from_loop071_20m",
        "proposal_name": "structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP071_20M_CHECKPOINT,
        "research_packet": LOOP076_V21_GATE_ACQUISITION_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP076_V21_GATE_ACQUISITION_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["track_generator_profile"],
            "changed_reward_numbers": [
                "gate_stage_coef",
                "gate_axis_coef",
                "gate_front_bonus",
                "gate_bonus",
                "gate_back_bonus",
                "finish_bonus",
                "time_penalty",
            ],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop071:20M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 13.0,
            "gate_axis_coef": 24.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 200.0,
            "gate_front_bonus": 5.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 35.0,
            "finish_bonus": 175.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.02,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop076 rejected default-distribution continuation from loop071: "
            "it tied loop069 on success and crash but was slower, and failed "
            "to recover loop071's 0.25 success and 2.00 mean-gates frontier. "
            "All reviewers rejected v20 maturation and PPO changes. This lane "
            "returns to the loop071 20M anchor, keeps default Level3 training, "
            "v5 observation, 2x256 MLP, constant 5e-5 learning rate, PPO "
            "settings, obstacle/crash safety, and legacy_staged reward "
            "structure, while applying only the bounded gate-acquisition "
            "reward-number increase recommended by the loop076 analyzer. Hard "
            "eval remains on unchanged level3_dr.toml."
        ),
    },
    "v22_loop071_gate_corridor_obstacle_obs_default_20m": {
        "name": "v22_loop071_gate_corridor_obstacle_obs_default_20m",
        "proposal_name": "structural_v22_loop071_gate_corridor_obstacle_obs_default_20m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP071_20M_CHECKPOINT,
        "research_packet": LOOP077_V22_GATE_CORRIDOR_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP077_V22_GATE_CORRIDOR_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_observation_layout": "gate_corridor_obstacle_relative",
            "changed_training_numbers": ["track_generator_profile"],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop071:20M",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop077/v21 showed that stronger gate-acquisition reward numbers "
            "increased near-gate obstacle/frame crashes and did not recover "
            "loop071's 0.25 success and 2.00 mean-gates diagnostic frontier. "
            "The trace synthesis recommends a structural observation lane "
            "rather than another reward-number increase. This lane starts from "
            "the loop071 20M frontier, keeps the default Level3 training "
            "distribution, 2x256 MLP, constant 5e-5 learning rate, PPO settings, "
            "controller settings, and nominal loop071 reward numbers fixed, but "
            "switches to the existing gate-corridor obstacle observation layout "
            "with zero-padded warm-start support. Hard eval remains on unchanged "
            "level3_dr.toml."
        ),
    },
    "v22_gate_corridor_obs_maturation_from_loop078_final_to_60m": {
        "name": "v22_gate_corridor_obs_maturation_from_loop078_final_to_60m",
        "proposal_name": "structural_v22_gate_corridor_obs_mature_loop078_final_to_60m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 40_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": LOOP078_ANALYSIS_PACKET,
        "approved_hypothesis_packet": LOOP078_V22_MATURATION_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": ["train_timesteps", "initial_checkpoint"],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop078:final",
            "continuation_anchor": "loop078:final",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop078/v22 established a new global best on hard eval: 0.25 "
            "success, 2.05 mean gates, 0.75 crash, and 8.048s mean successful "
            "time. It matched loop071's success/crash frontier, improved mean "
            "gates, and improved time versus loop071, while keeping hard eval "
            "on unchanged level3_dr.toml. All three post-run reviewers "
            "recommended maturing the same v22 hypothesis before changing "
            "reward numbers or PPO/training structure. Continue from loop078 "
            "final for 40M more steps to reach a 60M-style decision horizon, "
            "keeping v8 gate-corridor observation, default training "
            "distribution, 2x256 MLP, PPO settings, controller settings, and "
            "nominal reward numbers fixed."
        ),
    },
    "v23_v22_frame_obstacle_retention_from_loop078_final_20m": {
        "name": "v23_v22_frame_obstacle_retention_from_loop078_final_20m",
        "proposal_name": "structural_v23_v22_frame_obstacle_retention_from_loop078_final_20m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": LOOP079_V23_FRAME_OBSTACLE_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP079_V23_FRAME_OBSTACLE_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "initial_checkpoint",
                "learning_rate",
            ],
            "changed_reward_numbers": [
                "reward_structure",
                "gate_frame_pressure_coef",
                "obstacle_coef",
                "obstacle_margin",
                "time_penalty",
            ],
            "track_generator_profile": "default",
            "reward_structure": "decoupled_frame_clearance",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop078:final",
            "continuation_anchor": "loop078:final",
        },
        "params": {
            "learning_rate": 2e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "decoupled_frame_clearance",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 1.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 10.0,
            "obstacle_margin": 0.45,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.015,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop079 same-hypothesis v22 maturation regressed from loop078's "
            "0.25 success, 2.05 mean gates, and 0.75 crash to a best of "
            "0.15 success, 1.55 mean gates, and 0.85 crash. The trace "
            "diagnostic shows success-retention loss and dominant near-gate "
            "obstacle/frame endpoints; weight interpolation failed to recover "
            "the union of successful seeds. This lane returns to loop078 final, "
            "keeps v8 gate-corridor observation and the 2x256 MLP, lowers "
            "learning rate to reduce further forgetting, and activates a "
            "decoupled frame-clearance penalty plus modest obstacle-safety "
            "increase and lower time pressure. Hard eval remains on unchanged "
            "level3_dr.toml."
        ),
    },
    "v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m": {
        "name": "v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m",
        "proposal_name": (
            "structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m"
        ),
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": LOOP080_V24_HYBRID_OBS_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP080_V24_HYBRID_OBS_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_observation_layout": (
                "gate_corridor_obstacle_relative_plus_aperture_margin"
            ),
            "changed_training_numbers": ["initial_checkpoint"],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop078:final",
            "continuation_anchor": "loop078:final",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop080/v23 rejected reward-structure and obstacle-pressure "
            "retention from loop078: best hard eval stayed below loop078, and "
            "final regressed to 0.10 success. The structure reviewer recommends "
            "an observation-structure test rather than another reward scalar. "
            "This lane starts from loop078 final, preserves v8 gate-corridor "
            "obstacle behavior, appends v9-style aperture-margin geometry via "
            "a new v10 hybrid observation layout with zero-padded warm-start, "
            "and keeps reward, PPO, controller, and default Level3 distribution "
            "fixed. Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m": {
        "name": "v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m",
        "proposal_name": (
            "structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m"
        ),
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": LOOP081_V25_MINIMAL_APERTURE_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP081_V25_MINIMAL_APERTURE_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_APERTURE_MARGIN_MINIMAL_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_observation_layout": (
                "gate_corridor_obstacle_relative_plus_aperture_margins_only"
            ),
            "changed_training_numbers": ["initial_checkpoint"],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop078:final",
            "continuation_anchor": "loop078:final",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop081/v24 appended the full v9 aperture-margin block to v8 but "
            "failed to preserve loop078 retention: hard eval regressed to "
            "0.15 success, 1.45 mean gates, and 0.85 crash. Reviewers agreed "
            "PPO was stable enough and the issue was non-conversion, not "
            "optimizer instability. This lane returns to loop078 final, keeps "
            "v22 reward/PPO/controller numbers fixed, and tests a minimal "
            "observation ablation: v8 plus only five aperture margin features, "
            "avoiding duplicate target-progress and gate-frame-position inputs. "
            "Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v26_v23_10m_success_replay_retention_20m": {
        "name": "v26_v23_10m_success_replay_retention_20m",
        "proposal_name": "structural_v26_v23_10m_success_replay_retention_20m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": DEFAULT_TRAIN_TIMESTEPS,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP080_V23_10M_CHECKPOINT,
        "research_packet": LOOP082_V26_SUCCESS_REPLAY_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP082_V26_SUCCESS_REPLAY_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "initial_checkpoint",
                "track_generator_profile",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "loop078_v23_success_replay_lowprob",
            "reward_structure": "decoupled_frame_clearance",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "v23:10M",
            "continuation_anchor": "v23:10M",
        },
        "params": {
            "learning_rate": 2e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "decoupled_frame_clearance",
            "track_generator_profile": "loop078_v23_success_replay_lowprob",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 1.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 10.0,
            "obstacle_margin": 0.45,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.015,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop082/v25 and aperture observation additions were rejected after "
            "trace diagnostics. The closest post-loop078 variant is v23 10M: "
            "0.20 success, 2.00 mean gates, 0.80 crash, and successful seeds "
            "4, 5, 12, 18. Loop078 final succeeds on 4, 9, 12, 18, 19. "
            "Simple weight interpolation did not combine these seed sets. This "
            "lane starts from v23 10M and uses a low-probability training-only "
            "hard-eval seed replay profile over the union [4, 5, 9, 12, 18, "
            "19], preserving v8 observation and v23 decoupled frame-clearance "
            "reward settings. Hard eval remains on unchanged level3_dr.toml."
        ),
    },
    "v26_v23_10m_success_replay_retention_maturation_to_60m": {
        "name": "v26_v23_10m_success_replay_retention_maturation_to_60m",
        "proposal_name": (
            "structural_v26_v23_10m_success_replay_retention_mature_to_60m"
        ),
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 45_000_000,
        "checkpoint_interval": 5_000_000,
        "from_scratch": False,
        "initial_checkpoint": LOOP083_V26_15M_CHECKPOINT,
        "research_packet": LOOP082_V26_SUCCESS_REPLAY_SYNTHESIS_PACKET,
        "approved_hypothesis_packet": LOOP083_V26_MATURATION_DECISION_PACKET,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "train_timesteps",
                "initial_checkpoint",
                "track_generator_profile",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "loop078_v23_success_replay_lowprob",
            "reward_structure": "decoupled_frame_clearance",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "initial_checkpoint": "loop083:15M",
            "continuation_anchor": "loop083:15M",
        },
        "params": {
            "learning_rate": 2e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "decoupled_frame_clearance",
            "track_generator_profile": "loop078_v23_success_replay_lowprob",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 1.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 10.0,
            "obstacle_margin": 0.45,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.015,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "loop083/v26 did not beat loop078, so it is not promoted. Its "
            "best 15M checkpoint reached 0.20 success, 2.00 mean gates, 0.80 "
            "crash, and 7.595s, with successful seeds 4, 8, 9, and 12. This "
            "is below loop078's 0.25 success, 2.05 mean gates, and 0.75 crash, "
            "but it is close enough to the frontier to justify one "
            "step-curve maturation under the Level2-calibrated policy. Continue "
            "from loop083 15M for 45M additional steps, keeping v8 observation, "
            "v23 decoupled frame-clearance reward settings, 2x256 MLP, and the "
            "low-probability success-replay training profile fixed. Hard eval "
            "remains on unchanged level3_dr.toml. If the 60M-style result does "
            "not exceed loop078 on hard eval, reject v26."
        ),
    },
    "v27_teacher_retention_beta0_5m": {
        "name": "v27_teacher_retention_beta0_5m",
        "proposal_name": "structural_v27_teacher_retention_beta0_control_5m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": V27_TEACHER_RETENTION_SPEC_PACKET,
        "approved_hypothesis_packet": V27_BETA0_CONTROL_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "train_timesteps",
                "checkpoint_interval",
                "v27_teacher_kl_beta",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "teacher_checkpoint": "loop052:final",
            "student_initial_checkpoint": "loop078:final",
            "v27_beta": 0.0,
            "retention_dataset": "disabled_control_arm",
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "v27_teacher_kl_beta": 0.0,
            "v27_teacher_model_name": LOOP052_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "v27_retention_dataset_path": "disabled_control_arm",
            "v27_lane_name": "v27_teacher_retention_beta0_5m",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "After the unseen-validation audit selected loop052 final as the "
            "teacher/reliability anchor, v27 needs a no-teacher-KL control arm "
            "before beta=0.03 or beta=0.10 can be interpreted. This lane starts "
            "from the observation-compatible loop078 v8 student checkpoint, "
            "keeps the v8 gate-corridor observation, 2x256 MLP, loop078/v22 "
            "reward and PPO settings, and default Level3 training distribution, "
            "but shortens the screen to 5M with 1M checkpoint evaluation. Hard "
            "eval remains on unchanged level3_dr.toml using the dev-to-validation "
            "seed-manifest protocol."
        ),
    },
    "v27_teacher_retention_beta003_5m": {
        "name": "v27_teacher_retention_beta003_5m",
        "proposal_name": "structural_v27_teacher_retention_beta003_5m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": V27_TEACHER_RETENTION_SPEC_PACKET,
        "approved_hypothesis_packet": V27_BETA003_TEACHER_KL_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "train_timesteps",
                "checkpoint_interval",
                "v27_teacher_kl_beta",
                "v27_retention_batch_size",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "teacher_checkpoint": "loop052:final",
            "student_initial_checkpoint": "loop078:final",
            "v27_beta": 0.03,
            "retention_dataset": V27_RETENTION_DATASET_PATH,
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "v27_teacher_kl_beta": 0.03,
            "v27_teacher_model_name": LOOP052_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "v27_retention_dataset_path": V27_RETENTION_DATASET_PATH,
            "v27_retention_batch_size": 512,
            "v27_lane_name": "v27_teacher_retention_beta003_5m",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Light v27 teacher-retention arm. It keeps the loop085 beta=0 "
            "control setup fixed but enables beta=0.03 KL(pi_teacher || "
            "pi_student) on a train_pool retention dataset from successful "
            "loop052 teacher states. The lane is a 5M screen with 1M "
            "checkpoints, hard-evaluated on unchanged level3_dr.toml through "
            "the dev-to-validation seed-manifest protocol."
        ),
    },
    "v27_teacher_retention_beta010_5m": {
        "name": "v27_teacher_retention_beta010_5m",
        "proposal_name": "structural_v27_teacher_retention_beta010_5m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "from_scratch": False,
        "initial_checkpoint": LOOP078_FINAL_CHECKPOINT,
        "research_packet": V27_TEACHER_RETENTION_SPEC_PACKET,
        "approved_hypothesis_packet": V27_EVAL_PROTOCOL_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "train_timesteps",
                "checkpoint_interval",
                "v27_teacher_kl_beta",
                "v27_retention_batch_size",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "default",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "teacher_checkpoint": "loop052:final",
            "student_initial_checkpoint": "loop078:final",
            "v27_beta": 0.10,
            "retention_dataset": V27_RETENTION_DATASET_PATH,
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "default",
            "v27_teacher_kl_beta": 0.10,
            "v27_teacher_model_name": LOOP052_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "v27_retention_dataset_path": V27_RETENTION_DATASET_PATH,
            "v27_retention_batch_size": 512,
            "v27_lane_name": "v27_teacher_retention_beta010_5m",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Medium v27 teacher-retention arm. This should only be launched "
            "after beta=0.03 has a post-run decision saying retention metrics "
            "are healthy but validation reliability still falls below the "
            "loop052 anchor. It keeps the unchanged level3_dr.toml hard eval "
            "and the same train_pool retention dataset."
        ),
    },
    "v28_success24_retention_bounds_replay_5m": {
        "name": "v28_success24_retention_bounds_replay_5m",
        "proposal_name": "structural_v28_success24_retention_bounds_replay_5m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "from_scratch": False,
        "initial_checkpoint": LOOP087_FINAL_CHECKPOINT,
        "research_packet": V28_RETENTION_DATA_AUDIT_PACKET,
        "approved_hypothesis_packet": V28_SUCCESS24_BOUNDS_REPLAY_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "train_timesteps",
                "checkpoint_interval",
                "track_generator_profile",
                "v27_retention_dataset_path",
                "v27_retention_batch_size",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "v28_train_pool_bounds_failure_replay",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "teacher_checkpoint": "loop052:final",
            "student_initial_checkpoint": "loop087:final",
            "v27_beta": 0.10,
            "retention_dataset": V28_SUCCESS24_RETENTION_DATASET_PATH,
            "failure_dataset": V28_FAILURE_TRAJECTORY_DATASET_PATH,
            "failure_replay_seed_probability": 0.20,
            "failure_replay_seeds": [
                2114,
                2115,
                2120,
                2121,
                2126,
                2128,
                2131,
                2135,
                2142,
                2143,
                2146,
                2149,
                2151,
                2153,
                2161,
                2162,
                2167,
                2168,
                2172,
                2179,
                2181,
                2189,
                2193,
                2195,
                2200,
                2202,
                2203,
                2207,
                2211,
            ],
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "v28_train_pool_bounds_failure_replay",
            "v27_teacher_kl_beta": 0.10,
            "v27_teacher_model_name": LOOP052_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "v27_retention_dataset_path": V28_SUCCESS24_RETENTION_DATASET_PATH,
            "v27_retention_batch_size": 512,
            "v27_lane_name": "v28_success24_retention_bounds_replay_5m",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Loop087 showed that beta=0.10 teacher retention is numerically "
            "healthy but too narrow to beat the loop052 hard-eval anchor. The "
            "v28 lane keeps the same v8 observation, 2x256 MLP, legacy reward "
            "scale, and unchanged level3_dr hard eval, but expands retention "
            "from 8 to 24 train_pool teacher-success episodes and mixes a 20% "
            "training-only replay of audited train_pool bounds-or-ground "
            "failure seeds. This tests whether success preservation plus "
            "failure-geometry correction converts into validation progress "
            "without using dev, validation, or final_locked seeds for training."
        ),
    },
    "v29_revert_reward_success_churn_replay_5m": {
        "name": "v29_revert_reward_success_churn_replay_5m",
        "proposal_name": "structural_v29_revert_reward_success_churn_replay_5m",
        "config": "level3_dr.toml",
        "eval_config": "level3_dr.toml",
        "observation_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "from_scratch": False,
        "initial_checkpoint": LOOP088_4M_CHECKPOINT,
        "research_packet": V29_TRAIN_POOL_SUCCESS_CHURN_PACKET,
        "approved_hypothesis_packet": V29_REVERT_REWARD_SUCCESS_CHURN_DECISION_PACKET,
        "allow_repeat_params": True,
        "architecture": {
            "policy_arch": "mlp_2x_tanh",
            "actor_obs_layout": LOCAL_GATE_CORRIDOR_OBSTACLE_OBSERVATION_LAYOUT,
            "actor": [256, 256],
            "critic": [256, 256],
            "changed_training_numbers": [
                "initial_checkpoint",
                "track_generator_profile",
            ],
            "changed_reward_numbers": [],
            "track_generator_profile": "v29_train_pool_success_churn_replay",
            "reward_structure": "legacy_staged",
            "train_config": "level3_dr.toml",
            "hard_eval_config": "level3_dr.toml",
            "teacher_checkpoint": "loop052:final",
            "student_initial_checkpoint": "loop088:4M",
            "v27_beta": 0.10,
            "retention_dataset": V28_SUCCESS24_RETENTION_DATASET_PATH,
            "train_pool_success_churn_probe": V29_TRAIN_POOL_SUCCESS_CHURN_PACKET,
            "replay_seed_probability": 0.16,
            "replay_seeds": [
                2301,
                2321,
                2330,
                2331,
                2335,
                2343,
                2352,
                2353,
                2355,
                2361,
                2364,
                2370,
                2374,
                2381,
                2383,
                2384,
            ],
            "reference_rejected_checkpoint": LOOP089_2M_CHECKPOINT,
        },
        "params": {
            "learning_rate": 5e-5,
            "anneal_lr": False,
            "gamma": 0.99,
            "gae_lambda": 0.95,
            "update_epochs": 5,
            "num_minibatches": 8,
            "clip_coef": 0.26,
            "clip_vloss": True,
            "ent_coef": 0.02,
            "vf_coef": 0.7,
            "max_grad_norm": 1.5,
            "target_kl": 0.03,
            "hidden_dim": 256,
            "policy_arch": "mlp_2x_tanh",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 32,
            "n_obs": 2,
            "action_rp_limit_deg": 90.0,
            "action_lowpass_alpha": 1.0,
            "reward_structure": "legacy_staged",
            "track_generator_profile": "v29_train_pool_success_churn_replay",
            "v27_teacher_kl_beta": 0.10,
            "v27_teacher_model_name": LOOP052_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "v27_retention_dataset_path": V28_SUCCESS24_RETENTION_DATASET_PATH,
            "v27_retention_batch_size": 512,
            "v27_lane_name": "v29_revert_reward_success_churn_replay_5m",
            "progress_coef": 0.0,
            "gate_stage_coef": 10.0,
            "gate_axis_coef": 12.0,
            "near_gate_coef": 0.0,
            "gate_bonus": 90.0,
            "gate_front_bonus": 0.0,
            "gate_plane_bonus": 0.0,
            "gate_back_bonus": 12.0,
            "finish_bonus": 160.0,
            "missed_gate_penalty": 0.0,
            "gate_frame_pressure_coef": 0.0,
            "wrong_side_penalty": 8.0,
            "crash_penalty": 100.0,
            "obstacle_coef": 8.0,
            "obstacle_margin": 0.4,
            "obstacle_clearance_coef": 6.0,
            "timeout_penalty": 80.0,
            "time_penalty": 0.03,
            "act_coef": 0.03,
            "d_act_th_coef": 0.1,
            "d_act_xy_coef": 0.1,
            "cmd_tilt_coef": 1.0,
            "rpy_coef": 1.0,
            "tilt_limit_deg": 40.0,
            "tilt_excess_coef": 15.0,
        },
        "rationale": (
            "Loop089's gate-conversion reward escalation improved some W&B "
            "signals but worsened validation success, mean gates, and crash "
            "rate relative to loop088 4M. The v29 lane reverts to the loop088 "
            "reward scale and tests a narrower training-data hypothesis: keep "
            "success24 teacher retention, start from loop088 4M, and mix a "
            "low-probability train_pool-only replay of seeds where loop088 and "
            "loop089 disagree about success. This avoids validation/final seed "
            "leakage while probing whether success behavior can be preserved "
            "without another reward-number escalation."
        ),
    },
    "v30_episode_semantics_only_2m": {
        "name": "v30_episode_semantics_only_2m",
        "proposal_name": "structural_v30_episode_semantics_only_2m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 2_000_000,
        "checkpoint_interval": 500_000,
        "max_eval_checkpoints": 4,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "0.5,1,1.5,2",
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "requires_training_support": "v30_episode_semantics",
        "research_packet": V30_SEMANTICS_AUDIT_PACKET,
        "approved_hypothesis_packet": V30_CORRECTED_SEMANTICS_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
        },
        "hypothesis": {
            "baseline": "loop052 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "domain_randomized_config_role": (
                f"{DOMAIN_RANDOMIZED_TRAIN_CONFIG} is optional sim-to-real robustness training, "
                "not the final acceptance target."
            ),
            "teacher_kl": "disabled",
            "static_seed_replay": "disabled",
            "final_locked": "forbidden",
            "training_seeds_required": 3,
            "promotion_gate": {
                "median_success_rate": 0.25,
                "any_checkpoint_success_rate": 0.30,
                "max_crash_rate": 0.70,
                "min_mean_gates": 1.60,
            },
        },
        "params": LOOP052_REMOTE_NOMINAL_PARAMS,
        "rationale": (
            "Loop090 did not disprove end-to-end PPO; it showed that reward "
            "tuning, static replay, teacher KL, and short continuation did not "
            "convert. v30-A isolates episode/reset/finish semantics while "
            "keeping loop052 observation, network, reward, PPO numbers, and "
            "hard-eval track fixed."
        ),
    },
    "v30_squashed_gaussian_episode_semantics_2m": {
        "name": "v30_squashed_gaussian_episode_semantics_2m",
        "proposal_name": "structural_v30_squashed_gaussian_episode_semantics_2m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 2_000_000,
        "checkpoint_interval": 500_000,
        "max_eval_checkpoints": 4,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "0.5,1,1.5,2",
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "requires_training_support": "v30_squashed_gaussian_episode_semantics",
        "research_packet": V30_SEMANTICS_AUDIT_PACKET,
        "approved_hypothesis_packet": V30_CORRECTED_SEMANTICS_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "tanh_squashed_gaussian",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "required_zero_update_parity": {
                "anchor_checkpoint": LOOP052_BEST_CHECKPOINT,
                "split": "validation_unseen_101_200",
                "max_step_action_abs_error": 1e-6,
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
                "squashed_gaussian_logprob_jacobian",
            ],
        },
        "hypothesis": {
            "baseline": "loop052 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "domain_randomized_config_role": (
                f"{DOMAIN_RANDOMIZED_TRAIN_CONFIG} is optional sim-to-real robustness training, "
                "not the final acceptance target."
            ),
            "teacher_kl": "disabled",
            "static_seed_replay": "disabled",
            "final_locked": "forbidden",
            "training_seeds_required": 3,
            "promotion_gate": {
                "median_success_rate": 0.25,
                "any_checkpoint_success_rate": 0.30,
                "max_crash_rate": 0.70,
                "min_mean_gates": 1.60,
            },
        },
        "params": LOOP052_REMOTE_NOMINAL_PARAMS,
        "rationale": (
            "v30-B tests whether matching PPO log-probability to the executed "
            "bounded action fixes a training/simulation mismatch, after the "
            "episode/reset semantics from v30-A are also repaired. The "
            "zero-update deterministic action path must match loop052 before "
            "any training is launched."
        ),
    },
    "v31a_longer_rollout_clean_ppo_5m": {
        "name": "v31a_longer_rollout_clean_ppo_5m",
        "proposal_name": "structural_v31a_longer_rollout_clean_ppo_5m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP052_BEST_CHECKPOINT,
        "requires_training_support": "v30_episode_semantics",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V31A_LONGER_ROLLOUT_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "comparison_baseline": "v30-A used 1024 envs x 32 steps",
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
            "not_yet_implemented_support": [
                "actor_observation_running_normalization",
                "return_or_value_running_scale",
                "asymmetric_privileged_critic",
                "gate_phase_reset_buffer",
                "prioritized_level_replay",
                "tanh_squashed_gaussian_logprob",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 1 partial clean PPO baseline",
            "baseline": "loop052 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "domain_randomized_config_role": (
                f"{DOMAIN_RANDOMIZED_TRAIN_CONFIG} remains optional training-only "
                "robustness evidence, not final acceptance."
            ),
            "primary_question": (
                "Does reducing vector parallelism and extending per-env rollout "
                "from 0.64s to 2.56s improve credit assignment and hard-eval "
                "gate progress under the corrected v30 episode semantics?"
            ),
            "success_screen": {
                "beats_loop093_success_rate": "> 0.17",
                "beats_loop093_mean_gates": "> 1.55",
                "promising_for_maturation": (
                    "non-zero success with mean_gates >= 1.60 or success >= 0.20"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 43,
        },
        "rationale": (
            "The framework packet argues that 1024x32 rollouts may be too short "
            "for gate approach, crossing, and recovery credit assignment at 50 Hz. "
            "This lane keeps loop052 reward/PPO numbers, v5 deployment observation, "
            "and the corrected v30 episode/reset semantics fixed, but changes the "
            "rollout geometry to 256 envs x 128 steps with the same 32768 samples "
            "per PPO update. It is an executable first step toward the clean PPO "
            "baseline before implementing normalization, privileged critic, "
            "gate-phase reset curriculum, PLR, or GRU."
        ),
    },
    "v31b_obs_return_norm_clean_ppo_5m": {
        "name": "v31b_obs_return_norm_clean_ppo_5m",
        "proposal_name": "structural_v31b_obs_return_norm_clean_ppo_5m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "num_envs": 256,
        "num_steps": 128,
        "from_scratch": True,
        "requires_training_support": "observation_return_normalization_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V31B_OBS_RETURN_NORM_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": {
                "actor_observation_running_mean_std": True,
                "frozen_eval_time_actor_stats_from_checkpoint": True,
                "critic_return_running_mean_std": True,
                "gae_scale": "raw_reward_scale",
                "critic_loss_scale": "normalized_return_scale",
                "warm_start": "from_scratch_to_avoid_raw_checkpoint_input_distribution_shift",
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 2 observation and return normalization",
            "baseline": "v31a longer-rollout clean PPO",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Does normalizing actor observations and critic return targets "
                "make the clean PPO baseline train with stronger update signal "
                "and more stable value learning on Level3?"
            ),
            "success_screen": {
                "mechanics": "checkpoint contains obs_normalization and return_normalization",
                "beats_or_explains_v31a": (
                    "success >= 0.19 or W&B/evaluator evidence shows healthier "
                    "value/update dynamics worth maturing beyond 5M"
                ),
                "promising_for_maturation": (
                    "non-zero success with mean_gates >= 1.60, or clear W&B "
                    "conversion with lower value loss and no collapse"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 44,
            "obs_norm_enabled": True,
            "obs_norm_clip": 10.0,
            "return_norm_enabled": True,
            "return_norm_clip": 10.0,
        },
        "rationale": (
            "loop094/v31a showed only a weak hard-eval gain and W&B still had "
            "low PPO update pressure with large raw value targets. The current "
            "framework packet ranks observation/return normalization as the next "
            "implementation step before privileged critic, curriculum, PLR, GRU, "
            "or further reward-number search. This screen starts from scratch "
            "so the Actor never has to reinterpret a raw-observation checkpoint "
            "through newly normalized inputs."
        ),
    },
    "v31c_warmstart_identity_norm_clean_ppo_5m": {
        "name": "v31c_warmstart_identity_norm_clean_ppo_5m",
        "proposal_name": "structural_v31c_warmstart_identity_norm_clean_ppo_5m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": V31C_IDENTITY_NORM_CHECKPOINT,
        "identity_norm_warmstart": {
            "source_checkpoint": LOOP094_BEST_CHECKPOINT,
            "target_checkpoint": V31C_IDENTITY_NORM_CHECKPOINT,
            "obs_count": 1_000_000.0,
            "return_count": 1_000_000.0,
            "requires_zero_update_parity": True,
        },
        "requires_training_support": "observation_return_normalization_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V31C_IDENTITY_NORM_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": {
                "actor_observation_running_mean_std": True,
                "actor_observation_init": "identity_mean0_var1_from_loop094_4m",
                "frozen_eval_time_actor_stats_from_checkpoint": True,
                "critic_return_running_mean_std": True,
                "critic_return_init": "identity_mean0_var1_from_loop094_4m",
                "gae_scale": "raw_reward_scale",
                "critic_loss_scale": "normalized_return_scale",
                "warm_start": "loop094_4m_identity_normalized_checkpoint",
                "parity_gate": "validation_unseen_101_200_zero_update_before_training",
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 2b warm-start-compatible normalization",
            "baseline": "loop094/v31a 4M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can observation/return normalization be introduced without "
                "destroying the working loop094 behavioral prior?"
            ),
            "success_screen": {
                "parity_required_before_training": (
                    "identity-normalized checkpoint hard-eval matches loop094 4M "
                    "within one success-count episode and no material mean-gates drop"
                ),
                "after_training": (
                    "beats loop094 success >= 0.19 or improves mean_gates/crash "
                    "without losing success frontier"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 45,
            "obs_norm_enabled": True,
            "obs_norm_clip": 10.0,
            "return_norm_enabled": True,
            "return_norm_clip": 10.0,
        },
        "rationale": (
            "loop095 showed that from-scratch normalization never acquired gate 0, "
            "while loop094 already has a weak but real Level3 behavior prior. This "
            "lane materializes an identity-normalized copy of loop094 4M, requires "
            "zero-update hard-eval parity before training, then screens whether "
            "normalization can improve value scale without erasing the frontier."
        ),
    },
    "v31d_v31a_longer_rollout_maturation_15m": {
        "name": "v31d_v31a_longer_rollout_maturation_15m",
        "proposal_name": "structural_v31d_v31a_longer_rollout_maturation_15m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 15_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 9,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5,8,10,12,15",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP094_BEST_CHECKPOINT,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "requires_training_support": "v30_episode_semantics",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V31D_V31A_MATURATION_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP094_BEST_CHECKPOINT,
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
            "deferred_support": [
                "asymmetric_privileged_critic",
                "gate_phase_reset_buffer",
                "prioritized_level_replay",
                "recurrent_actor_gru256",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 1b clean PPO longer-rollout maturation",
            "baseline": "loop094/v31a 4M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Does the only currently promising clean-PPO branch improve if "
                "continued from its best 4M checkpoint with normalization disabled?"
            ),
            "evidence": {
                "loop094_best": "19/100 success, mean_gates 1.55, mean success time 6.876s",
                "loop095_v31b": "0/100 success from scratch with normalization",
                "loop096_v31c": (
                    "zero-update identity-normalization parity passed, but training "
                    "regressed to 0/100 success and 0.0 mean gates"
                ),
            },
            "success_screen": {
                "promising_for_more_maturation": (
                    "success > 0.19, or mean_gates materially above 1.55 with "
                    "nonzero success and lower crash rate"
                ),
                "reject_condition": (
                    "all milestones stay at or below loop094 best without new "
                    "success seeds or gate-progress expansion"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 46,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
        },
        "rationale": (
            "loop094/v31a is the only recent framework lane with nonzero Level3 "
            "hard-eval success after v30 semantics, reaching 19% at the 4M "
            "milestone. Both normalization lanes failed to preserve or improve "
            "that frontier, with v31c proving the identity warm-start itself is "
            "not destructive but normalization-enabled training is. Before "
            "implementing asymmetric privileged critic support, this lane gives "
            "the clean longer-rollout branch a bounded 15M maturation chunk with "
            "frequent milestone hard evals, while keeping the track, observation, "
            "reward numbers, PPO numbers, and deployed actor path fixed."
        ),
    },
    "v31d_longer_rollout_maturation_from_loop097_12m_to_30m": {
        "name": "v31d_longer_rollout_maturation_from_loop097_12m_to_30m",
        "proposal_name": "structural_v31d_longer_rollout_mature_loop097_12m_to_30m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 18_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 7,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "3,6,9,12,15,18",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP097_BEST_CHECKPOINT,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "requires_training_support": "v30_episode_semantics",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V31D_TO_30M_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP097_BEST_CHECKPOINT,
                "additional_train_steps": 18_000_000,
                "approx_cumulative_branch_steps": 30_000_000,
            },
            "semantic_repairs": [
                "same_step_finish_termination",
                "finish_bonus_once",
                "no_terminal_to_reset_dummy_transition",
                "per_slot_wrapper_reset",
                "true_observation_delay_reset",
                "termination_reason_logging",
            ],
            "changed_reward_numbers": [],
            "changed_training_numbers": ["train_timesteps", "initial_checkpoint"],
            "deferred_support": [
                "asymmetric_privileged_critic",
                "gate_phase_reset_buffer",
                "prioritized_level_replay",
                "recurrent_actor_gru256",
                "gate_acquisition_reward_adjustment",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 1c clean PPO maturation to 30M-style horizon",
            "baseline": "loop097/v31d 12M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Does the weakly improved clean-PPO branch continue gaining "
                "success seeds when matured from its 12M best checkpoint toward "
                "a 30M-style horizon, without changing reward numbers?"
            ),
            "evidence": {
                "loop094_v31a_best": "19/100 success, mean_gates 1.55, crash 81%",
                "loop097_v31d_best": "20/100 success, mean_gates 1.66, crash 80%",
                "reviewer_split": (
                    "Evaluator and structure reviewers favor same-hypothesis "
                    "maturation; W&B reviewer flags weak conversion and keeps "
                    "gate-acquisition reward adjustment as the next fallback."
                ),
            },
            "promotion_gate": {
                "continue_toward_60m": (
                    "success > 0.20, or mean_gates materially above 1.66 with "
                    "new success seeds or lower crash rate"
                ),
                "fallback_if_plateau": (
                    "reject same-hypothesis maturation and choose either a named "
                    "gate-acquisition reward-number lane or v32 trainer-support work"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 47,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
        },
        "rationale": (
            "loop097/v31d marginally but genuinely improved the clean-PPO frontier "
            "to 20% success and 1.66 mean gates from the 12M checkpoint. Under the "
            "Level2-calibrated step-curve policy, a branch with nonzero success and "
            "mean-gate expansion should receive a bounded maturation check before "
            "being rejected. This lane keeps v5 observation, loop052 reward/PPO "
            "numbers, corrected v30 semantics, no normalization, and unchanged "
            "config/level3.toml hard eval, while adding 18M more training steps "
            "from the loop097 12M best checkpoint."
        ),
    },
    "v32_asymmetric_privileged_critic_clean_ppo_5m": {
        "name": "v32_asymmetric_privileged_critic_clean_ppo_5m",
        "proposal_name": "structural_v32_asymmetric_privileged_critic_clean_ppo_5m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP097_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "asymmetric_privileged_critic_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V32_PRIVILEGED_CRITIC_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "critic_observation_mode": CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
            "critic_extra_state": [
                "drone position velocity angular_velocity rotation_matrix",
                "target_gate_progress",
                "all gate positions and quaternions",
                "all obstacle positions",
                "gate and obstacle visited flags",
            ],
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled for v32 parity lane",
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP097_BEST_CHECKPOINT,
            },
            "parity_gate_before_training": {
                "source_checkpoint": LOOP097_BEST_CHECKPOINT,
                "seed_split": "validation_unseen_101_200",
                "required": True,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 4 asymmetric privileged Critic",
            "baseline": "loop097/v31d 12M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can a Critic with training-only full-track state reduce noisy "
                "advantage estimates while the deployed Actor remains the exact "
                "v5 observation/history policy?"
            ),
            "success_screen": {
                "precondition": (
                    "zero-update actor parity against loop097/v31d 12M passes on "
                    "validation_unseen_101_200"
                ),
                "promising_for_maturation": (
                    "success > 0.20, or mean_gates materially above 1.66 with "
                    "new success seeds or lower crash rate"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 48,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
        },
        "rationale": (
            "loop098 rejected further clean-PPO longer-rollout maturation, and "
            "the framework packet ranks asymmetric privileged Critic as the next "
            "structural stage before curriculum, PLR, GRU, reward-number search, "
            "or speed pressure. This lane keeps the deployed Actor observation, "
            "action semantics, reward numbers, PPO numbers, rollout geometry, "
            "and final hard eval fixed, but lets the training Critic consume "
            "full-track state. It is runnable only after the zero-update Actor "
            "parity check passes."
        ),
    },
    "v32_asymmetric_privileged_critic_maturation_from_loop099_3m_to_18m": {
        "name": "v32_asymmetric_privileged_critic_maturation_from_loop099_3m_to_18m",
        "proposal_name": "structural_v32_privileged_critic_mature_loop099_3m_to_18m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 15_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "3,6,9,12,15",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP099_V32_BEST_CHECKPOINT,
        "allow_step_curve_maturation": True,
        "allow_repeat_params": True,
        "requires_training_support": "asymmetric_privileged_critic_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V32_MATURATION_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "critic_observation_mode": CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP099_V32_BEST_CHECKPOINT,
                "additional_train_steps": 15_000_000,
                "approx_cumulative_v32_steps": 18_000_000,
            },
            "changed_reward_numbers": [],
            "changed_training_numbers": ["train_timesteps", "initial_checkpoint"],
            "deferred_support": [
                "gate_phase_reset_buffer",
                "prioritized_level_replay",
                "recurrent_actor_gru256",
                "reward_number_search",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 4b asymmetric privileged Critic maturation",
            "baseline": "loop099/v32 3M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Was the first v32 privileged-Critic screen too short, or does "
                "the lane plateau around the loop097 frontier even after a "
                "bounded continuation from its best 3M checkpoint?"
            ),
            "evidence": {
                "loop097_global_best": "20/100 success, mean_gates 1.66, crash 80%, mean success time 7.055s",
                "loop099_v32_best": "19/100 success, mean_gates 1.66, crash 81%, mean success time 7.208s",
                "reviewer_split": (
                    "Structure reviewer favored bounded same-hypothesis "
                    "maturation; evaluator and W&B reviewers warned that v32 "
                    "did not yet expand the hard-eval frontier."
                ),
            },
            "promotion_gate": {
                "continue_toward_60m": (
                    "success > 0.20, or mean_gates materially above 1.66 with "
                    "new success seeds or lower crash rate"
                ),
                "fallback_if_plateau": (
                    "reject v32 maturation and write a named v33 support packet "
                    "for gate-phase reset curriculum or another source-backed "
                    "training-distribution change"
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 49,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_LEVEL3_FULL_STATE_V1,
        },
        "rationale": (
            "loop099/v32 did not beat the loop097 global best, but its 3M "
            "checkpoint matched the frontier mean-gate depth and remained close "
            "to the success frontier after only a short privileged-Critic screen. "
            "This continuation is a bounded test of the user's step-count concern: "
            "it starts from the loop099 3M best checkpoint, keeps v5 Actor "
            "observation, reward numbers, PPO numbers, rollout geometry, "
            "corrected v30 semantics, and unchanged config/level3.toml hard eval "
            "fixed, and changes only the training horizon. If it still fails to "
            "beat 20% success or expand mean gates, the next decision should stop "
            "v32 and move to a named gate-phase reset/curriculum support lane."
        ),
    },
    "v33_gate_phase_reset_curriculum_from_loop097_12m": {
        "name": "v33_gate_phase_reset_curriculum_from_loop097_12m",
        "proposal_name": "structural_v33_gate_phase_reset_curriculum_loop097_12m_10m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 10_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,5,8,10",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP097_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "gate_phase_reset_curriculum_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V33_GATE_PHASE_RESET_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "gate_phase_reset_prob",
                "gate_phase_reset_x_min",
                "gate_phase_reset_x_max",
                "gate_phase_reset_yz_max",
                "gate_phase_reset_speed_min",
                "gate_phase_reset_speed_max",
            ],
            "changed_reward_numbers": [],
            "curriculum": {
                "training_only": True,
                "normal_reset_probability": 0.55,
                "gate_phase_reset_probability": 0.45,
                "local_gate_x_range_m": [-1.05, -0.18],
                "local_gate_yz_abs_max_m": 0.16,
                "forward_speed_range_mps": [0.15, 1.20],
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP097_BEST_CHECKPOINT,
            },
            "deferred_support": [
                "prioritized_level_replay",
                "recurrent_actor_gru256",
                "reward_number_search",
                "speed_optimization",
            ],
        },
        "hypothesis": {
            "framework_stage": "Experiment 5 gate-phase reset curriculum",
            "baseline": "loop097/v31d 12M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Does exposing 45% of training episodes to randomized target-gate "
                "approach states improve gate acquisition and crash conversion "
                "after v32 privileged-Critic maturation failed to expand the "
                "loop097 hard-eval frontier?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.20, or mean_gates materially above 1.66 with "
                    "lower crash rate or new validation success seeds"
                ),
                "rollback": (
                    "If hard eval stays <=0.20 success with crash around 80% and "
                    "no stable mean-gate expansion, stop v33 and consider PLR or "
                    "GRU only through a new named packet."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 50,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "gate_phase_reset_prob": 0.45,
            "gate_phase_reset_x_min": -1.05,
            "gate_phase_reset_x_max": -0.18,
            "gate_phase_reset_yz_max": 0.16,
            "gate_phase_reset_speed_min": 0.15,
            "gate_phase_reset_speed_max": 1.20,
        },
        "rationale": (
            "loop100 rejected further v32 maturation: the best checkpoint reached "
            "only 19% success and did not beat the loop097 20% / 1.66-gate "
            "frontier. All three post-run reviewers recommended launching a "
            "named training-distribution lane rather than continuing v32, reward "
            "numbers, or W&B-reward-led tuning. This v33 screen keeps the "
            "deployed v5 Actor, reward numbers, PPO numbers, rollout geometry, "
            "and unchanged config/level3.toml hard eval fixed, but trains with "
            "a mixed reset distribution: most episodes still start normally, "
            "while 45% begin near randomized gate approach phases so the Actor "
            "gets more direct practice on acquire/pass/exit behavior."
        ),
    },
    "v34_lowprob_train_pool_plr_from_loop101": {
        "name": "v34_lowprob_train_pool_plr_from_loop101",
        "proposal_name": "structural_v34_lowprob_train_pool_plr_loop101_10m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 10_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,5,8,10",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "offline_train_pool_plr_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V34_TRAIN_POOL_PLR_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "track_generator_profile",
                "gate_phase_reset_prob",
                "gate_phase_reset_x_min",
                "gate_phase_reset_x_max",
                "gate_phase_reset_yz_max",
                "gate_phase_reset_speed_min",
                "gate_phase_reset_speed_max",
            ],
            "changed_reward_numbers": [],
            "offline_plr": {
                "training_only": True,
                "profile": "v34_lowprob_train_pool_bounds_plr",
                "replay_probability": 0.08,
                "source": (
                    "train_pool bounds-or-ground failures from the v28 "
                    "failure-correction probe; excludes dev_seen, "
                    "validation_unseen, and final_locked seeds"
                ),
                "normal_random_track_probability": 0.92,
            },
            "curriculum": {
                "training_only": True,
                "normal_reset_probability": 0.55,
                "gate_phase_reset_probability": 0.45,
                "local_gate_x_range_m": [-1.05, -0.18],
                "local_gate_yz_abs_max_m": 0.16,
                "forward_speed_range_mps": [0.15, 1.20],
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 6 offline prioritized level replay",
            "baseline": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "validation_seed_leakage": "forbidden",
            "primary_question": (
                "Does a low-probability train-pool prioritized track sampler, "
                "combined with the already-tested v33 gate-phase reset curriculum, "
                "expand validation-unseen seed coverage beyond the 20% success / "
                "1.69 mean-gate frontier?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.20, or success = 0.20 with stable mean_gates "
                    "above 1.80 and crash <= 0.80 plus new validation success seeds"
                ),
                "rollback": (
                    "If hard eval stays <=0.20 success with crash around 80% and "
                    "no stable mean-gate expansion, stop offline PLR and write a "
                    "new packet for online PLR/competence gating or GRU."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 51,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "v34_lowprob_train_pool_bounds_plr",
            "gate_phase_reset_prob": 0.45,
            "gate_phase_reset_x_min": -1.05,
            "gate_phase_reset_x_max": -0.18,
            "gate_phase_reset_yz_max": 0.16,
            "gate_phase_reset_speed_min": 0.15,
            "gate_phase_reset_speed_max": 1.20,
        },
        "rationale": (
            "loop101/v33 tied the old 20% success frontier and improved mean gates "
            "slightly to 1.69, with an 8M checkpoint reaching 1.81 mean gates, "
            "but crash stayed at 80% and W&B race metrics did not show real "
            "conversion. The next framework stage is prioritized level replay, "
            "not reward-number tuning. This v34 screen keeps the final Level3 "
            "track, deployed v5 Actor, reward numbers, PPO numbers, rollout "
            "geometry, and v33 gate-phase reset curriculum fixed, then adds only "
            "a low-probability training-only replay sampler over train-pool "
            "bounds-or-ground seeds. It deliberately excludes validation and "
            "final seeds and uses 8% replay so normal random Level3 tracks remain "
            "the dominant training distribution."
        ),
    },
    "v35_competence_gated_gate_phase_curriculum_from_loop101": {
        "name": "v35_competence_gated_gate_phase_curriculum_from_loop101",
        "proposal_name": "structural_v35_competence_gated_curriculum_loop101_10m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 10_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,5,8,10",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "competence_gated_gate_phase_curriculum_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V35_COMPETENCE_GATED_CURRICULUM_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "gate_phase_reset_prob",
                "gate_phase_reset_x_min",
                "gate_phase_reset_x_max",
                "gate_phase_reset_yz_max",
                "gate_phase_reset_speed_min",
                "gate_phase_reset_speed_max",
                "gate_phase_reset_competence_enabled",
                "gate_phase_reset_competence_start_prob",
                "gate_phase_reset_competence_step_prob",
                "gate_phase_reset_competence_min_passed_gate_rate",
                "gate_phase_reset_competence_min_finished_rate",
                "gate_phase_reset_competence_max_crashed_rate",
            ],
            "changed_reward_numbers": [],
            "curriculum": {
                "training_only": True,
                "normal_reset_probability_initial": 0.88,
                "normal_reset_probability_min": 0.55,
                "gate_phase_reset_probability_initial": 0.12,
                "gate_phase_reset_probability_max": 0.45,
                "gate_phase_reset_increment": 0.02,
                "competence_gate": {
                    "min_passed_gate_rate": 0.0068,
                    "min_finished_rate": 0.0007,
                    "max_crashed_rate": 0.0082,
                    "source": "rollout race metrics, updated once per PPO iteration",
                },
                "local_gate_x_range_m": [-1.05, -0.18],
                "local_gate_yz_abs_max_m": 0.16,
                "forward_speed_range_mps": [0.15, 1.20],
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 5b competence-gated gate-phase reset curriculum",
            "baseline": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "validation_seed_leakage": "forbidden",
            "primary_question": (
                "Can the loop101 policy keep its 20% validation-unseen frontier "
                "while gate-phase reset exposure is unlocked only when rollout "
                "finish/pass/crash competence signals are healthy?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.20, or mean_gates > 1.69 with crash <= 0.80 "
                    "and no late-checkpoint collapse"
                ),
                "rollback": (
                    "If all checkpoints are <=0.17 success, mean gates do not "
                    "expand, or crash rises to >=0.83, reject v35 and move to a "
                    "new packet for online PLR with competence gates or GRU."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 52,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "gate_phase_reset_prob": 0.45,
            "gate_phase_reset_x_min": -1.05,
            "gate_phase_reset_x_max": -0.18,
            "gate_phase_reset_yz_max": 0.16,
            "gate_phase_reset_speed_min": 0.15,
            "gate_phase_reset_speed_max": 1.20,
            "gate_phase_reset_competence_enabled": True,
            "gate_phase_reset_competence_start_prob": 0.12,
            "gate_phase_reset_competence_step_prob": 0.02,
            "gate_phase_reset_competence_min_passed_gate_rate": 0.0068,
            "gate_phase_reset_competence_min_finished_rate": 0.0007,
            "gate_phase_reset_competence_max_crashed_rate": 0.0082,
        },
        "rationale": (
            "loop102/v34 showed that even an 8% train-pool failure replay sampler "
            "can create negative transfer: best hard eval fell to 17% success, "
            "1.59 mean gates, and 83% crash, with final collapsing to 10%. "
            "All three reviewers rejected continuing offline PLR as-is and "
            "recommended returning to loop101 final. v35 keeps the final Level3 "
            "track, deployed v5 Actor, reward numbers, PPO numbers, rollout "
            "geometry, and normal random track sampler fixed. It changes only "
            "the gate-phase reset curriculum schedule: start at 12% reset "
            "exposure and increase toward the proven 45% ceiling only when "
            "rollout pass/finish/crash metrics indicate the policy is not "
            "forgetting the base task."
        ),
    },
    "v36_online_competence_gated_level_replay_from_loop101": {
        "name": "v36_online_competence_gated_level_replay_from_loop101",
        "proposal_name": "structural_v36_online_level_replay_loop101_10m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 10_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,5,8,10",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "online_competence_gated_level_replay_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V36_ONLINE_LEVEL_REPLAY_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "online_level_replay_profile",
                "online_level_replay_prob",
                "online_level_replay_competence_enabled",
                "online_level_replay_competence_start_prob",
                "online_level_replay_competence_step_prob",
                "online_level_replay_competence_min_passed_gate_rate",
                "online_level_replay_competence_min_finished_rate",
                "online_level_replay_competence_max_crashed_rate",
                "gate_phase_reset_prob",
                "gate_phase_reset_x_min",
                "gate_phase_reset_x_max",
                "gate_phase_reset_yz_max",
                "gate_phase_reset_speed_min",
                "gate_phase_reset_speed_max",
                "gate_phase_reset_competence_enabled",
                "gate_phase_reset_competence_start_prob",
                "gate_phase_reset_competence_step_prob",
                "gate_phase_reset_competence_min_passed_gate_rate",
                "gate_phase_reset_competence_min_finished_rate",
                "gate_phase_reset_competence_max_crashed_rate",
            ],
            "changed_reward_numbers": [],
            "online_level_replay": {
                "training_only": True,
                "profile": "v36_train_pool_bounds_gate0_gate2",
                "replay_probability_initial": 0.03,
                "replay_probability_max": 0.08,
                "replay_probability_increment": 0.01,
                "source": (
                    "audited train_pool bounds-or-ground failures from the v28 "
                    "failure-correction probe; excludes dev_seen, "
                    "validation_unseen, and final_locked seeds"
                ),
                "competence_gate": {
                    "min_passed_gate_rate": 0.0065,
                    "min_finished_rate": 0.0005,
                    "max_crashed_rate": 0.0082,
                    "source": "rollout race metrics, updated once per PPO iteration",
                },
                "normal_random_track_probability_initial": 0.97,
                "normal_random_track_probability_min": 0.92,
            },
            "curriculum": {
                "training_only": True,
                "normal_reset_probability_initial": 0.88,
                "normal_reset_probability_min": 0.55,
                "gate_phase_reset_probability_initial": 0.12,
                "gate_phase_reset_probability_max": 0.45,
                "gate_phase_reset_increment": 0.02,
                "competence_gate": {
                    "min_passed_gate_rate": 0.0068,
                    "min_finished_rate": 0.0007,
                    "max_crashed_rate": 0.0082,
                    "source": "rollout race metrics, updated once per PPO iteration",
                },
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 6b online competence-gated level replay",
            "baseline": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "validation_seed_leakage": "forbidden",
            "primary_question": (
                "Can a train-pool-only level replay wrapper improve the 20% "
                "validation-unseen frontier if replay pressure starts at 3% "
                "and only rises toward the old v34 8% ceiling when rollout "
                "competence is healthy?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.20, or mean_gates > 1.69 with crash <= 0.80 "
                    "and no late-checkpoint collapse"
                ),
                "rollback": (
                    "If the 10M screen is <=0.20 success with mean_gates <=1.69 "
                    "or crash >=0.81, reject v36 and write a GRU transfer or "
                    "memory-structure packet instead of replay-probability tuning."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 53,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "online_level_replay_profile": "v36_train_pool_bounds_gate0_gate2",
            "online_level_replay_prob": 0.08,
            "online_level_replay_competence_enabled": True,
            "online_level_replay_competence_start_prob": 0.03,
            "online_level_replay_competence_step_prob": 0.01,
            "online_level_replay_competence_min_passed_gate_rate": 0.0065,
            "online_level_replay_competence_min_finished_rate": 0.0005,
            "online_level_replay_competence_max_crashed_rate": 0.0082,
            "gate_phase_reset_prob": 0.45,
            "gate_phase_reset_x_min": -1.05,
            "gate_phase_reset_x_max": -0.18,
            "gate_phase_reset_yz_max": 0.16,
            "gate_phase_reset_speed_min": 0.15,
            "gate_phase_reset_speed_max": 1.20,
            "gate_phase_reset_competence_enabled": True,
            "gate_phase_reset_competence_start_prob": 0.12,
            "gate_phase_reset_competence_step_prob": 0.02,
            "gate_phase_reset_competence_min_passed_gate_rate": 0.0068,
            "gate_phase_reset_competence_min_finished_rate": 0.0007,
            "gate_phase_reset_competence_max_crashed_rate": 0.0082,
        },
        "rationale": (
            "loop103/v35 did not beat the loop101 frontier and its gate-phase "
            "competence gate never opened, while loop102/v34 showed that a "
            "static 8% train-pool replay sampler caused negative transfer. "
            "v36 therefore keeps the loop101 checkpoint, v5 Actor observation, "
            "MLP policy, reward numbers, PPO numbers, default random Level3 "
            "track generator, and unchanged config/level3.toml hard eval. It "
            "adds only a training-time replay wrapper whose train-pool seed "
            "pressure starts below v34 and is increased online only when rollout "
            "pass/finish/crash metrics are healthy."
        ),
    },
    "v37_gru_transfer_memory_structure_from_loop101": {
        "name": "v37_gru_transfer_memory_structure_from_loop101",
        "proposal_name": "structural_v37_gru_transfer_memory_loop101_preflight",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,5",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "mlp_to_gru_transfer_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V37_GRU_TRANSFER_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "policy_arch",
                "recurrent_hidden_dim",
                "recurrent_sequence_len",
                "mlp_to_gru_transfer",
            ],
            "changed_reward_numbers": [],
            "transfer": {
                "source_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
                "source_policy_arch": "mlp_2x_tanh",
                "target_policy_arch": "mlp_residual_recurrent_actor_gru256",
                "preflight_packet": V37_GRU_TRANSFER_PREFLIGHT_PACKET,
                "required_before_training": [
                    "MLP-to-GRU initialization support",
                    "hidden-state reset checks on episode boundaries",
                    "sequence rollout and BPTT checks",
                    "checkpoint metadata checks",
                    "ppo_level3_inference recurrent hidden-state reset checks",
                    "bounded zero-update or deterministic parity packet",
                ],
                "reason": (
                    "old from-scratch GRU evidence was poor, so the next GRU "
                    "lane must preserve useful loop101 behavior instead of "
                    "blindly restarting memory training"
                ),
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "sequence_len": 128,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 7a GRU transfer memory preflight",
            "baseline": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can a recurrent Actor with GRU-256 memory preserve useful "
                "loop101 behavior through explicit MLP-to-GRU transfer, then "
                "improve gate acquisition on the partially observable Level3 "
                "task?"
            ),
            "preflight_gate": {
                "required": (
                    "Do not launch training until transfer support, reset "
                    "semantics, sequence updates, metadata, and inference "
                    "hidden-state handling have focused tests and a dry-run "
                    "or parity packet."
                ),
                "rollback": (
                    "If transfer cannot preserve useful deterministic behavior "
                    "from loop101, hold for a GRU distillation or memory "
                    "pretraining packet instead of launching training."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 54,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 128,
        },
        "rationale": (
            "loop106/v36 did not improve the loop101 frontier: best hard eval "
            "was only a 20% success tie with lower mean gates and slower "
            "successful time, and final collapsed to 14% success with 86% "
            "crash. The replay and curriculum gates did not open, and all "
            "three reviewers recommended rejecting replay tuning. v37 therefore "
            "moves to the next roadmap mechanism, recurrent memory, but it is "
            "held before training until explicit MLP-to-GRU transfer and reset "
            "parity support exists."
        ),
    },
    "v37b_residual_gru_maturation_from_loop107_1m": {
        "name": "v37b_residual_gru_maturation_from_loop107_1m",
        "proposal_name": "structural_v37b_residual_gru_mature_loop107_1m_2m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 2_000_000,
        "checkpoint_interval": 500_000,
        "max_eval_checkpoints": 4,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "0.5,1,1.5,2",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP107_V37_1M_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "mlp_to_gru_transfer_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V37B_LOOP107_1M_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "initial_checkpoint",
                "train_timesteps",
                "checkpoint_interval",
                "eval_milestones_m",
            ],
            "changed_reward_numbers": [],
            "transfer": {
                "source_checkpoint": LOOP107_V37_1M_CHECKPOINT,
                "source_policy_arch": "mlp_residual_recurrent_actor_gru256",
                "target_policy_arch": "mlp_residual_recurrent_actor_gru256",
                "preflight_packet": V37_GRU_TRANSFER_PREFLIGHT_PACKET,
                "decision_packet": V37B_LOOP107_1M_DECISION_PACKET,
                "reason": (
                    "loop107 showed a small hard-eval signal at 1M, followed "
                    "by drift. v37b tests whether that 1M checkpoint can be "
                    "stabilized over a short continuation with dense milestone "
                    "evaluation."
                ),
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "sequence_len": 128,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP107_V37_1M_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 7b residual-GRU 1M maturation",
            "baseline": "loop107/v37 1M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can the only promising residual-GRU checkpoint, loop107 1M, "
                "be stabilized or improved without drifting into the later "
                "loop107 failures?"
            ),
            "rollback": (
                "If this short continuation does not reproduce or improve "
                "21% success and 1.66 mean gates, retire plain v37 and propose "
                "a named retention/distillation GRU lane."
            ),
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 55,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 128,
        },
        "rationale": (
            "loop107/v37 produced the current corrected-loop success best at "
            "1M with 21% success and 79% crash, but later checkpoints drifted "
            "down to 15%, 12%, 12%, and 17% success. The three post-run "
            "reviewers agreed not to continue from final and not to tune reward "
            "numbers immediately. v37b therefore starts from loop107 1M and "
            "runs only a dense 2M continuation to test whether the early signal "
            "is stable before escalating to retention/distillation."
        ),
    },
    "v38_gru_teacher_retention_distillation_from_loop107_1m": {
        "name": "v38_gru_teacher_retention_distillation_from_loop107_1m",
        "proposal_name": "structural_v38_gru_teacher_retention_loop107_1m_preflight",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 2_000_000,
        "checkpoint_interval": 500_000,
        "max_eval_checkpoints": 4,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "0.5,1,1.5,2",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP107_V37_1M_CHECKPOINT,
        "allow_repeat_params": True,
        "requires_training_support": "residual_gru_teacher_retention_support",
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V38_RETENTION_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "teacher_retention_distillation",
                "initial_checkpoint",
                "checkpoint_interval",
                "eval_milestones_m",
            ],
            "changed_reward_numbers": [],
            "teacher_retention": {
                "student_start_checkpoint": LOOP107_V37_1M_CHECKPOINT,
                "teacher_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
                "teacher_policy_arch": "mlp_2x_tanh",
                "student_policy_arch": "mlp_residual_recurrent_actor_gru256",
                "required_before_training": [
                    "teacher-retention dataset or online teacher sampling",
                    "residual-GRU recurrent minibatch retention loss",
                    "metadata recording teacher checkpoint and observation layout",
                    "nonzero retention/sampled_batch_size logging",
                    "finite teacher_kl, teacher_action_mse, and teacher_agreement logging",
                    "zero-update or deterministic preflight packet",
                ],
                "reason": (
                    "loop108 failed to reproduce loop107 1M and retention "
                    "metrics were inactive, so v38 must prove retention is "
                    "actually sampled and logged before training."
                ),
            },
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "sequence_len": 128,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP107_V37_1M_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 8 GRU teacher retention preflight",
            "baseline": "loop107/v37 1M",
            "teacher": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can explicit teacher retention prevent the residual-GRU "
                "student from drifting below the loop107 1M hard-eval frontier?"
            ),
            "preflight_gate": (
                "Do not launch training until tests prove retention is "
                "sampled, logged, and compatible with recurrent PPO updates."
            ),
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 56,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "policy_arch": "mlp_residual_recurrent_actor_gru256",
            "recurrent_hidden_dim": 256,
            "recurrent_sequence_len": 128,
            "v27_teacher_kl_beta": 0.08,
            "v27_teacher_model_name": LOOP101_V33_BEST_CHECKPOINT,
            "v27_teacher_observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        },
        "rationale": (
            "loop108/v37b failed the explicit reproduction test: best hard "
            "eval was only 18% success, 1.58 mean gates, and 82% crash, below "
            "both loop107 1M and the loop101 gate frontier. Reviewers agreed "
            "plain residual-GRU continuation should stop and the next step "
            "should be a held v38 preflight for explicit teacher retention or "
            "distillation from the stable frontier."
        ),
    },
    "v39_feedforward_gate_acquisition_reward_rebalance_loop101_final": {
        "name": "v39_feedforward_gate_acquisition_reward_rebalance_loop101_final",
        "proposal_name": "structural_v39_feedforward_gate_acquisition_reward_loop101_5m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 5_000_000,
        "checkpoint_interval": 1_000_000,
        "max_eval_checkpoints": 5,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "1,2,3,4,5",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
        "allow_repeat_params": True,
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V39_GATE_ACQUISITION_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "initial_checkpoint",
                "checkpoint_interval",
                "eval_milestones_m",
            ],
            "changed_reward_numbers": [
                "gate_stage_coef",
                "gate_axis_coef",
                "gate_front_bonus",
                "gate_bonus",
                "gate_back_bonus",
                "finish_bonus",
                "time_penalty",
            ],
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP101_V33_BEST_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 9 feed-forward gate-acquisition reward screen",
            "baseline": "loop101/v33 final",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "After GRU retention preserved teacher behavior but failed to "
                "improve hard eval, can the stable feed-forward frontier improve "
                "gate acquisition using stronger gate-axis/stage/bonus shaping "
                "and slightly lower time pressure?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.21, or success >= 0.20 with mean_gates > 1.69 "
                    "and crash <= 0.80, or clear new validation success-seed "
                    "coverage without worse crash"
                ),
                "rollback": (
                    "If hard eval stays below 20% success, mean_gates below "
                    "1.69, or crash remains above 80%, reject this reward "
                    "screen instead of continuing from its checkpoints."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 57,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "policy_arch": "mlp_2x_tanh",
            "gate_stage_coef": 13.0,
            "gate_axis_coef": 24.0,
            "gate_front_bonus": 5.0,
            "gate_bonus": 200.0,
            "gate_back_bonus": 35.0,
            "finish_bonus": 175.0,
            "time_penalty": 0.02,
        },
        "rationale": (
            "loop109/v38 proved online teacher retention was active but did not "
            "convert to hard-eval progress: best was 18% success, 1.64 mean "
            "gates, and 82% crash, below both loop107 1M and loop101 final. "
            "The analyzer diagnosed gate acquisition and proposed stronger "
            "gate-stage/axis/bonus shaping with slightly lower time pressure. "
            "v39 returns to the stable feed-forward loop101 checkpoint, keeps "
            "the v5 observation, PPO architecture, rollout geometry, and "
            "unchanged config/level3.toml fixed, and tests only that "
            "gate-acquisition reward-number hypothesis."
        ),
    },
    "v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m": {
        "name": "v39b_feedforward_gate_acquisition_seed_expansion_from_loop110_3m",
        "proposal_name": "structural_v39b_feedforward_gate_acquisition_loop110_3m_3m",
        "config": TARGET_EVAL_CONFIG,
        "eval_config": TARGET_EVAL_CONFIG,
        "observation_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
        "train_timesteps": 3_000_000,
        "checkpoint_interval": 500_000,
        "max_eval_checkpoints": 6,
        "eval_seed_split": "validation_unseen",
        "eval_checkpoint_strategy": "milestone",
        "eval_milestones_m": "0.5,1,1.5,2,2.5,3",
        "num_envs": 256,
        "num_steps": 128,
        "initial_checkpoint": LOOP110_V39_3M_CHECKPOINT,
        "allow_repeat_params": True,
        "research_packet": LEVEL3_FRAMEWORK_STRUCTURAL_PLAN_PACKET,
        "approved_hypothesis_packet": V39B_LOOP110_3M_DECISION_PACKET,
        "architecture": {
            "deployment_policy": "end_to_end_ppo_actor",
            "policy_arch": "mlp_2x_tanh",
            "policy_distribution": "legacy_normal_action_for_A_control",
            "actor_obs_layout": LOCAL_OBSTACLE_OBSERVATION_LAYOUT,
            "actor_output": "roll_pitch_yaw_thrust",
            "normalization": "disabled",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "track_geometry_change": "forbidden",
            "changed_training_numbers": [
                "initial_checkpoint",
                "train_timesteps",
                "checkpoint_interval",
                "eval_milestones_m",
            ],
            "changed_reward_numbers": [],
            "continues_hypothesis": (
                "v39_feedforward_gate_acquisition_reward_rebalance_loop101_final"
            ),
            "rollout_structure": {
                "num_envs": 256,
                "num_steps": 128,
                "batch_size": 32768,
                "control_horizon_s": 2.56,
                "continues_checkpoint": LOOP110_V39_3M_CHECKPOINT,
            },
        },
        "hypothesis": {
            "framework_stage": "Experiment 9b feed-forward gate-acquisition maturation",
            "baseline": "loop110/v39 3M",
            "train_config": TARGET_EVAL_CONFIG,
            "hard_eval_config": TARGET_EVAL_CONFIG,
            "deployment_actor_only": True,
            "track_geometry_change": "forbidden",
            "primary_question": (
                "Can the v39 3M checkpoint's success-rate tie, faster "
                "successful time, and validation seed redistribution reproduce "
                "or improve under a short same-hypothesis continuation?"
            ),
            "promotion_gate": {
                "promising_for_maturation": (
                    "success > 0.21, success >= 0.21 with mean_gates > 1.66, "
                    "or success >= 0.20 with mean_gates > 1.69 and crash <= 0.80"
                ),
                "rollback": (
                    "Reject v39 if the continuation drifts below 20% success, "
                    "stays <=1.64 mean_gates with about 80% contact crashes, "
                    "or repeats loop110's late-checkpoint collapse."
                ),
            },
        },
        "params": {
            **LOOP052_REMOTE_NOMINAL_PARAMS,
            "seed": 58,
            "obs_norm_enabled": False,
            "return_norm_enabled": False,
            "critic_observation_mode": CRITIC_OBSERVATION_SAME_AS_ACTOR,
            "track_generator_profile": "default",
            "policy_arch": "mlp_2x_tanh",
            "gate_stage_coef": 13.0,
            "gate_axis_coef": 24.0,
            "gate_front_bonus": 5.0,
            "gate_bonus": 200.0,
            "gate_back_bonus": 35.0,
            "finish_bonus": 175.0,
            "time_penalty": 0.02,
        },
        "rationale": (
            "loop110/v39 tied the current 21% success / 79% crash frontier at "
            "its 3M checkpoint, improved successful time to 6.756s, and solved "
            "8 validation seeds not solved by loop107 1M, but it did not improve "
            "mean gates and later checkpoints regressed. All three reviewers "
            "recommended a bounded same-hypothesis continuation from loop110 "
            "3M before changing reward numbers again. v39b keeps the exact v39 "
            "reward numbers, MLP policy, v5 observation, rollout geometry, and "
            "unchanged config/level3.toml fixed."
        ),
    },
}

FIRE_PARAM_KEYS = [
    "seed",
    "learning_rate",
    "anneal_lr",
    "gamma",
    "gae_lambda",
    "update_epochs",
    "num_minibatches",
    "clip_coef",
    "clip_vloss",
    "ent_coef",
    "vf_coef",
    "max_grad_norm",
    "target_kl",
    "hidden_dim",
    "policy_arch",
    "critic_observation_mode",
    "recurrent_hidden_dim",
    "recurrent_sequence_len",
    "n_obs",
    "action_rp_limit_deg",
    "action_lowpass_alpha",
    "reward_structure",
    "track_generator_profile",
    "online_level_replay_profile",
    "online_level_replay_prob",
    "online_level_replay_competence_enabled",
    "online_level_replay_competence_start_prob",
    "online_level_replay_competence_step_prob",
    "online_level_replay_competence_min_passed_gate_rate",
    "online_level_replay_competence_min_finished_rate",
    "online_level_replay_competence_max_crashed_rate",
    "gate_phase_reset_prob",
    "gate_phase_reset_x_min",
    "gate_phase_reset_x_max",
    "gate_phase_reset_yz_max",
    "gate_phase_reset_speed_min",
    "gate_phase_reset_speed_max",
    "gate_phase_reset_competence_enabled",
    "gate_phase_reset_competence_start_prob",
    "gate_phase_reset_competence_step_prob",
    "gate_phase_reset_competence_min_passed_gate_rate",
    "gate_phase_reset_competence_min_finished_rate",
    "gate_phase_reset_competence_max_crashed_rate",
    "v27_teacher_kl_beta",
    "v27_teacher_model_name",
    "v27_teacher_observation_layout",
    "v27_retention_dataset_path",
    "v27_retention_batch_size",
    "v27_lane_name",
    "obs_norm_enabled",
    "obs_norm_clip",
    "return_norm_enabled",
    "return_norm_clip",
    "progress_coef",
    "gate_stage_coef",
    "gate_axis_coef",
    "near_gate_coef",
    "gate_bonus",
    "gate_front_bonus",
    "gate_plane_bonus",
    "gate_back_bonus",
    "finish_bonus",
    "missed_gate_penalty",
    "gate_frame_pressure_coef",
    "wrong_side_penalty",
    "crash_penalty",
    "obstacle_coef",
    "obstacle_margin",
    "obstacle_clearance_coef",
    "timeout_penalty",
    "time_penalty",
    "act_coef",
    "d_act_th_coef",
    "d_act_xy_coef",
    "cmd_tilt_coef",
    "rpy_coef",
    "tilt_limit_deg",
    "tilt_excess_coef",
]

TUNABLE_REWARD_PARAM_KEYS = [
    "gate_stage_coef",
    "gate_axis_coef",
    "gate_bonus",
    "gate_front_bonus",
    "gate_back_bonus",
    "finish_bonus",
    "wrong_side_penalty",
    "crash_penalty",
    "obstacle_coef",
    "obstacle_margin",
    "timeout_penalty",
    "time_penalty",
    "act_coef",
    "d_act_th_coef",
    "d_act_xy_coef",
    "cmd_tilt_coef",
    "rpy_coef",
    "tilt_limit_deg",
    "tilt_excess_coef",
]

FLOAT_SUMMARY_FIELDS = {
    "success_rate",
    "success_ci95_low",
    "success_ci95_high",
    "crash_rate",
    "timeout_rate",
    "mean_gates",
    "mean_time_s_success",
    "median_time_s_success",
    "p90_time_s_success",
    "mean_smooth_penalty_per_step",
    "mean_action_delta_l2",
    "mean_max_tilt_deg",
    "worst_tilt_deg",
    "tilt_over_limit_frac",
    "mean_max_cmd_tilt_deg",
    "worst_cmd_tilt_deg",
    "cmd_tilt_over_limit_frac",
}
INT_SUMMARY_FIELDS = {"episodes", "success_count"}


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_state(path: Path) -> dict[str, Any]:
    """Load loop state, creating the default shape when it is absent."""
    now = utc_now()
    if not path.exists():
        return {
            "schema_version": 2,
            "created_at": now,
            "updated_at": now,
            "target": {
                "success_rate": TARGET_SUCCESS_RATE,
                "mean_time_s_success": TARGET_TIME_S,
            },
            "best": None,
            "best_dev": None,
            "best_validation": None,
            "final_candidate": None,
            "final_certified": None,
            "pending_post_run_decision": None,
            "research_packets": [],
            "autonomy_policy": deepcopy(DEFAULT_AUTONOMY_POLICY),
            "trials": [],
        }
    try:
        with path.open() as handle:
            state = json.load(handle)
    except json.JSONDecodeError as exc:
        if path.read_text().strip():
            raise SystemExit(f"error: state file is not valid JSON: {path}") from exc
        state = {
            "schema_version": 2,
            "created_at": now,
            "updated_at": now,
            "target": {
                "success_rate": TARGET_SUCCESS_RATE,
                "mean_time_s_success": TARGET_TIME_S,
            },
            "best": None,
            "best_dev": None,
            "best_validation": None,
            "final_candidate": None,
            "final_certified": None,
            "pending_post_run_decision": None,
            "research_packets": [],
            "autonomy_policy": deepcopy(DEFAULT_AUTONOMY_POLICY),
            "trials": [],
        }
    state.setdefault("schema_version", 1)
    state.setdefault("created_at", utc_now())
    state.setdefault(
        "target", {"success_rate": TARGET_SUCCESS_RATE, "mean_time_s_success": TARGET_TIME_S}
    )
    state.setdefault("best", None)
    state.setdefault("best_dev", None)
    state.setdefault("best_validation", None)
    state.setdefault("final_candidate", None)
    state.setdefault("final_certified", None)
    state.setdefault("pending_post_run_decision", None)
    state.setdefault("research_packets", [])
    autonomy_policy = deepcopy(DEFAULT_AUTONOMY_POLICY)
    if isinstance(state.get("autonomy_policy"), dict):
        autonomy_policy.update(state["autonomy_policy"])
    approval = state.get("structural_search_approval")
    if isinstance(approval, dict) and approval.get("status") == "approved_by_user":
        autonomy_policy.update(
            {
                "reward_only_first": False,
                "structural_changes_stage": "active_structural_search",
                "structural_changes_require_detailed_escalation_packet": False,
                "may_choose_structural_next_run_without_per_run_user_confirmation": True,
                "reward_scope": (
                    "open structural search; hard eval target remains "
                    f"config/{TARGET_EVAL_CONFIG}"
                ),
            }
        )
    state["autonomy_policy"] = autonomy_policy
    state.setdefault("trials", [])
    return state


def write_state(path: Path, state: dict[str, Any]) -> None:
    """Persist loop state as pretty JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = utc_now()
    if state.get("created_at") is None:
        state["created_at"] = state["updated_at"]
    with path.open("w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Parse finite floats, returning default for empty or NaN values."""
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def command_text(command: list[str]) -> str:
    """Return a shell-copyable command string."""
    return " ".join(shlex.quote(part) for part in command)


def checkpoint_step(path: Path) -> int:
    """Extract the numeric training step from a checkpoint file name."""
    stem = path.stem
    if "_step_" not in stem:
        return -1
    try:
        return int(stem.rsplit("_step_", 1)[1])
    except ValueError:
        return -1


def parse_steps_m(value: str) -> list[int]:
    """Parse comma-separated checkpoint milestones in millions into steps."""
    steps: list[int] = []
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        try:
            step = int(float(item) * 1_000_000)
        except ValueError as exc:
            raise ValueError(f"Invalid milestone step in millions: {item!r}.") from exc
        if step > 0 and step not in steps:
            steps.append(step)
    return sorted(steps)


def latest_initial_checkpoint() -> Path | None:
    """Return the latest checked-in level3 initial checkpoint, if present."""
    checkpoints = sorted(DEFAULT_INITIAL_DIR.glob("*_step_*.ckpt"), key=checkpoint_step)
    return checkpoints[-1] if checkpoints else None


def existing_path(value: str | None) -> Path | None:
    """Resolve a user-provided path and require it to exist."""
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise FileNotFoundError(path)
    return path.resolve()


def _checkpoint_input_dim(model_state_dict: dict[str, Any]) -> int:
    """Return the actor observation dimension for a Level3 PPO checkpoint."""
    if "actor_mean.0.weight" in model_state_dict:
        return int(model_state_dict["actor_mean.0.weight"].shape[1])
    if "actor_pre.0.weight" in model_state_dict:
        return int(model_state_dict["actor_pre.0.weight"].shape[1])
    raise ValueError("Cannot infer checkpoint actor observation dimension.")


def materialize_identity_norm_warmstart(
    hypothesis: dict[str, Any] | None,
    params: dict[str, Any],
) -> Path | None:
    """Create a checkpoint that preserves raw Actor behavior under identity normalization."""
    if hypothesis is None:
        return None
    spec = hypothesis.get("identity_norm_warmstart")
    if not isinstance(spec, dict):
        return None
    source = existing_path(str(spec["source_checkpoint"]))
    target = Path(str(spec["target_checkpoint"])).expanduser()
    if not target.is_absolute():
        target = ROOT / target
    if target.exists():
        return target.resolve()

    import torch

    from lsy_drone_racing.control.ppo_level3_observation import (
        checkpoint_action_lowpass_alpha,
        checkpoint_action_rp_limit_deg,
        checkpoint_hidden_dim,
        checkpoint_policy_arch,
        checkpoint_recurrent_hidden_dim,
        make_checkpoint,
        unpack_checkpoint,
    )

    checkpoint = torch.load(source, map_location="cpu")
    model_state_dict, observation_layout = unpack_checkpoint(checkpoint)
    policy_arch = checkpoint_policy_arch(checkpoint, model_state_dict)
    obs_dim = _checkpoint_input_dim(model_state_dict)
    obs_clip = float(params.get("obs_norm_clip", 10.0))
    return_clip = float(params.get("return_norm_clip", 10.0))
    obs_count = float(spec.get("obs_count", 1_000_000.0))
    return_count = float(spec.get("return_count", 1_000_000.0))
    obs_normalization = {
        "enabled": True,
        "mean": [0.0] * obs_dim,
        "var": [1.0] * obs_dim,
        "count": obs_count,
        "clip": obs_clip,
        "epsilon": 1e-4,
        "init_mode": "identity_warmstart",
        "source_checkpoint": checkpoint_reference(source),
    }
    return_normalization = (
        {
            "enabled": True,
            "mean": 0.0,
            "var": 1.0,
            "count": return_count,
            "clip": return_clip,
            "epsilon": 1e-4,
            "init_mode": "identity_warmstart",
            "source_checkpoint": checkpoint_reference(source),
        }
        if params.get("return_norm_enabled")
        else None
    )
    wrapped = make_checkpoint(
        model_state_dict,
        hidden_dim=checkpoint_hidden_dim(checkpoint, model_state_dict),
        observation_layout=observation_layout,
        action_rp_limit_deg=checkpoint_action_rp_limit_deg(checkpoint),
        action_lowpass_alpha=checkpoint_action_lowpass_alpha(checkpoint),
        policy_arch=policy_arch,
        recurrent_hidden_dim=checkpoint_recurrent_hidden_dim(checkpoint, model_state_dict),
        recurrent_sequence_len=(
            int(checkpoint["recurrent_sequence_len"])
            if isinstance(checkpoint, dict) and checkpoint.get("recurrent_sequence_len")
            else None
        ),
        obs_normalization=obs_normalization,
        return_normalization=return_normalization,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(wrapped, target)
    print(
        "materialized identity-normalized warm-start checkpoint "
        f"{checkpoint_reference(target)} from {checkpoint_reference(source)}"
    )
    return target.resolve()


def best_checkpoint_for_observation_layout(
    state: dict[str, Any],
    observation_layout: str,
    hidden_dim: int | None = None,
) -> Path | None:
    """Return the best evaluated checkpoint recorded for an observation layout/width."""
    candidates: list[tuple[tuple[float, float, float, float, float, float], Path]] = []
    for trial in evaluated_trials(state):
        trial_layout = trial.get("observation_layout") or WORLD_HISTORY_OBSERVATION_LAYOUT
        if trial_layout != observation_layout:
            continue
        if hidden_dim is not None:
            trial_params = trial.get("params")
            trial_hidden_dim = (
                safe_float(trial_params.get("hidden_dim"))
                if isinstance(trial_params, dict)
                else None
            )
            if trial_hidden_dim is None or int(trial_hidden_dim) != int(hidden_dim):
                continue
        summary = best_summary_for_trial(trial)
        if not isinstance(summary, dict):
            continue
        checkpoint_file = summary.get("checkpoint_file")
        if not checkpoint_file:
            continue
        path = ROOT / str(checkpoint_file)
        if path.exists():
            candidates.append((evaluation_rank_key(summary), path.resolve()))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def choose_initial_checkpoint(
    args: argparse.Namespace,
    state: dict[str, Any],
    params: dict[str, int | float],
) -> Path | None:
    """Choose the checkpoint to initialize the next trial from."""
    if args.from_scratch:
        return None

    explicit = existing_path(args.initial_checkpoint)
    if explicit is not None:
        return explicit

    if not args.resume_from_best:
        return latest_initial_checkpoint()

    target_hidden_dim = safe_float(params.get("hidden_dim"))
    matching_best = best_checkpoint_for_observation_layout(
        state,
        args.observation_layout,
        hidden_dim=int(target_hidden_dim) if target_hidden_dim is not None else None,
    )
    if matching_best is not None:
        return matching_best

    best = state.get("best")
    best_layout = best.get("observation_layout") if isinstance(best, dict) else None
    if (
        isinstance(best, dict)
        and args.observation_layout == WORLD_HISTORY_OBSERVATION_LAYOUT
        and best_layout in (None, WORLD_HISTORY_OBSERVATION_LAYOUT)
    ):
        checkpoint_file = best.get("checkpoint_file")
        if checkpoint_file:
            path = ROOT / str(checkpoint_file)
            if path.exists():
                return path.resolve()

    if args.observation_layout != WORLD_HISTORY_OBSERVATION_LAYOUT:
        raise FileNotFoundError(
            f"No evaluated checkpoint found for observation layout {args.observation_layout}; "
            "use --from-scratch."
        )

    return latest_initial_checkpoint()


def param_bounds(relaxed: bool) -> dict[str, tuple[float, float]]:
    """Return active reward parameter bounds."""
    return RELAXED_PARAM_BOUNDS if relaxed else PARAM_BOUNDS


def clamp_params(
    params: dict[str, int | float],
    *,
    relaxed: bool = False,
) -> dict[str, int | float]:
    """Clamp tunable parameters into conservative bounds."""
    clamped = dict(params)
    for key, (lower, upper) in param_bounds(relaxed).items():
        if key in clamped:
            value = float(clamped[key])
            clamped[key] = round(min(max(value, lower), upper), 6)
    for key in (
        "update_epochs",
        "num_minibatches",
        "hidden_dim",
        "recurrent_hidden_dim",
        "recurrent_sequence_len",
        "seed",
        "n_obs",
        "v27_retention_batch_size",
    ):
        if key in clamped:
            clamped[key] = int(clamped[key])
    for key in BOOL_PARAM_KEYS:
        if key in clamped:
            clamped[key] = bool(clamped[key])
    return clamped


def parse_bool_value(raw_value: str) -> bool:
    """Parse a Fire-compatible boolean override."""
    lowered = raw_value.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value {raw_value!r}.")


def parse_param_overrides(overrides: list[str]) -> dict[str, int | float | str | bool]:
    """Parse one-off training/reward parameter overrides from KEY=VALUE strings."""
    parsed: dict[str, int | float | str | bool] = {}
    allowed = set(FIRE_PARAM_KEYS)
    for override in overrides:
        if "=" not in override:
            raise ValueError(f"Parameter override must be KEY=VALUE, got {override!r}.")
        key, raw_value = override.split("=", 1)
        if key not in allowed:
            allowed_text = ", ".join(FIRE_PARAM_KEYS)
            raise ValueError(f"Unknown tunable parameter {key!r}. Allowed: {allowed_text}.")
        if key in STRING_PARAM_KEYS:
            choices_for_key = STRING_PARAM_CHOICES[key]
            if raw_value not in choices_for_key:
                choices = ", ".join(sorted(choices_for_key))
                raise ValueError(f"Invalid value for {key!r}: {raw_value!r}. Choices: {choices}.")
            parsed[key] = raw_value
            continue
        if key in BOOL_PARAM_KEYS:
            parsed[key] = parse_bool_value(raw_value)
            continue
        try:
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"Invalid numeric value for {key!r}: {raw_value!r}.") from exc
        parsed[key] = value
    return parsed


def read_research_packets(paths: list[str]) -> list[dict[str, Any]]:
    """Read research packets to attach evidence to a trial."""
    packets: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            raise FileNotFoundError(path)
        text = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        title = path.stem
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip() or title
                break
        packets.append(
            {
                "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                "title": title,
                "sha256": digest,
                "char_count": len(text),
                "excerpt": text[:MAX_RESEARCH_CHARS],
                "truncated": len(text) > MAX_RESEARCH_CHARS,
            }
        )
    return packets


def sanitize_proposal_name(value: str) -> str:
    """Return a filesystem/W&B-safe proposal suffix."""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    cleaned = "".join(char if char in allowed else "_" for char in value.strip())
    cleaned = cleaned.strip("_-").lower()
    if not cleaned:
        raise ValueError("--proposal-name must contain at least one safe character.")
    return cleaned[:80]


def remember_research_packets(state: dict[str, Any], packets: list[dict[str, Any]]) -> None:
    """Store unique research packets at the top level for later tuning context."""
    if not packets:
        return
    remembered = state.setdefault("research_packets", [])
    known = {packet.get("sha256") for packet in remembered if isinstance(packet, dict)}
    for packet in packets:
        if packet["sha256"] not in known:
            remembered.append(
                {
                    "path": packet["path"],
                    "title": packet["title"],
                    "sha256": packet["sha256"],
                    "char_count": packet["char_count"],
                    "truncated": packet["truncated"],
                    "added_at": utc_now(),
                }
            )
            known.add(packet["sha256"])


def structural_search_approved(state: dict[str, Any]) -> bool:
    """Return whether the user has opened structural Level3 search."""
    approval = state.get("structural_search_approval")
    if isinstance(approval, dict) and approval.get("status") == "approved_by_user":
        return True
    policy = state.get("autonomy_policy")
    if not isinstance(policy, dict):
        return False
    return (
        policy.get("structural_changes_stage") == "active_structural_search"
        and policy.get("reward_only_first") is False
        and policy.get("do_not_modify_level3_track") is True
    )


def append_unique_path(paths: list[str], packet: str) -> None:
    """Append a packet path if it is not already present."""
    if packet and packet not in paths:
        paths.append(packet)


def structural_hypothesis_trials(
    state: dict[str, Any],
    hypothesis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return trials that belong to one structural hypothesis."""
    name = str(hypothesis["name"])
    proposal_name = str(hypothesis["proposal_name"])
    layout = str(hypothesis["observation_layout"])
    matches: list[dict[str, Any]] = []
    for trial in state.get("trials", []):
        if not isinstance(trial, dict):
            continue
        if trial.get("structural_hypothesis") == name:
            matches.append(trial)
            continue
        proposal = str(trial.get("proposal", ""))
        if proposal == proposal_name or proposal.startswith(f"{proposal_name}_"):
            matches.append(trial)
            continue
        if trial.get("observation_layout") == layout and proposal.startswith("structural_v5"):
            matches.append(trial)
    return matches


def structural_hypothesis_tried(state: dict[str, Any], hypothesis: dict[str, Any]) -> bool:
    """Return whether a structural hypothesis has any recorded trial."""
    return bool(structural_hypothesis_trials(state, hypothesis))


def unsupported_training_structure(hypothesis: dict[str, Any] | None) -> str | None:
    """Return the required training structure when the current code cannot run it."""
    if hypothesis is None:
        return None
    required = hypothesis.get("requires_training_support")
    if not required:
        return None
    required_name = str(required)
    if required_name in SUPPORTED_TRAINING_STRUCTURES:
        return None
    return required_name


def structural_hypothesis_runnable(hypothesis: dict[str, Any]) -> bool:
    """Return whether a structural hypothesis can be launched by the current trainer."""
    return unsupported_training_structure(hypothesis) is None


def choose_structural_hypothesis(
    args: argparse.Namespace,
    state: dict[str, Any],
) -> dict[str, Any] | None:
    """Choose an explicit or automatic structural hypothesis."""
    requested = args.structural_hypothesis
    if requested != "none":
        return STRUCTURAL_HYPOTHESES[requested]
    if not args.auto_structural_search:
        return None
    if not structural_search_approved(state):
        return None
    for hypothesis in STRUCTURAL_HYPOTHESES.values():
        if not structural_hypothesis_runnable(hypothesis):
            continue
        if not structural_hypothesis_tried(state, hypothesis):
            return hypothesis
    return None


def apply_structural_hypothesis_args(
    args: argparse.Namespace,
    hypothesis: dict[str, Any],
) -> None:
    """Apply default CLI settings for a selected structural hypothesis."""
    if hypothesis.get("config"):
        args.config = str(hypothesis["config"])
    if hypothesis.get("eval_config"):
        args.eval_config = str(hypothesis["eval_config"])
    args.observation_layout = str(hypothesis["observation_layout"])
    if hypothesis.get("from_scratch") and args.initial_checkpoint is None:
        args.from_scratch = True
    if (
        hypothesis.get("initial_checkpoint")
        and args.initial_checkpoint is None
        and not args.from_scratch
    ):
        args.initial_checkpoint = str(hypothesis["initial_checkpoint"])
    if args.train_timesteps == args.default_train_timesteps:
        args.train_timesteps = int(hypothesis["train_timesteps"])
    if args.checkpoint_interval == args.default_checkpoint_interval:
        args.checkpoint_interval = int(hypothesis["checkpoint_interval"])
    if hypothesis.get("num_envs"):
        args.num_envs = int(hypothesis["num_envs"])
    if hypothesis.get("num_steps"):
        args.num_steps = int(hypothesis["num_steps"])
    if hypothesis.get("max_eval_checkpoints"):
        args.max_eval_checkpoints = int(hypothesis["max_eval_checkpoints"])
    if hypothesis.get("eval_seed_split"):
        args.eval_seed_split = str(hypothesis["eval_seed_split"])
    if hypothesis.get("eval_checkpoint_strategy"):
        args.eval_checkpoint_strategy = str(hypothesis["eval_checkpoint_strategy"])
    if hypothesis.get("eval_milestones_m"):
        args.eval_milestones_m = str(hypothesis["eval_milestones_m"])
    if hypothesis.get("allow_hidden_dim_warmstart"):
        args.allow_hidden_dim_warmstart = True
    if hypothesis.get("allow_step_curve_maturation"):
        args.allow_step_curve_maturation = True
    if hypothesis.get("allow_repeat_params"):
        args.allow_repeat_params = True
    if args.proposal_name is None:
        args.proposal_name = str(hypothesis["proposal_name"])
    append_unique_path(args.research_packet, str(hypothesis.get("research_packet", "")))
    if not args.approved_hypothesis_packet:
        append_unique_path(
            args.approved_hypothesis_packet,
            str(hypothesis.get("approved_hypothesis_packet", "")),
        )


def best_summary_for_trial(trial: dict[str, Any]) -> dict[str, Any] | None:
    """Return a trial's best checkpoint summary if available."""
    best = trial.get("best_summary")
    return best if isinstance(best, dict) else None


def normalise_repo_path(value: str | None) -> str | None:
    """Return a stable repo-relative path string when possible."""
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = ROOT / path
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def summary_for_checkpoint(
    state: dict[str, Any],
    checkpoint: Path | None,
) -> dict[str, Any] | None:
    """Find stored evaluator evidence for a checkpoint path."""
    checkpoint_key = normalise_repo_path(str(checkpoint)) if checkpoint is not None else None
    if checkpoint_key is None:
        return None

    def is_target_eval(summary: dict[str, Any], trial: dict[str, Any] | None = None) -> bool:
        eval_config = summary.get("eval_config")
        if eval_config is None and trial is not None:
            eval_config = trial.get("eval_config")
        return str(eval_config or "") in {TARGET_EVAL_CONFIG, f"config/{TARGET_EVAL_CONFIG}"}

    best = state.get("best")
    if (
        isinstance(best, dict)
        and normalise_repo_path(best.get("checkpoint_file")) == checkpoint_key
        and is_target_eval(best)
    ):
        return best

    for trial in state.get("trials", []):
        if not isinstance(trial, dict):
            continue
        summaries = trial.get("summaries")
        if not isinstance(summaries, list):
            continue
        for summary in summaries:
            if (
                isinstance(summary, dict)
                and normalise_repo_path(summary.get("checkpoint_file")) == checkpoint_key
            ):
                if is_target_eval(summary, trial):
                    return summary
    return None


def promising_summary(summary: dict[str, Any] | None) -> bool:
    """Return whether early hard-eval evidence deserves maturation training."""
    if summary is None:
        return False
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    mean_gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    return success >= PROMISING_SUCCESS_RATE or mean_gates >= PROMISING_MEAN_GATES


def latest_metric_summary(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return the newest usable summary from the state."""
    for trial in reversed(state.get("trials", [])):
        summary = best_summary_for_trial(trial)
        if summary is not None:
            return summary
    best = state.get("best")
    return best if isinstance(best, dict) else None


def evaluated_trials(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Return trials with completed evaluator evidence."""
    return [
        trial
        for trial in state.get("trials", [])
        if isinstance(trial, dict)
        and trial.get("status") in {"evaluated", "target_met"}
        and best_summary_for_trial(trial) is not None
    ]


def latest_trial_params(state: dict[str, Any]) -> dict[str, int | float] | None:
    """Return the most recent trial params, normalized with base defaults."""
    for trial in reversed(state.get("trials", [])):
        params = trial.get("params") if isinstance(trial, dict) else None
        if isinstance(params, dict):
            return {**BASE_PARAMS, **params}
    return None


def reward_param_delta(
    previous: dict[str, int | float | str] | None,
    current: dict[str, int | float | str],
) -> dict[str, tuple[Any, Any]]:
    """Return changed train/reward parameters after clamping."""
    if previous is None:
        return {
            key: (None, current[key])
            for key in FIRE_PARAM_KEYS
            if key in current
        }

    changed: dict[str, tuple[Any, Any]] = {}
    for key in FIRE_PARAM_KEYS:
        if key in STRING_PARAM_KEYS:
            previous_value = previous.get(key)
            current_value = current.get(key)
            if current_value is not None and str(previous_value) != str(current_value):
                changed[key] = (previous_value, current_value)
            continue
        if key in BOOL_PARAM_KEYS:
            previous_value = bool(previous.get(key))
            current_value = bool(current.get(key))
            if previous_value != current_value:
                changed[key] = (previous_value, current_value)
            continue
        previous_value = safe_float(previous.get(key))
        current_value = safe_float(current.get(key))
        if current_value is None:
            continue
        if previous_value is None or round(previous_value, 6) != round(current_value, 6):
            changed[key] = (previous_value, current_value)
    return changed


def summary_improved(
    candidate: dict[str, Any] | None,
    reference: dict[str, Any] | None,
    *,
    min_mean_gates_delta: float = MIN_MEAN_GATES_IMPROVEMENT,
) -> bool:
    """Return whether candidate improved the hard early-search metrics."""
    if candidate is None:
        return False
    if reference is None:
        return True

    candidate_success = safe_float(candidate.get("success_rate"), 0.0) or 0.0
    reference_success = safe_float(reference.get("success_rate"), 0.0) or 0.0
    if candidate_success > reference_success:
        return True

    candidate_gates = safe_float(candidate.get("mean_gates"), 0.0) or 0.0
    reference_gates = safe_float(reference.get("mean_gates"), 0.0) or 0.0
    return candidate_gates > reference_gates + min_mean_gates_delta


def consecutive_plateau_count(state: dict[str, Any]) -> int:
    """Count consecutive evaluated trials with no success/gate improvement."""
    trials = evaluated_trials(state)
    count = 0
    for index in range(len(trials) - 1, 0, -1):
        current = best_summary_for_trial(trials[index])
        previous = best_summary_for_trial(trials[index - 1])
        if summary_improved(current, previous):
            break
        count += 1
    return count


def trial_train_timesteps(trial: dict[str, Any]) -> int:
    """Parse total timesteps from a stored training command."""
    command = trial.get("train_command")
    if not command:
        return 0
    try:
        parts = shlex.split(str(command))
    except ValueError:
        parts = str(command).split()
    for part in parts:
        if part.startswith("--total_timesteps="):
            raw_value = part.split("=", 1)[1]
            try:
                return int(float(raw_value))
            except ValueError:
                return 0
    return 0


def reward_hypothesis_signature(trial: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    """Return a stable signature for one train/reward hypothesis."""
    params = trial.get("params") if isinstance(trial, dict) else {}
    if not isinstance(params, dict):
        params = {}
    return tuple(
        (key, str(params.get(key)) if key in STRING_PARAM_KEYS else safe_float(params.get(key)))
        for key in FIRE_PARAM_KEYS
    )


def reward_only_exhaustion_evidence(
    state: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Summarize whether reward-only tuning has enough failures to escalate."""
    trials = evaluated_trials(state)
    total_timesteps = sum(trial_train_timesteps(trial) for trial in trials)
    distinct_hypotheses = {
        reward_hypothesis_signature(trial)
        for trial in trials
        if trial.get("status") in {"evaluated", "target_met"}
    }
    plateau_count = consecutive_plateau_count(state)
    best = state.get("best") if isinstance(state.get("best"), dict) else {}
    best_success = safe_float(best.get("success_rate"), 0.0) or 0.0
    best_gates = safe_float(best.get("mean_gates"), 0.0) or 0.0

    criteria = {
        "evaluated_trials": {
            "actual": len(trials),
            "required": args.escalation_min_evaluated_trials,
            "met": len(trials) >= args.escalation_min_evaluated_trials,
        },
        "distinct_reward_hypotheses": {
            "actual": len(distinct_hypotheses),
            "required": args.escalation_min_distinct_reward_hypotheses,
            "met": len(distinct_hypotheses)
            >= args.escalation_min_distinct_reward_hypotheses,
        },
        "total_reward_only_timesteps": {
            "actual": total_timesteps,
            "required": args.escalation_min_total_timesteps,
            "met": total_timesteps >= args.escalation_min_total_timesteps,
        },
        "consecutive_plateau_trials": {
            "actual": plateau_count,
            "required": args.escalation_min_plateau_trials,
            "met": plateau_count >= args.escalation_min_plateau_trials,
        },
        "target_not_met": {
            "actual": best_success,
            "required": f"< {TARGET_SUCCESS_RATE}",
            "met": best_success < TARGET_SUCCESS_RATE,
        },
    }
    eligible = all(item["met"] for item in criteria.values())
    return {
        "eligible_for_structural_escalation_review": eligible,
        "criteria": criteria,
        "best_success_rate": best_success,
        "best_mean_gates": best_gates,
        "required_action_if_eligible": (
            "Spawn separate subagents for evaluator evidence, W&B curves, "
            "reward-only failure audit, papers/GitHub research, and codebase "
            "architecture diagnosis. Write a detailed escalation packet before "
            "any PPO/observation/reward-structure/training-structure change."
        ),
    }


def long_run_extension_eligible(state: dict[str, Any]) -> bool:
    """Return whether the latest completed trial earned a longer continuation."""
    trials = evaluated_trials(state)
    if len(trials) < 2:
        return False
    latest = best_summary_for_trial(trials[-1])
    previous = best_summary_for_trial(trials[-2])
    return summary_improved(latest, previous)


def step_curve_maturation_eligible(
    args: argparse.Namespace,
    state: dict[str, Any],
    initial_checkpoint: Path | None,
) -> bool:
    """Return whether Level2 step-curve evidence permits a longer maturation run."""
    if not args.allow_step_curve_maturation:
        return False
    if args.train_timesteps <= args.long_run_threshold:
        return False
    initial_summary = summary_for_checkpoint(state, initial_checkpoint)
    return promising_summary(initial_summary)


def training_horizon_policy(
    args: argparse.Namespace,
    state: dict[str, Any],
    initial_checkpoint: Path | None,
) -> dict[str, Any]:
    """Describe how the current train chunk fits the step-curve policy."""
    if args.train_timesteps <= SCREENING_TIMESTEPS:
        phase = "screening"
        next_action = (
            "If hard eval has non-zero success or meaningful gate progress, "
            "continue the same hypothesis toward 60M before rejecting it."
        )
    elif args.train_timesteps <= MATURATION_TIMESTEPS:
        phase = "maturation_60m"
        next_action = (
            "Use hard eval plus W&B analysis. If success/gates improve, continue "
            "toward 90M; otherwise reject or revise the reward hypothesis."
        )
    elif args.train_timesteps <= CONFIRMATION_TIMESTEPS:
        phase = "maturation_90m"
        next_action = (
            "Treat this as the first serious success-rate decision point; promote "
            "candidate checkpoints to wider seed evaluation if promising."
        )
    else:
        phase = "extended"
        next_action = (
            "Only continue beyond 90M when a checkpoint is already competitive or "
            "a source-backed decision packet explains the extra budget."
        )

    initial_summary = summary_for_checkpoint(state, initial_checkpoint)
    return {
        "source": LEVEL2_STEP_CURVE_PACKET,
        "phase": phase,
        "train_timesteps": args.train_timesteps,
        "checkpoint_interval": args.checkpoint_interval,
        "eval_checkpoint_strategy": args.eval_checkpoint_strategy,
        "eval_milestones_m": args.eval_milestones_m,
        "initial_checkpoint": checkpoint_reference(initial_checkpoint),
        "initial_checkpoint_evidence": {
            "found": initial_summary is not None,
            "success_rate": safe_float(initial_summary.get("success_rate"))
            if initial_summary
            else None,
            "mean_gates": safe_float(initial_summary.get("mean_gates"))
            if initial_summary
            else None,
            "crash_rate": safe_float(initial_summary.get("crash_rate"))
            if initial_summary
            else None,
            "promising_for_maturation": promising_summary(initial_summary),
        },
        "rule": (
            "30M is screening, not final judgment. Mature promising branches to "
            "60M-90M and select among intermediate checkpoints; final is not "
            "assumed best."
        ),
        "next_action": next_action,
    }


def checkpoint_reference(path: Path | None) -> str | None:
    """Render a checkpoint path relative to the repo when possible."""
    if path is None:
        return None
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def initial_audit_required(
    args: argparse.Namespace,
    state: dict[str, Any],
    initial_checkpoint: Path | None,
) -> bool:
    """Require an initial-checkpoint audit before the first training trial."""
    if args.skip_initial_audit or args.from_scratch or initial_checkpoint is None:
        return False
    if evaluated_trials(state) or state.get("initial_checkpoint_audit"):
        return False
    return True


def build_hold_decision(
    args: argparse.Namespace,
    state: dict[str, Any],
    proposal_name: str,
    params: dict[str, int | float],
    reason: str,
    param_overrides: dict[str, int | float],
    initial_checkpoint: Path | None,
) -> dict[str, Any] | None:
    """Return a hold decision when the next automatic run would be low-value."""
    manual_hypothesis = bool(param_overrides or args.approved_hypothesis_packet)
    reasons: list[str] = []
    previous_params = latest_trial_params(state)
    param_delta = reward_param_delta(previous_params, params)

    if not param_delta and not args.allow_repeat_params:
        reasons.append(
            "proposed reward params are identical to the latest trial after bounds; "
            "automatic continuation would be a no-op"
        )

    plateau_count = consecutive_plateau_count(state)
    if (
        plateau_count >= args.plateau_trial_limit
        and not manual_hypothesis
        and not args.auto_hypothesis_search
        and not args.allow_plateau_continuation
    ):
        reasons.append(
            f"{plateau_count} consecutive evaluated trials did not improve "
            "success_rate or mean_gates; require a new approved reward-only "
            "hypothesis packet or explicit reward --param override"
        )

    if proposal_name == "auto_hypotheses_exhausted" and not manual_hypothesis:
        reasons.append(
            "all predefined automatic reward-only hypotheses were already tried; "
            "require a new approved reward-only hypothesis packet or structural "
            "escalation review"
        )

    if (
        args.train_timesteps > args.long_run_threshold
        and not args.allow_long_run_without_improvement
        and not long_run_extension_eligible(state)
        and not step_curve_maturation_eligible(args, state, initial_checkpoint)
    ):
        reasons.append(
            f"train_timesteps={args.train_timesteps} exceeds the long-run threshold "
            f"{args.long_run_threshold}, but the latest screened hypothesis did not "
            "improve success_rate or mean_gates and the selected initial checkpoint "
            "does not satisfy the Level2 step-curve maturation rule"
        )

    if initial_audit_required(args, state, initial_checkpoint):
        reasons.append(
            f"initial checkpoint has not been audited on {TARGET_EVAL_CONFIG}; "
            "run --audit-initial-checkpoint first or pass --skip-initial-audit explicitly"
        )

    if not reasons:
        return None

    exhaustion = reward_only_exhaustion_evidence(state, args)

    return {
        "created_at": utc_now(),
        "status": "held_before_training",
        "proposal": proposal_name,
        "proposal_reason": reason,
        "reasons": reasons,
        "changed_reward_params": {
            key: {"from": old, "to": new} for key, (old, new) in param_delta.items()
        },
        "auto_hypothesis_search": args.auto_hypothesis_search,
        "relaxed_reward_bounds": args.relaxed_reward_bounds,
        "codex_autonomous_loop": args.codex_autonomous_loop,
        "plateau_count": plateau_count,
        "train_timesteps": args.train_timesteps,
        "long_run_threshold": args.long_run_threshold,
        "step_curve_policy": training_horizon_policy(args, state, initial_checkpoint),
        "initial_checkpoint": checkpoint_reference(initial_checkpoint),
        "observation_layout": args.observation_layout,
        "keep_latest_params": args.keep_latest_params,
        "reward_only_exhaustion": exhaustion,
    }


def build_training_structure_hold(
    args: argparse.Namespace,
    hypothesis: dict[str, Any] | None,
    proposal_name: str,
    reason: str,
    analysis_packets: list[dict[str, str]],
    research_packets: list[dict[str, str]],
    approved_hypothesis_packets: list[dict[str, str]],
) -> dict[str, Any] | None:
    """Hold when a named structural lane needs trainer/controller support first."""
    missing_support = unsupported_training_structure(hypothesis)
    if missing_support is None:
        return None
    architecture = hypothesis.get("architecture", {}) if isinstance(hypothesis, dict) else {}
    if str(missing_support).startswith("v30_"):
        support_steps = (
            "implement the v30 semantic repair gates first: deterministic "
            "loop052 parity, same-step finish termination, exactly-once finish "
            "bonus, no terminal-to-reset dummy transition, per-slot wrapper "
            "resets, true observation-delay reset, termination reason logging, "
            "and squashed-Gaussian logprob support when requested"
        )
    elif missing_support == "mlp_to_gru_transfer_support":
        support_steps = (
            "implement explicit MLP-to-GRU checkpoint transfer from loop101, "
            "hidden-state reset checks on episode boundaries, sequence rollout "
            "and BPTT checks, checkpoint metadata validation, "
            "ppo_level3_inference recurrent hidden-state reset checks, and a "
            "bounded zero-update or deterministic parity packet before "
            "launching this lane"
        )
    elif missing_support == "residual_gru_teacher_retention_support":
        support_steps = (
            "implement residual-GRU teacher-retention or distillation support "
            "before launching this lane: build retention data or online teacher "
            "sampling for recurrent students, wire retention loss into sequence "
            "minibatches, record teacher checkpoint/layout metadata, log "
            "nonzero retention/sampled_batch_size plus finite teacher_kl, "
            "teacher_action_mse, and teacher_agreement metrics, and write a "
            "zero-update or deterministic preflight packet"
        )
    else:
        support_steps = (
            "implement recurrent PPO rollout storage, sequence minibatching, "
            "GRU hidden-state reset on episode boundaries, checkpoint metadata, "
            "and ppo_level3_inference hidden-state handling before launching "
            "this lane"
        )
    return {
        "created_at": utc_now(),
        "status": "held_before_training",
        "proposal": proposal_name,
        "proposal_reason": reason,
        "reasons": [
            (
                f"structural hypothesis requires training support "
                f"{missing_support!r}, but the current loop only supports "
                f"{sorted(SUPPORTED_TRAINING_STRUCTURES)}"
            ),
            support_steps,
        ],
        "required_training_support": missing_support,
        "supported_training_structures": sorted(SUPPORTED_TRAINING_STRUCTURES),
        "architecture": architecture,
        "observation_layout": args.observation_layout,
        "train_timesteps": args.train_timesteps,
        "checkpoint_interval": args.checkpoint_interval,
        "analysis_packets": analysis_packets,
        "research_packets": research_packets,
        "approved_hypothesis_packets": approved_hypothesis_packets,
        "codex_autonomous_loop": args.codex_autonomous_loop,
    }


def record_hold_decision(
    state_path: Path,
    state: dict[str, Any],
    decision: dict[str, Any],
    *,
    dry_run: bool,
) -> None:
    """Persist or display a hold decision."""
    if dry_run:
        print(json.dumps(decision, indent=2, sort_keys=True))
        return
    state["last_decision"] = decision
    state.setdefault("hold_decisions", []).append(decision)
    write_state(state_path, state)
    print("Loop held before training:")
    for reason in decision["reasons"]:
        print(f"- {reason}")


def active_post_run_decision_gate(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return a pending post-run decision gate, if the analyzer created one."""
    gate = state.get("pending_post_run_decision")
    if not isinstance(gate, dict):
        return None
    if gate.get("status") != "awaiting_main_agent_decision":
        return None
    if not gate.get("requires_packet_before_next_training", True):
        return None
    return gate


def decision_packet_text(packet: dict[str, Any]) -> str:
    """Return searchable packet metadata and excerpt text."""
    return "\n".join(
        str(packet.get(key, "")) for key in ("path", "title", "excerpt")
    )


def decision_packet_option(packet: dict[str, Any]) -> str | None:
    """Return the explicit post-run decision option in a markdown packet."""
    text = decision_packet_text(packet)
    for option in POST_RUN_DECISION_OPTIONS:
        if f"`{option}`" in text or f"Decision: {option}" in text:
            return option
    return None


def decision_packet_matches_gate(packet: dict[str, Any], gate: dict[str, Any]) -> bool:
    """Return whether a decision packet is specific to the pending post-run gate."""
    text = decision_packet_text(packet)
    markers: list[str] = []
    for key in ("trial_id", "analysis_report", "analysis_json"):
        value = gate.get(key)
        if not value:
            continue
        value_text = str(value)
        markers.append(value_text)
        markers.append(Path(value_text).name)
    return any(marker and marker in text for marker in markers)


def main_agent_decision_packets(
    approved_hypothesis_packets: list[dict[str, Any]],
    *,
    gate: dict[str, Any] | None = None,
    require_training_decision: bool = False,
) -> list[dict[str, Any]]:
    """Return attached packets that are valid post-run main-agent decisions."""
    packets: list[dict[str, Any]] = []
    for packet in approved_hypothesis_packets:
        path = Path(str(packet.get("path", "")))
        if path.parts[:3] != ("experiments", "level3_ppo_loop", "decisions"):
            continue
        if gate is not None and not decision_packet_matches_gate(packet, gate):
            continue
        if require_training_decision:
            decision = decision_packet_option(packet)
            if decision not in POST_RUN_TRAINING_DECISION_OPTIONS:
                continue
        packets.append(packet)
    return packets


def build_post_run_decision_hold(
    args: argparse.Namespace,
    state: dict[str, Any],
    proposal_name: str,
    reason: str,
    initial_checkpoint: Path | None,
    approved_hypothesis_packets: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Hold when analysis requires a main-agent decision packet first."""
    gate = active_post_run_decision_gate(state)
    if gate is None:
        return None
    valid_decision_packets = main_agent_decision_packets(
        approved_hypothesis_packets,
        gate=gate,
        require_training_decision=True,
    )
    if valid_decision_packets:
        return None
    attached_decision_packets = main_agent_decision_packets(approved_hypothesis_packets)
    invalid_packet_paths = [packet["path"] for packet in attached_decision_packets]
    reasons = [
        "latest evaluated trial has a pending post-run decision gate",
        "spawn the required review subagents, synthesize their findings, "
        "and attach a main-agent decision packet with "
        "--approved-hypothesis-packet before the next train/evaluate chunk",
    ]
    if invalid_packet_paths:
        reasons.append(
            "attached decision packet(s) do not resolve the latest gate because "
            "they are stale, point at a different trial, or choose hold/stop: "
            + ", ".join(invalid_packet_paths)
        )

    return {
        "created_at": utc_now(),
        "status": "held_before_training",
        "proposal": proposal_name,
        "proposal_reason": reason,
        "reasons": reasons,
        "pending_post_run_decision": gate,
        "required_review_roles": gate.get("required_review_roles", POST_RUN_REVIEW_ROLES),
        "allowed_decisions": gate.get("allowed_decisions", POST_RUN_DECISION_OPTIONS),
        "override_requirements": (
            "Create a markdown decision packet under "
            "experiments/level3_ppo_loop/decisions/ and pass it with "
            "--approved-hypothesis-packet. Structural lanes must be named and "
            f"must keep hard eval on config/{TARGET_EVAL_CONFIG}."
        ),
        "codex_autonomous_loop": args.codex_autonomous_loop,
        "train_timesteps": args.train_timesteps,
        "step_curve_policy": training_horizon_policy(args, state, initial_checkpoint),
        "initial_checkpoint": checkpoint_reference(initial_checkpoint),
        "observation_layout": args.observation_layout,
    }


def resolve_post_run_decision_gate(
    state: dict[str, Any],
    trial: dict[str, Any],
    approved_hypothesis_packets: list[dict[str, Any]],
) -> None:
    """Mark the pending gate resolved by the packet attached to this trial."""
    gate = active_post_run_decision_gate(state)
    decision_packets = main_agent_decision_packets(
        approved_hypothesis_packets,
        gate=gate,
        require_training_decision=True,
    )
    if gate is None or not decision_packets:
        return
    resolved_gate = dict(gate)
    resolved_gate["status"] = "resolved_by_next_training_packet"
    resolved_gate["resolved_at"] = utc_now()
    resolved_gate["resolved_by_trial"] = trial["trial_id"]
    resolved_gate["decision_packets"] = [
        packet["path"] for packet in decision_packets
    ]
    trial["resolved_post_run_decision_gate"] = resolved_gate
    trial["main_agent_decision_packet"] = resolved_gate["decision_packets"][-1]
    state["pending_post_run_decision"] = resolved_gate
    state["last_main_agent_decision_packet"] = resolved_gate["decision_packets"][-1]


def active_state_training_hold(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return the latest state-level hold that requires approval before training."""
    candidates: list[dict[str, Any]] = []
    for key in (
        "stage2_after_loop014_escalation_audit",
        "level3_loop_014_taxonomy_reward_code_hold",
        "level3_after_loop084_eval_protocol_hold",
        "level3_after_loop087_v27_teacher_kl_hold",
        "level3_after_loop089_gate_conversion_hold",
        "level3_after_loop090_v29_rejection_hold",
        "level3_after_loop098_v32_parity_hold",
        "level3_v30_semantics_audit_hold",
    ):
        value = state.get(key)
        if not isinstance(value, dict):
            continue
        requires_approval = bool(value.get("requires_user_approval_for_next_training"))
        status = str(value.get("status", ""))
        if requires_approval or status.startswith("hold_after_loop014"):
            candidate = dict(value)
            candidate["state_key"] = key
            candidates.append(candidate)

    last_decision = state.get("last_decision")
    if isinstance(last_decision, dict):
        status = str(last_decision.get("status", ""))
        if status in {"held_after_stage2_audit", "held_by_state_guard"}:
            candidate = dict(last_decision)
            candidate["state_key"] = "last_decision"
            candidates.append(candidate)

    if not candidates:
        return None
    return max(candidates, key=lambda item: str(item.get("created_at", "")))


def build_state_hold_decision(
    args: argparse.Namespace,
    state: dict[str, Any],
    proposal_name: str,
    reason: str,
    param_overrides: dict[str, int | float],
    initial_checkpoint: Path | None,
) -> dict[str, Any] | None:
    """Hold when state records a post-audit stop pending explicit approval."""
    hold = active_state_training_hold(state)
    if hold is None:
        return None

    structural_command = (
        args.config != args.eval_config
        or args.observation_layout != WORLD_HISTORY_OBSERVATION_LAYOUT
    )
    requires_override = bool(hold.get("requires_override_state_hold"))
    explicit_approval = bool(
        args.override_state_hold
        and (
            param_overrides
            or (structural_command and args.approved_hypothesis_packet)
        )
        or (
            not requires_override
            and
            structural_search_approved(state)
            and structural_command
            and args.approved_hypothesis_packet
        )
    )
    if explicit_approval:
        return None

    if args.override_state_hold:
        raise SystemExit(
            "error: --override-state-hold requires explicit reward --param values, "
            "or an approved structural command with --approved-hypothesis-packet."
        )

    report = hold.get("report")
    reasons = [
        "state records a post-audit hold that requires explicit approval before "
        "the next train/evaluate chunk"
    ]
    if report:
        reasons.append(f"review the hold packet first: {report}")

    return {
        "created_at": utc_now(),
        "status": "held_by_state_guard",
        "proposal": proposal_name,
        "proposal_reason": reason,
        "reasons": reasons,
        "source_state_key": hold.get("state_key"),
        "source_report": report,
        "override_required": "--override-state-hold",
        "override_requirements": (
            "Use only after the user explicitly approves a new lane; pair it "
            "with explicit reward --param values, or with a structural command "
            "and --approved-hypothesis-packet."
        ),
        "codex_autonomous_loop": args.codex_autonomous_loop,
        "train_timesteps": args.train_timesteps,
        "step_curve_policy": training_horizon_policy(args, state, initial_checkpoint),
        "initial_checkpoint": checkpoint_reference(initial_checkpoint),
        "observation_layout": args.observation_layout,
    }


def auto_hypothesis_index(state: dict[str, Any]) -> int:
    """Choose the next automatic reward hypothesis to try."""
    tried_names: set[str] = set()
    for trial in state.get("trials", []):
        proposal = str(trial.get("proposal", ""))
        if proposal.startswith("auto_"):
            tried_names.add(proposal)
    for index, hypothesis in enumerate(AUTO_REWARD_HYPOTHESES):
        if str(hypothesis["name"]) not in tried_names:
            return index
    return len(AUTO_REWARD_HYPOTHESES)


def propose_auto_hypothesis(
    state: dict[str, Any],
    base_params: dict[str, int | float] | None = None,
) -> tuple[str, dict[str, int | float], str]:
    """Return a bounded absolute reward-only hypothesis after plateau."""
    index = auto_hypothesis_index(state)
    params = {**BASE_PARAMS, **(base_params or {})}
    if index >= len(AUTO_REWARD_HYPOTHESES):
        return (
            "auto_hypotheses_exhausted",
            params,
            (
                "All predefined automatic reward-only hypotheses have already "
                "been evaluated. Require a new source-backed reward hypothesis "
                "or a structural-escalation review if exhaustion criteria are met."
            ),
        )
    hypothesis = AUTO_REWARD_HYPOTHESES[index]
    params.update(hypothesis["params"])
    summary = latest_metric_summary(state) or {}
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    mean_gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    crash = safe_float(summary.get("crash_rate"), 0.0) or 0.0
    reason = (
        f"Auto hypothesis {index + 1}/{len(AUTO_REWARD_HYPOTHESES)} after plateau. "
        f"{hypothesis['rationale']} Latest evidence: success={success:.2f}, "
        f"gates={mean_gates:.2f}, crash={crash:.2f}."
    )
    return str(hypothesis["name"]), params, reason


def scale(params: dict[str, int | float], key: str, factor: float) -> None:
    """Scale one numeric parameter in place."""
    params[key] = float(params[key]) * factor


def propose_params(
    state: dict[str, Any],
    *,
    relaxed_bounds: bool = False,
    auto_hypothesis_search: bool = False,
    plateau_trial_limit: int = DEFAULT_PLATEAU_TRIAL_LIMIT,
) -> tuple[str, dict[str, int | float], str]:
    """Choose the next bounded parameter set from the latest metrics."""
    trials = state.get("trials", [])
    if not trials:
        return (
            "baseline",
            clamp_params(BASE_PARAMS, relaxed=relaxed_bounds),
            "Notebook baseline parameters.",
        )

    last_trial = trials[-1]
    params = deepcopy(last_trial.get("params", BASE_PARAMS))
    params = {**BASE_PARAMS, **params}
    if auto_hypothesis_search and consecutive_plateau_count(state) >= plateau_trial_limit:
        name, params, reason = propose_auto_hypothesis(state, base_params=params)
        return name, clamp_params(params, relaxed=relaxed_bounds), reason
    summary = latest_metric_summary(state)
    if summary is None:
        scale(params, "gate_bonus", 1.08)
        scale(params, "gate_front_bonus", 1.05)
        return (
            "explore_no_metrics",
            clamp_params(params, relaxed=relaxed_bounds),
            "No metrics found; mild reward-only exploration.",
        )

    target = state.get("target", {})
    target_success = float(target.get("success_rate", TARGET_SUCCESS_RATE))
    target_time = float(target.get("mean_time_s_success", TARGET_TIME_S))
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    crash = safe_float(summary.get("crash_rate"), 0.0) or 0.0
    timeout = safe_float(summary.get("timeout_rate"), 0.0) or 0.0
    mean_gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    time_s = safe_float(summary.get("mean_time_s_success"))
    worst_tilt = safe_float(summary.get("worst_tilt_deg"), 0.0) or 0.0

    moves: list[str] = []
    if success < target_success and mean_gates < 2.5:
        scale(params, "gate_stage_coef", 1.15)
        scale(params, "gate_axis_coef", 1.1)
        scale(params, "gate_bonus", 1.12)
        scale(params, "gate_front_bonus", 1.08)
        scale(params, "finish_bonus", 1.08)
        scale(params, "time_penalty", 0.85)
        moves.append("gate_acquisition")
    elif success < target_success:
        scale(params, "finish_bonus", 1.12)
        scale(params, "gate_back_bonus", 1.1)
        scale(params, "timeout_penalty", 1.08)
        moves.append("completion")

    if crash > 0.25 or worst_tilt > 45.0:
        scale(params, "crash_penalty", 1.25)
        scale(params, "obstacle_coef", 1.15)
        scale(params, "act_coef", 1.15)
        scale(params, "d_act_xy_coef", 1.12)
        scale(params, "d_act_th_coef", 1.12)
        scale(params, "cmd_tilt_coef", 1.12)
        scale(params, "rpy_coef", 1.1)
        params["tilt_limit_deg"] = min(float(params["tilt_limit_deg"]), 38.0)
        moves.append("safety")

    if success >= target_success and time_s is not None and time_s > target_time:
        scale(params, "time_penalty", 1.35)
        scale(params, "gate_axis_coef", 1.08)
        scale(params, "act_coef", 0.9)
        scale(params, "d_act_xy_coef", 0.9)
        scale(params, "d_act_th_coef", 0.9)
        moves.append("speed")

    if timeout > 0.30 and success < target_success:
        scale(params, "timeout_penalty", 1.15)
        scale(params, "gate_axis_coef", 1.05)
        moves.append("timeout_pressure")

    if not moves:
        moves.append("reward_hold")

    name = "_".join(moves)
    reason = (
        f"Based on success={success:.2f}, gates={mean_gates:.2f}, crash={crash:.2f}, "
        f"timeout={timeout:.2f}, time={time_s}."
    )
    return name, clamp_params(params, relaxed=relaxed_bounds), reason


def format_fire_value(value: int | float | bool | str) -> str:
    """Format values for Fire CLI flags."""
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def build_train_command(
    args: argparse.Namespace,
    run_name: str,
    run_dir: Path,
    params: dict[str, int | float],
    initial_checkpoint: Path | None,
) -> list[str]:
    """Build the training command for one trial."""
    command = [
        *args.python_command,
        str(CONTROL_DIR / "train_CleanRL_ppo_level3.py"),
        f"--config={args.config}",
        f"--wandb_enabled={format_fire_value(args.wandb_enabled)}",
        f"--wandb_project_name={args.wandb_project_name}",
        f"--wandb_mode={args.wandb_mode}",
        "--train=True",
        "--eval=0",
        f"--total_timesteps={args.train_timesteps}",
        f"--num_envs={args.num_envs}",
        f"--num_steps={args.num_steps}",
        f"--cuda={format_fire_value(args.cuda)}",
        f"--jax_device={args.jax_device}",
        f"--model_name=checkpoints/{run_name}/{run_name}_final.ckpt",
        f"--checkpoint_dir={run_dir}",
        f"--checkpoint_interval={args.checkpoint_interval}",
        f"--observation_layout={args.observation_layout}",
    ]
    if args.wandb_entity:
        command.append(f"--wandb_entity={args.wandb_entity}")
    if args.wandb_enabled:
        command.extend(
            [
                f"--wandb_run_name={run_name}",
                f"--wandb_run_id={run_name}",
            ]
        )
    if initial_checkpoint is not None:
        command.append(f"--initial_model_name={initial_checkpoint}")
    if args.allow_hidden_dim_warmstart:
        command.append("--allow_hidden_dim_warmstart=True")
    for key in FIRE_PARAM_KEYS:
        if key in params:
            command.append(f"--{key}={format_fire_value(params[key])}")
    return command


def select_step_checkpoints(
    step_checkpoints: list[Path],
    *,
    limit: int,
    strategy: str,
    milestones: list[int],
) -> list[Path]:
    """Choose step checkpoints for hard eval."""
    if limit <= 0:
        return []
    if strategy == "latest":
        return step_checkpoints[-limit:]

    by_step = {checkpoint_step(path): path for path in step_checkpoints}
    selected: list[Path] = []
    seen: set[Path] = set()
    for milestone in milestones:
        path = by_step.get(milestone)
        if path is not None:
            selected.append(path)
            seen.add(path.resolve())

    if len(selected) < limit:
        for path in reversed(step_checkpoints):
            resolved = path.resolve()
            if resolved in seen:
                continue
            selected.append(path)
            seen.add(resolved)
            if len(selected) >= limit:
                break

    return sorted(selected[:limit], key=checkpoint_step)


def trial_checkpoints(
    run_name: str,
    run_dir: Path,
    limit: int,
    *,
    strategy: str,
    milestones: list[int],
) -> list[Path]:
    """Return selected step checkpoints plus final."""
    step_checkpoints = sorted(run_dir.glob(f"{run_name}_step_*.ckpt"), key=checkpoint_step)
    selected = select_step_checkpoints(
        step_checkpoints,
        limit=max(limit, 0),
        strategy=strategy,
        milestones=milestones,
    )
    final = run_dir / f"{run_name}_final.ckpt"
    if final.exists():
        selected.append(final)
    unique: list[Path] = []
    seen: set[Path] = set()
    for checkpoint in selected:
        resolved = checkpoint.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(checkpoint)
    return unique


def build_eval_command(
    args: argparse.Namespace,
    out_prefix: Path,
    checkpoints: list[Path],
    *,
    seed_file: Path | None = None,
    seed_split_name: str | None = None,
) -> list[str]:
    """Build the checkpoint evaluation command."""
    command = [
        *args.python_command,
        str(ROOT / "scripts" / "evaluate_level2_selected_ppo.py"),
        "--config",
        args.eval_config,
        "--inference-module",
        args.eval_inference_module,
        "--confidence-interval",
        args.confidence_interval,
        "--out-prefix",
        str(out_prefix),
    ]
    if seed_file is not None:
        command.extend(["--seed-file", str(seed_file)])
        if seed_split_name:
            command.extend(["--seed-split-name", seed_split_name])
    else:
        command.extend(["--seed-start", str(args.seed_start), "--num-seeds", str(args.eval_seeds)])
        if seed_split_name:
            command.extend(["--seed-split-name", seed_split_name])
    if args.enable_failure_taxonomy:
        command.append("--failure-taxonomy")
    command.extend(str(path) for path in checkpoints)
    return command


def split_seed_file(args: argparse.Namespace, split: str) -> Path | None:
    """Return the seed manifest for an evaluator split."""
    if split == "dev_seen":
        return args.dev_seed_file
    if split == "validation_unseen":
        return args.validation_seed_file
    if split == "final_locked":
        return args.final_seed_file
    return None


def eval_out_prefix(base: Path, split: str) -> Path:
    """Return a split-specific evaluator output prefix."""
    return base.with_name(f"{base.name}_{split}")


def eval_log_path(base: Path, split: str) -> Path:
    """Return a split-specific evaluator log path."""
    return base.with_name(f"{base.stem}_{split}{base.suffix}")


def promotion_gate_met(summary: dict[str, Any], args: argparse.Namespace) -> bool:
    """Return whether a dev checkpoint should be promoted to validation eval."""
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    return success >= args.validation_promotion_threshold or (
        success >= args.validation_promotion_secondary_success
        and gates >= args.validation_promotion_mean_gates
    )


def checkpoint_paths_for_summaries(
    checkpoints: list[Path], summaries: list[dict[str, Any]]
) -> list[Path]:
    """Map evaluator summary rows back to checkpoint paths."""
    by_reference = {checkpoint_reference(path): path for path in checkpoints}
    selected: list[Path] = []
    for summary in summaries:
        checkpoint = by_reference.get(str(summary.get("checkpoint_file")))
        if checkpoint is not None:
            selected.append(checkpoint)
    return selected


def run_logged(command: list[str], log_path: Path, dry_run: bool) -> int:
    """Run a command, teeing stdout and stderr into a log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(command_text(command))
        return 0
    with log_path.open("w") as log:
        log.write(f"$ {command_text(command)}\n\n")
        log.flush()
        process = subprocess.run(
            command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=False
        )
    return int(process.returncode)


def normalise_summary_row(
    row: dict[str, str], target_success: float, target_time: float
) -> dict[str, Any]:
    """Convert evaluator CSV strings into typed summary fields."""
    typed: dict[str, Any] = {}
    for key, value in row.items():
        if key in FLOAT_SUMMARY_FIELDS or key.startswith("failure_rate_gate_"):
            typed[key] = safe_float(value)
        elif key in INT_SUMMARY_FIELDS:
            typed[key] = int(float(value)) if value not in (None, "") else None
        else:
            typed[key] = value
    typed["score"] = score_summary(typed)
    typed["target_met"] = target_met(typed, target_success, target_time)
    return typed


def read_summary_csv(
    path: Path, target_success: float, target_time: float
) -> list[dict[str, Any]]:
    """Read evaluator summaries."""
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="") as handle:
        return [
            normalise_summary_row(row, target_success, target_time)
            for row in csv.DictReader(handle)
        ]


def score_summary(summary: dict[str, Any]) -> float:
    """Score a checkpoint for search ordering."""
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    crash = safe_float(summary.get("crash_rate"), 0.0) or 0.0
    timeout = safe_float(summary.get("timeout_rate"), 0.0) or 0.0
    gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    time_s = safe_float(summary.get("mean_time_s_success"))
    score = 100.0 * success + 4.0 * gates - 25.0 * crash - 15.0 * timeout
    if time_s is None:
        score -= 50.0
    else:
        score -= max(0.0, time_s - TARGET_TIME_S) * 8.0
    return round(score, 6)


def target_met(summary: dict[str, Any], target_success: float, target_time: float) -> bool:
    """Return whether the hard Level3 gate is satisfied."""
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    time_s = safe_float(summary.get("mean_time_s_success"))
    return time_s is not None and success >= target_success and time_s <= target_time


def evaluation_rank_key(summary: dict[str, Any]) -> tuple[float, float, float, float, float, float]:
    """Return the hard-eval ordering key for checkpoint selection."""
    success = safe_float(summary.get("success_rate"), 0.0) or 0.0
    ci_low = safe_float(summary.get("success_ci95_low"), success) or success
    crash = safe_float(summary.get("crash_rate"), 1.0)
    crash = 1.0 if crash is None else crash
    gates = safe_float(summary.get("mean_gates"), 0.0) or 0.0
    time_s = safe_float(summary.get("mean_time_s_success"))
    time_key = -time_s if time_s is not None else -1e9
    score = safe_float(summary.get("score"), -1e9) or -1e9
    return (success, ci_low, -crash, gates, time_key, score)


def best_of(summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the best checkpoint under the current hard-eval ordering."""
    return max(summaries, key=evaluation_rank_key, default=None)


def checkpoint_train_step(summary: dict[str, Any], default_step: int) -> int:
    """Infer the checkpoint training step for W&B eval logging."""
    checkpoint_file = summary.get("checkpoint_file")
    if not checkpoint_file:
        return default_step
    step = checkpoint_step(Path(str(checkpoint_file)))
    return step if step > 0 else default_step


def log_eval_summaries_to_wandb(
    args: argparse.Namespace,
    run_name: str,
    summaries: list[dict[str, Any]],
    trial_best: dict[str, Any] | None,
) -> str | None:
    """Append competition-style evaluation metrics to the trial's W&B run."""
    if not args.wandb_enabled:
        return None
    try:
        import wandb
    except ImportError:
        return None

    init_kwargs: dict[str, Any] = {
        "project": args.wandb_project_name,
        "entity": args.wandb_entity,
        "name": run_name,
        "id": run_name,
        "resume": "allow",
        "mode": args.wandb_mode,
        "config": {
            "loop_eval_config": args.eval_config,
            "loop_eval_seed_split": args.eval_seed_split,
            "loop_eval_dev_seed_file": checkpoint_reference(args.dev_seed_file),
            "loop_eval_validation_seed_file": checkpoint_reference(args.validation_seed_file),
            "loop_eval_final_seed_file": checkpoint_reference(args.final_seed_file),
            "loop_eval_confidence_interval": args.confidence_interval,
            "loop_eval_failure_taxonomy": args.enable_failure_taxonomy,
            "loop_target_success_rate": TARGET_SUCCESS_RATE,
            "loop_target_time_s": TARGET_TIME_S,
        },
    }
    run = wandb.init(**init_kwargs)
    try:
        table = wandb.Table(
            columns=[
                "checkpoint",
                "checkpoint_file",
                "seed_split",
                "episodes",
                "success_count",
                "success_rate",
                "success_ci95_low",
                "success_ci95_high",
                "mean_time_s_success",
                "median_time_s_success",
                "p90_time_s_success",
                "crash_rate",
                "timeout_rate",
                "mean_gates",
                "score",
                "target_met",
                "endpoint_classes",
                "success_seeds",
            ]
        )
        for index, summary in enumerate(summaries):
            train_step = checkpoint_train_step(summary, args.train_timesteps)
            log_step = args.train_timesteps + index + 1
            metrics = {
                "eval/checkpoint_train_step": train_step,
                "eval/success_rate": safe_float(summary.get("success_rate"), 0.0),
                "eval/success_ci95_low": safe_float(summary.get("success_ci95_low")),
                "eval/success_ci95_high": safe_float(summary.get("success_ci95_high")),
                "eval/success_count": safe_float(summary.get("success_count"), 0.0),
                "eval/episodes": safe_float(summary.get("episodes"), 0.0),
                "eval/mean_time_s_success": safe_float(summary.get("mean_time_s_success")),
                "eval/median_time_s_success": safe_float(summary.get("median_time_s_success")),
                "eval/p90_time_s_success": safe_float(summary.get("p90_time_s_success")),
                "eval/crash_rate": safe_float(summary.get("crash_rate"), 0.0),
                "eval/timeout_rate": safe_float(summary.get("timeout_rate"), 0.0),
                "eval/mean_gates": safe_float(summary.get("mean_gates"), 0.0),
                "eval/score": safe_float(summary.get("score"), 0.0),
                "eval/target_met": float(bool(summary.get("target_met"))),
            }
            for key, value in summary.items():
                if key.startswith("failure_rate_gate_"):
                    metrics[f"eval/{key}"] = safe_float(value)
            wandb.log(metrics, step=log_step)
            table.add_data(
                summary.get("checkpoint"),
                summary.get("checkpoint_file"),
                summary.get("seed_split"),
                summary.get("episodes"),
                summary.get("success_count"),
                safe_float(summary.get("success_rate")),
                safe_float(summary.get("success_ci95_low")),
                safe_float(summary.get("success_ci95_high")),
                safe_float(summary.get("mean_time_s_success")),
                safe_float(summary.get("median_time_s_success")),
                safe_float(summary.get("p90_time_s_success")),
                safe_float(summary.get("crash_rate")),
                safe_float(summary.get("timeout_rate")),
                safe_float(summary.get("mean_gates")),
                safe_float(summary.get("score")),
                bool(summary.get("target_met")),
                summary.get("endpoint_classes"),
                summary.get("success_seeds"),
            )

        wandb.log({"eval/summary_table": table}, step=args.train_timesteps + len(summaries) + 1)
        if trial_best is not None:
            for key in (
                "checkpoint_file",
                "seed_split",
                "episodes",
                "success_count",
                "success_rate",
                "success_ci95_low",
                "success_ci95_high",
                "mean_time_s_success",
                "median_time_s_success",
                "p90_time_s_success",
                "crash_rate",
                "timeout_rate",
                "mean_gates",
                "score",
                "target_met",
            ):
                run.summary[f"best_eval/{key}"] = trial_best.get(key)
        return run.url
    finally:
        wandb.finish()


def update_global_best(state: dict[str, Any], candidate: dict[str, Any] | None) -> None:
    """Update split-aware best records if the candidate improves hard-eval rank."""
    if candidate is None:
        return
    seed_split = str(candidate.get("seed_split") or "")
    if seed_split == "dev_seen":
        current = state.get("best_dev")
        if not isinstance(current, dict) or evaluation_rank_key(candidate) > evaluation_rank_key(current):
            state["best_dev"] = deepcopy(candidate)
        return
    if seed_split == "validation_unseen":
        current = state.get("best_validation")
        if not isinstance(current, dict) or evaluation_rank_key(candidate) > evaluation_rank_key(current):
            state["best_validation"] = deepcopy(candidate)
            state["best"] = deepcopy(candidate)
        return
    if seed_split == "final_locked":
        current = state.get("final_certified")
        if not isinstance(current, dict) or evaluation_rank_key(candidate) > evaluation_rank_key(current):
            state["final_certified"] = deepcopy(candidate)
        return

    current = state.get("best")
    if not isinstance(current, dict) or evaluation_rank_key(candidate) > evaluation_rank_key(current):
        state["best"] = deepcopy(candidate)


def choose_audit_checkpoint(args: argparse.Namespace) -> Path:
    """Choose the checkpoint used by --audit-initial-checkpoint."""
    explicit = existing_path(args.initial_checkpoint)
    if explicit is not None:
        return explicit
    latest = latest_initial_checkpoint()
    if latest is None:
        raise SystemExit("error: no level3_DR_initial checkpoint found to audit.")
    return latest.resolve()


def run_initial_checkpoint_audit(args: argparse.Namespace, state: dict[str, Any]) -> None:
    """Evaluate the starting checkpoint before training from an empty state."""
    checkpoint = choose_audit_checkpoint(args)
    checkpoint_file = checkpoint_reference(checkpoint)
    existing = state.get("initial_checkpoint_audit")
    if (
        isinstance(existing, dict)
        and existing.get("checkpoint_file") == checkpoint_file
        and existing.get("status") == "evaluated"
        and not args.force_initial_audit
    ):
        print(f"Initial checkpoint already audited: {checkpoint_file}")
        print_summary(state)
        return

    run_name = "level3_initial_checkpoint_audit"
    out_prefix = LOOP_DIR / run_name
    eval_log = out_prefix.with_name(f"{run_name}_eval.log")
    audit_split = "dev_seen" if args.eval_seed_split == "dev_then_validation" else args.eval_seed_split
    eval_command = build_eval_command(
        args,
        eval_out_prefix(out_prefix, audit_split),
        [checkpoint],
        seed_file=split_seed_file(args, audit_split),
        seed_split_name=audit_split,
    )

    audit: dict[str, Any] = {
        "created_at": utc_now(),
        "status": "planned" if args.dry_run else "evaluating",
        "checkpoint_file": checkpoint_file,
        "eval_command": command_text(eval_command),
        "eval_log": str(eval_log.relative_to(ROOT)),
        "seed_split": audit_split,
        "seed_file": checkpoint_reference(split_seed_file(args, audit_split)),
    }
    if args.dry_run:
        run_logged(eval_command, eval_log, dry_run=True)
        print(json.dumps(audit, indent=2, sort_keys=True))
        return

    state["initial_checkpoint_audit"] = audit
    write_state(args.state_path, state)

    eval_code = run_logged(eval_command, eval_log, dry_run=args.dry_run)
    audit["eval_returncode"] = eval_code
    if eval_code != 0:
        audit["status"] = "eval_failed"
        write_state(args.state_path, state)
        print(f"Initial checkpoint audit failed with return code {eval_code}.")
        return

    target = state.get("target", {})
    target_success = float(target.get("success_rate", TARGET_SUCCESS_RATE))
    target_time = float(target.get("mean_time_s_success", TARGET_TIME_S))
    split_prefix = eval_out_prefix(out_prefix, audit_split)
    summary_csv = split_prefix.with_name(split_prefix.name + "_summary.csv")
    summaries = read_summary_csv(summary_csv, target_success, target_time)
    audit["summary_csv"] = str(summary_csv.relative_to(ROOT))
    audit["summaries"] = summaries
    audit["best_summary"] = best_of(summaries)
    audit["status"] = "evaluated"
    update_global_best(state, audit["best_summary"])
    write_state(args.state_path, state)
    print_summary(state)


def print_summary(state: dict[str, Any]) -> None:
    """Print a compact state summary."""
    best = state.get("best")
    if not isinstance(best, dict):
        print("No evaluated checkpoint yet.")
        return
    print(
        "best="
        f"{best.get('checkpoint_file')} "
        f"success={safe_float(best.get('success_rate'), 0.0):.2%} "
        f"time={safe_float(best.get('mean_time_s_success'))} "
        f"crash={safe_float(best.get('crash_rate'), 0.0):.2%} "
        f"score={best.get('score')}"
    )


def run_one_iteration(args: argparse.Namespace, state: dict[str, Any]) -> str:
    """Run one train/evaluate/tune iteration."""
    selected_structural_hypothesis = choose_structural_hypothesis(args, state)
    if selected_structural_hypothesis is not None:
        apply_structural_hypothesis_args(args, selected_structural_hypothesis)

    trial_num = len(state.get("trials", [])) + 1
    if selected_structural_hypothesis is not None:
        proposal_name = sanitize_proposal_name(
            str(args.proposal_name or selected_structural_hypothesis["proposal_name"])
        )
        params = clamp_params(
            {**BASE_PARAMS, **selected_structural_hypothesis["params"]},
            relaxed=args.relaxed_reward_bounds,
        )
        reason = (
            f"Structural hypothesis {selected_structural_hypothesis['name']}: "
            f"{selected_structural_hypothesis['rationale']}"
        )
    elif args.keep_latest_params:
        proposal_name = "keep_latest_params"
        params = clamp_params(
            latest_trial_params(state) or BASE_PARAMS,
            relaxed=args.relaxed_reward_bounds,
        )
        reason = (
            "Approved continuation of the latest screened hypothesis. Reward "
            "numbers are kept unchanged; only additional training/evaluation "
            "evidence is being collected."
        )
    else:
        proposal_name, params, reason = propose_params(
            state,
            relaxed_bounds=args.relaxed_reward_bounds,
            auto_hypothesis_search=args.auto_hypothesis_search,
            plateau_trial_limit=args.plateau_trial_limit,
        )
    try:
        param_overrides = parse_param_overrides(args.param)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from None
    if param_overrides:
        params = clamp_params({**params, **param_overrides}, relaxed=args.relaxed_reward_bounds)
        reason = f"{reason} CLI overrides: {param_overrides}."
    analysis_packets = read_research_packets(args.analysis_packet)
    research_packets = read_research_packets(args.research_packet)
    approved_hypothesis_packets = read_research_packets(args.approved_hypothesis_packet)
    packet_titles = [
        *(f"analysis:{packet['title']}" for packet in analysis_packets),
        *(f"research:{packet['title']}" for packet in research_packets),
        *(f"approved:{packet['title']}" for packet in approved_hypothesis_packets),
    ]
    if packet_titles:
        reason = f"{reason} Evidence packets attached: {packet_titles}."
    if args.proposal_name:
        if not (param_overrides or approved_hypothesis_packets):
            raise SystemExit(
                "error: --proposal-name requires explicit reward --param values "
                "or --approved-hypothesis-packet provenance."
            )
        try:
            override_name = sanitize_proposal_name(args.proposal_name)
        except ValueError as exc:
            raise SystemExit(f"error: {exc}") from None
        if override_name != proposal_name:
            reason = (
                f"{reason} Proposal name overridden by main-agent decision packet: "
                f"{override_name}."
            )
            proposal_name = override_name
    training_structure_hold = build_training_structure_hold(
        args,
        selected_structural_hypothesis,
        proposal_name,
        reason,
        analysis_packets,
        research_packets,
        approved_hypothesis_packets,
    )
    if training_structure_hold is not None:
        record_hold_decision(
            args.state_path,
            state,
            training_structure_hold,
            dry_run=args.dry_run,
        )
        return "held"
    materialized_checkpoint = materialize_identity_norm_warmstart(
        selected_structural_hypothesis,
        params,
    )
    if materialized_checkpoint is not None and args.initial_checkpoint is None:
        args.initial_checkpoint = checkpoint_reference(materialized_checkpoint)
    initial_checkpoint = choose_initial_checkpoint(args, state, params)
    state_hold_decision = build_state_hold_decision(
        args,
        state,
        proposal_name,
        reason,
        param_overrides,
        initial_checkpoint,
    )
    if state_hold_decision is not None:
        record_hold_decision(
            args.state_path,
            state,
            state_hold_decision,
            dry_run=args.dry_run,
        )
        return "held"

    post_run_decision_hold = build_post_run_decision_hold(
        args,
        state,
        proposal_name,
        reason,
        initial_checkpoint,
        approved_hypothesis_packets,
    )
    if post_run_decision_hold is not None:
        record_hold_decision(
            args.state_path,
            state,
            post_run_decision_hold,
            dry_run=args.dry_run,
        )
        return "held"

    hold_decision = build_hold_decision(
        args,
        state,
        proposal_name,
        params,
        reason,
        param_overrides,
        initial_checkpoint,
    )
    if hold_decision is not None:
        record_hold_decision(args.state_path, state, hold_decision, dry_run=args.dry_run)
        return "held"

    run_name = f"level3_loop_{trial_num:03d}_{proposal_name}"
    run_dir = CHECKPOINT_ROOT / run_name
    train_command = build_train_command(args, run_name, run_dir, params, initial_checkpoint)
    log_prefix = LOOP_DIR / run_name
    train_log = log_prefix.with_name(f"{run_name}_train.log")
    eval_log = log_prefix.with_name(f"{run_name}_eval.log")
    out_prefix = log_prefix.with_name(f"{run_name}_eval")
    selected_architecture = (
        selected_structural_hypothesis.get("architecture", {})
        if selected_structural_hypothesis
        else {}
    )
    training_structure = (
        str(selected_architecture.get("policy_arch"))
        if isinstance(selected_architecture, dict) and selected_architecture.get("policy_arch")
        else "mlp_2x_tanh"
    )

    trial: dict[str, Any] = {
        "trial_id": run_name,
        "created_at": utc_now(),
        "status": "planned" if args.dry_run else "training",
        "proposal": proposal_name,
        "proposal_reason": reason,
        "train_config": args.config,
        "eval_config": args.eval_config,
        "eval_inference_module": args.eval_inference_module,
        "observation_layout": args.observation_layout,
        "allow_hidden_dim_warmstart": args.allow_hidden_dim_warmstart,
        "training_structure": training_structure,
        "architecture": selected_architecture,
        "network_capacity": {
            "hidden_dim": params.get("hidden_dim"),
            "capacity_lane": (
                "hidden512"
                if int(safe_float(params.get("hidden_dim"), 0) or 0) == 512
                else "default"
            ),
            "checkpoint_selection": "observation_layout_and_hidden_dim",
        },
        "rollout_structure": {
            "num_envs": args.num_envs,
            "num_steps": args.num_steps,
            "batch_size": args.num_envs * args.num_steps,
        },
        "keep_latest_params": args.keep_latest_params,
        "params": params,
        "initial_checkpoint": str(initial_checkpoint.relative_to(ROOT))
        if initial_checkpoint is not None and initial_checkpoint.is_relative_to(ROOT)
        else str(initial_checkpoint)
        if initial_checkpoint is not None
        else None,
        "train_command": command_text(train_command),
        "train_log": str(train_log.relative_to(ROOT)),
        "eval_log": str(eval_log.relative_to(ROOT)),
        "eval_seed_protocol": {
            "mode": args.eval_seed_split,
            "dev_seed_file": checkpoint_reference(args.dev_seed_file),
            "validation_seed_file": checkpoint_reference(args.validation_seed_file),
            "final_seed_file": checkpoint_reference(args.final_seed_file),
            "confidence_interval": args.confidence_interval,
            "failure_taxonomy": args.enable_failure_taxonomy,
            "validation_promotion": {
                "success_rate": args.validation_promotion_threshold,
                "secondary_success_rate": args.validation_promotion_secondary_success,
                "secondary_mean_gates": args.validation_promotion_mean_gates,
            },
        },
        "summaries": [],
        "best_summary": None,
        "wandb_run_id": run_name if args.wandb_enabled else None,
        "wandb_project_name": args.wandb_project_name if args.wandb_enabled else None,
        "wandb_entity": args.wandb_entity if args.wandb_enabled else None,
        "analysis_packets": analysis_packets,
        "research_packets": research_packets,
        "approved_hypothesis_packets": approved_hypothesis_packets,
        "structural_hypothesis": selected_structural_hypothesis.get("name")
        if selected_structural_hypothesis
        else None,
        "structural_hypothesis_rationale": selected_structural_hypothesis.get("rationale")
        if selected_structural_hypothesis
        else None,
        "track_boundary": {
            "target_eval_config": TARGET_EVAL_CONFIG,
            "do_not_modify_level3_track": True,
        },
        "codex_autonomous_loop": args.codex_autonomous_loop,
        "autonomy_policy": state.get("autonomy_policy"),
        "step_curve_policy": training_horizon_policy(args, state, initial_checkpoint),
        "post_run_decision_protocol": deepcopy(POST_RUN_DECISION_PROTOCOL),
        "post_run_decision_required": True,
        "post_run_required_review_roles": POST_RUN_REVIEW_ROLES,
        "main_agent_decision_packet": None,
    }

    resolve_post_run_decision_gate(state, trial, approved_hypothesis_packets)

    if args.dry_run:
        print(json.dumps(trial, indent=2, sort_keys=True))
        return "planned"

    state["trials"].append(trial)
    remember_research_packets(state, [*research_packets, *approved_hypothesis_packets])
    write_state(args.state_path, state)

    train_code = run_logged(train_command, train_log, dry_run=False)
    trial["train_returncode"] = train_code
    if train_code != 0:
        trial["status"] = "train_failed"
        write_state(args.state_path, state)
        return "failed"

    checkpoints = trial_checkpoints(
        run_name,
        run_dir,
        args.max_eval_checkpoints,
        strategy=args.eval_checkpoint_strategy,
        milestones=parse_steps_m(args.eval_milestones_m),
    )
    trial["checkpoints"] = [
        str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        for path in checkpoints
    ]
    if not checkpoints:
        trial["status"] = "no_checkpoints"
        write_state(args.state_path, state)
        return "failed"

    target = state.get("target", {})
    target_success = float(target.get("success_rate", TARGET_SUCCESS_RATE))
    target_time = float(target.get("mean_time_s_success", TARGET_TIME_S))

    trial["eval_seed_protocol"] = {
        "mode": args.eval_seed_split,
        "dev_seed_file": checkpoint_reference(args.dev_seed_file),
        "validation_seed_file": checkpoint_reference(args.validation_seed_file),
        "final_seed_file": checkpoint_reference(args.final_seed_file),
        "confidence_interval": args.confidence_interval,
        "failure_taxonomy": args.enable_failure_taxonomy,
        "validation_promotion": {
            "success_rate": args.validation_promotion_threshold,
            "secondary_success_rate": args.validation_promotion_secondary_success,
            "secondary_mean_gates": args.validation_promotion_mean_gates,
        },
    }

    if args.eval_seed_split == "dev_then_validation":
        dev_prefix = eval_out_prefix(out_prefix, "dev_seen")
        dev_log = eval_log_path(eval_log, "dev_seen")
        dev_command = build_eval_command(
            args,
            dev_prefix,
            checkpoints,
            seed_file=args.dev_seed_file,
            seed_split_name="dev_seen",
        )
        trial["eval_command"] = command_text(dev_command)
        trial["eval_commands"] = {"dev_seen": command_text(dev_command)}
        trial["eval_logs"] = {"dev_seen": str(dev_log.relative_to(ROOT))}
        trial["status"] = "evaluating_dev_seen"
        write_state(args.state_path, state)

        dev_code = run_logged(dev_command, dev_log, dry_run=False)
        trial["eval_returncode"] = dev_code
        trial["eval_returncodes"] = {"dev_seen": dev_code}
        if dev_code != 0:
            trial["status"] = "eval_failed"
            write_state(args.state_path, state)
            return "failed"

        dev_summary_csv = dev_prefix.with_name(dev_prefix.name + "_summary.csv")
        dev_summaries = read_summary_csv(dev_summary_csv, target_success, target_time)
        trial["dev_summary_csv"] = str(dev_summary_csv.relative_to(ROOT))
        trial["dev_summaries"] = dev_summaries
        update_global_best(state, best_of(dev_summaries))

        promoted_summaries = [
            summary for summary in dev_summaries if promotion_gate_met(summary, args)
        ]
        promoted_checkpoints = checkpoint_paths_for_summaries(checkpoints, promoted_summaries)
        trial["validation_promoted_checkpoints"] = [
            checkpoint_reference(path) for path in promoted_checkpoints
        ]

        if promoted_checkpoints:
            validation_prefix = eval_out_prefix(out_prefix, "validation_unseen")
            validation_log = eval_log_path(eval_log, "validation_unseen")
            validation_command = build_eval_command(
                args,
                validation_prefix,
                promoted_checkpoints,
                seed_file=args.validation_seed_file,
                seed_split_name="validation_unseen",
            )
            trial["eval_commands"]["validation_unseen"] = command_text(validation_command)
            trial["eval_logs"]["validation_unseen"] = str(validation_log.relative_to(ROOT))
            trial["status"] = "evaluating_validation_unseen"
            write_state(args.state_path, state)

            validation_code = run_logged(validation_command, validation_log, dry_run=False)
            trial["eval_returncode"] = validation_code
            trial["eval_returncodes"]["validation_unseen"] = validation_code
            if validation_code != 0:
                trial["status"] = "eval_failed"
                write_state(args.state_path, state)
                return "failed"

            validation_summary_csv = validation_prefix.with_name(
                validation_prefix.name + "_summary.csv"
            )
            summaries = read_summary_csv(validation_summary_csv, target_success, target_time)
            trial["validation_summary_csv"] = str(validation_summary_csv.relative_to(ROOT))
            trial["validation_summaries"] = summaries
            trial["summary_csv"] = trial["validation_summary_csv"]
            trial["best_eval_split"] = "validation_unseen"
        else:
            summaries = dev_summaries
            trial["summary_csv"] = trial["dev_summary_csv"]
            trial["best_eval_split"] = "dev_seen"
    else:
        eval_split = args.eval_seed_split
        split_prefix = eval_out_prefix(out_prefix, eval_split)
        split_log = eval_log_path(eval_log, eval_split)
        eval_command = build_eval_command(
            args,
            split_prefix,
            checkpoints,
            seed_file=split_seed_file(args, eval_split),
            seed_split_name=eval_split,
        )
        trial["eval_command"] = command_text(eval_command)
        trial["eval_commands"] = {eval_split: command_text(eval_command)}
        trial["eval_logs"] = {eval_split: str(split_log.relative_to(ROOT))}
        trial["status"] = f"evaluating_{eval_split}"
        write_state(args.state_path, state)

        eval_code = run_logged(eval_command, split_log, dry_run=False)
        trial["eval_returncode"] = eval_code
        trial["eval_returncodes"] = {eval_split: eval_code}
        if eval_code != 0:
            trial["status"] = "eval_failed"
            write_state(args.state_path, state)
            return "failed"

        summary_csv = split_prefix.with_name(split_prefix.name + "_summary.csv")
        summaries = read_summary_csv(summary_csv, target_success, target_time)
        trial["summary_csv"] = str(summary_csv.relative_to(ROOT))
        trial[f"{eval_split}_summary_csv"] = trial["summary_csv"]
        trial[f"{eval_split}_summaries"] = summaries
        trial["best_eval_split"] = eval_split

    trial["summaries"] = summaries
    trial_best = best_of(summaries)
    if trial_best is not None:
        trial_best["observation_layout"] = args.observation_layout
    trial["best_summary"] = trial_best
    trial["wandb_url"] = log_eval_summaries_to_wandb(args, run_name, summaries, trial_best)
    trial["status"] = "target_met" if trial_best and trial_best["target_met"] else "evaluated"
    update_global_best(state, trial_best)
    write_state(args.state_path, state)
    print_summary(state)
    return "target_met" if trial_best and trial_best["target_met"] else "completed"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument(
        "--python-command",
        default=sys.executable,
        help=(
            "Python command used for train/eval subprocesses. Example: "
            '--python-command "pixi run -e gpu python"'
        ),
    )
    parser.add_argument("--config", default=TARGET_EVAL_CONFIG)
    parser.add_argument("--eval-config", default=TARGET_EVAL_CONFIG)
    parser.add_argument(
        "--eval-inference-module",
        choices=["ppo_level2_inference", "ppo_level3_inference"],
        default="ppo_level3_inference",
        help="Inference controller module used for hard checkpoint evaluation.",
    )
    parser.add_argument(
        "--observation-layout",
        choices=list(SUPPORTED_OBSERVATION_LAYOUTS),
        default=WORLD_HISTORY_OBSERVATION_LAYOUT,
        help=(
            "Observation layout used for training and expected by checkpoint "
            "evaluation. The default keeps compatibility with existing 103-dim "
            "Level3 checkpoints; the local-obstacle v5 layout is an approved "
            "structural observation experiment."
        ),
    )
    parser.add_argument("--max-iterations", type=int, default=1)
    parser.add_argument("--train-timesteps", type=int, default=DEFAULT_TRAIN_TIMESTEPS)
    parser.add_argument("--checkpoint-interval", type=int, default=DEFAULT_CHECKPOINT_INTERVAL)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=32)
    parser.add_argument("--jax-device", default="gpu")
    parser.add_argument("--cuda", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--wandb-enabled", action="store_true")
    parser.add_argument("--wandb-project-name", default="ADR-PPO-Racing-Level3")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-mode", default="online", choices=["online", "offline", "disabled"])
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Start this trial from random initialization instead of an existing checkpoint.",
    )
    parser.add_argument("--initial-checkpoint")
    parser.add_argument(
        "--allow-hidden-dim-warmstart",
        action="store_true",
        help=(
            "Allow an explicit block-copy warm-start from a narrower 2-layer "
            "PPO MLP checkpoint into a wider hidden_dim target. Intended only "
            "for named capacity structural lanes."
        ),
    )
    parser.add_argument(
        "--resume-from-best", action=argparse.BooleanOptionalAction, default=True
    )
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--eval-seeds", type=int, default=20)
    parser.add_argument(
        "--eval-seed-split",
        choices=["dev_then_validation", "dev_seen", "validation_unseen", "final_locked"],
        default="dev_then_validation",
        help=(
            "Checkpoint evaluator seed protocol. The default screens on dev_seen "
            "and promotes promising checkpoints to validation_unseen."
        ),
    )
    parser.add_argument("--dev-seed-file", type=Path, default=DEFAULT_DEV_SEED_FILE)
    parser.add_argument("--validation-seed-file", type=Path, default=DEFAULT_VALIDATION_SEED_FILE)
    parser.add_argument("--final-seed-file", type=Path, default=DEFAULT_FINAL_SEED_FILE)
    parser.add_argument(
        "--validation-promotion-threshold",
        type=float,
        default=DEFAULT_VALIDATION_PROMOTION_THRESHOLD,
        help="Promote a dev_seen checkpoint to validation when success_rate reaches this value.",
    )
    parser.add_argument(
        "--validation-promotion-secondary-success",
        type=float,
        default=DEFAULT_VALIDATION_PROMOTION_SECONDARY_SUCCESS,
        help="Secondary promotion success threshold used with --validation-promotion-mean-gates.",
    )
    parser.add_argument(
        "--validation-promotion-mean-gates",
        type=float,
        default=DEFAULT_VALIDATION_PROMOTION_MEAN_GATES,
        help="Secondary promotion mean-gates threshold.",
    )
    parser.add_argument(
        "--confidence-interval",
        choices=["none", "wilson"],
        default="wilson",
        help="Evaluator confidence interval method for success_rate.",
    )
    parser.add_argument(
        "--enable-failure-taxonomy",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Record endpoint/failure taxonomy during hard checkpoint evaluation.",
    )
    parser.add_argument(
        "--final-eval-explicit-unlock",
        action="store_true",
        help="Required before evaluating on final_locked seeds.",
    )
    parser.add_argument("--max-eval-checkpoints", type=int, default=4)
    parser.add_argument(
        "--eval-checkpoint-strategy",
        choices=["milestone", "latest"],
        default="milestone",
        help=(
            "Select which step checkpoints to hard-evaluate. 'milestone' keeps "
            "Level2-calibrated 30M/60M/90M-style checkpoints plus recent steps; "
            "'latest' preserves the old latest-N behavior."
        ),
    )
    parser.add_argument(
        "--eval-milestones-m",
        default=DEFAULT_EVAL_MILESTONES_M,
        help="Comma-separated checkpoint milestones in millions for milestone eval.",
    )
    parser.add_argument(
        "--plateau-trial-limit",
        type=int,
        default=DEFAULT_PLATEAU_TRIAL_LIMIT,
        help=(
            "Hold automatic tuning after this many consecutive evaluated trials "
            "without success_rate or mean_gates improvement."
        ),
    )
    parser.add_argument(
        "--long-run-threshold",
        type=int,
        default=LONG_RUN_TIMESTEP_THRESHOLD,
        help=(
            "Runs above this many timesteps require a prior screened improvement "
            "unless --allow-long-run-without-improvement is passed."
        ),
    )
    parser.add_argument(
        "--allow-repeat-params",
        action="store_true",
        help="Allow a run even when proposed reward params did not change after bounds.",
    )
    parser.add_argument(
        "--allow-plateau-continuation",
        action="store_true",
        help="Allow automatic continuation despite consecutive no-improvement trials.",
    )
    parser.add_argument(
        "--allow-long-run-without-improvement",
        action="store_true",
        help="Allow >long-run-threshold timesteps without a prior screened improvement.",
    )
    parser.add_argument(
        "--allow-step-curve-maturation",
        action="store_true",
        help=(
            "Allow a >long-run-threshold maturation chunk when the selected "
            "initial checkpoint already has promising hard-eval evidence "
            "(non-zero success or enough mean gates), following the Level2 "
            "checkpoint step-curve packet."
        ),
    )
    parser.add_argument(
        "--keep-latest-params",
        action="store_true",
        help=(
            "Reuse the latest trial reward numbers without automatic reward "
            "proposal. Use after analysis says the current hypothesis only needs "
            "more training evidence."
        ),
    )
    parser.add_argument(
        "--auto-hypothesis-search",
        action="store_true",
        help=(
            "After plateau, automatically rotate to an absolute reward-number "
            "hypothesis instead of holding for a human-authored --param set."
        ),
    )
    parser.add_argument(
        "--structural-hypothesis",
        choices=["none", *STRUCTURAL_HYPOTHESES.keys()],
        default="none",
        help=(
            "Apply a named structural hypothesis with its observation layout, "
            "training horizon, parameter defaults, and evidence packets."
        ),
    )
    parser.add_argument(
        "--auto-structural-search",
        action="store_true",
        help=(
            "Automatically choose the next untried approved structural hypothesis "
            "before falling back to reward-number tuning."
        ),
    )
    parser.add_argument(
        "--relaxed-reward-bounds",
        action="store_true",
        help="Use wider reward-number parameter bounds for exploratory search.",
    )
    parser.add_argument(
        "--codex-autonomous-loop",
        action="store_true",
        help=(
            "Record that this run is supervised by an unattended Codex main agent. "
            "Implies --auto-hypothesis-search and --relaxed-reward-bounds, but "
            "does not bypass post-run analysis, structural-lane records, or long-run "
            "guards."
        ),
    )
    parser.add_argument(
        "--escalation-min-evaluated-trials",
        type=int,
        default=DEFAULT_ESCALATION_MIN_EVALUATED_TRIALS,
        help=(
            "Legacy structural-escalation threshold kept for historical trial "
            "audit compatibility."
        ),
    )
    parser.add_argument(
        "--escalation-min-distinct-reward-hypotheses",
        type=int,
        default=DEFAULT_ESCALATION_MIN_DISTINCT_REWARD_HYPOTHESES,
        help=(
            "Legacy distinct reward-hypothesis threshold kept for historical "
            "trial audit compatibility."
        ),
    )
    parser.add_argument(
        "--escalation-min-total-timesteps",
        type=int,
        default=DEFAULT_ESCALATION_MIN_TOTAL_TIMESTEPS,
        help=(
            "Legacy reward-only timestep threshold kept for historical trial "
            "audit compatibility."
        ),
    )
    parser.add_argument(
        "--escalation-min-plateau-trials",
        type=int,
        default=DEFAULT_ESCALATION_MIN_PLATEAU_TRIALS,
        help=(
            "Minimum consecutive no-improvement evaluated trials before "
            "structural escalation review may be considered."
        ),
    )
    parser.add_argument(
        "--skip-initial-audit",
        action="store_true",
        help="Do not require an initial checkpoint audit before the first training trial.",
    )
    parser.add_argument(
        "--audit-initial-checkpoint",
        action="store_true",
        help="Evaluate the latest level3_DR_initial checkpoint and write it to state.",
    )
    parser.add_argument(
        "--force-initial-audit",
        action="store_true",
        help="Re-run --audit-initial-checkpoint even when a matching audit exists.",
    )
    parser.add_argument(
        "--allow-unanalysed-multi-iteration",
        action="store_true",
        help=(
            "Allow more than one train/eval iteration without an intervening "
            "post-run W&B/evaluator analysis packet."
        ),
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help=(
            "Override an active reward/training parameter for this trial, "
            "e.g. --param gate_axis_coef=24."
        ),
    )
    parser.add_argument(
        "--proposal-name",
        help=(
            "Override the recorded proposal/run suffix for an approved "
            "hypothesis. Requires explicit --param values or an "
            "--approved-hypothesis-packet."
        ),
    )
    parser.add_argument(
        "--research-packet",
        action="append",
        default=[],
        help=(
            "Attach a source-backed research/synthesis markdown file to this trial "
            "for tuning provenance. By itself this does not bypass plateau guards."
        ),
    )
    parser.add_argument(
        "--analysis-packet",
        action="append",
        default=[],
        help=(
            "Attach a post-run analysis markdown/json file for provenance. "
            "Analysis packets never bypass plateau guards."
        ),
    )
    parser.add_argument(
        "--approved-hypothesis-packet",
        action="append",
        default=[],
        help=(
            "Attach a main-agent approved decision packet. This may satisfy "
            "plateau/state guards when paired with explicit reward --param values "
            "or a named structural command."
        ),
    )
    parser.add_argument(
        "--override-state-hold",
        action="store_true",
        help=(
            "Bypass a state-recorded hold only after explicit user approval. "
            "Must be paired with reward --param values, or with a structural "
            "command and --approved-hypothesis-packet."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run the loop."""
    args = parse_args()
    args.default_train_timesteps = DEFAULT_TRAIN_TIMESTEPS
    args.default_checkpoint_interval = DEFAULT_CHECKPOINT_INTERVAL
    if args.eval_config != TARGET_EVAL_CONFIG:
        raise SystemExit(
            f"error: Level3 target evaluation is immutable; "
            f"--eval-config must be {TARGET_EVAL_CONFIG}."
        )
    if args.eval_seed_split == "final_locked" and not args.final_eval_explicit_unlock:
        raise SystemExit(
            "error: final_locked seeds require --final-eval-explicit-unlock and "
            "must not be used by the automatic training loop."
        )
    if args.codex_autonomous_loop:
        args.auto_structural_search = True
        args.auto_hypothesis_search = True
        args.relaxed_reward_bounds = True
        if args.allow_unanalysed_multi_iteration:
            raise SystemExit(
                "error: --codex-autonomous-loop requires analysis between iterations; "
                "do not combine it with --allow-unanalysed-multi-iteration."
            )
    if args.keep_latest_params:
        if args.param:
            raise SystemExit(
                "error: --keep-latest-params reuses existing reward numbers; "
                "do not combine it with reward --param overrides."
            )
        args.allow_repeat_params = True
    args.state_path = args.state_path.resolve()
    for attr in ("dev_seed_file", "validation_seed_file", "final_seed_file"):
        path = getattr(args, attr)
        if path is None:
            continue
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            raise SystemExit(f"error: seed manifest not found for --{attr.replace('_', '-')}: {path}")
        setattr(args, attr, path.resolve())
    args.python_command = shlex.split(args.python_command)
    try:
        parse_steps_m(args.eval_milestones_m)
    except ValueError as exc:
        raise SystemExit(f"error: {exc}") from None
    state = load_state(args.state_path)
    if args.audit_initial_checkpoint:
        run_initial_checkpoint_audit(args, state)
        return

    target = state.get("target", {})
    target_success = float(target.get("success_rate", TARGET_SUCCESS_RATE))
    target_time = float(target.get("mean_time_s_success", TARGET_TIME_S))

    best = state.get("best")
    if isinstance(best, dict) and target_met(best, target_success, target_time):
        print("Target already met.")
        print_summary(state)
        return
    if args.max_iterations > 1 and not args.allow_unanalysed_multi_iteration:
        raise SystemExit(
            "error: post-run analysis is required between Level3 loop iterations. "
            "Use --max-iterations 1, then run scripts/analyze_level3_ppo_trial.py. "
            "Pass --allow-unanalysed-multi-iteration only for an explicitly accepted "
            "blind run without analysis."
        )

    for _ in range(max(args.max_iterations, 0)):
        result = run_one_iteration(args, state)
        if result == "target_met":
            print("Target met.")
            return
        if result == "held":
            return

    if not args.dry_run:
        print_summary(state)


if __name__ == "__main__":
    main()
