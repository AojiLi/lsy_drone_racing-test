# v60：把干净 command reward 和旧 reward 分开

这次改动是为了让 v60 更干净。

之前虽然 gate reward 系数是 0，但 v60 还是走同一个 `ReferenceTrackerReward`
公式。那个公式里面还写着：

```text
gate_center
gate_x_progress
gate_cross_bonus
gate_recover_bonus
gate_linger_penalty
obstacle_penalty
```

这会让人误会：好像 v60 仍然有 gate / obstacle reward。

现在改成两条路：

```text
ReferenceCommandReward
  v60 专用
  只教 tracker 听懂低层运动命令

ReferenceTrackerReward / LegacyTrackerReward
  旧 v1/v2/gate_aperture 兼容
```

v60 的 `ReferenceCommandReward` 只包含：

```text
位置误差
速度误差
heading 误差
动作大小
动作变化
靠近 reference 的 progress
hold/brake 速度惩罚
slow-through 速度惩罚
slow-through 停死惩罚
recover 速度恢复惩罚
crash penalty
```

它不再计算这些东西：

```text
gate reward
obstacle reward
finish reward
race progress
stage progress
```

通俗说：

```text
旧工具箱还留着
但 v60 不再从旧工具箱里拿 gate/obstacle 那些工具
```

trainer smoke 已确认新版 checkpoint 里写的是：

```text
reward_model = reference_command_reward
observation_layout = level3_reference_tracker_command_v3
obs_dim = 56
gate / obstacle coefficients = 0
```

下一步应该重跑一次 bounded v60 smoke，然后再考虑 8M maturation。
