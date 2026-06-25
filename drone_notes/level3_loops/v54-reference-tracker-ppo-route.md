# v54 reference-tracker PPO 路线

这轮决定把主路从 v53 的“Level2 PPO 虚拟门包装”切到 v54：

```text
上层 planner 负责路线和局部轨迹
PPO 只负责跟踪 reference trajectory
```

## 为什么换路线

v53 已经证明代码能跑，action 也是 finite，但在 `101-105` 的 smoke 里：

- 成功率：0%
- 平均过门数：0
- 失败都卡在第一门

通俗说：Level2 PPO 会飞，但它不是被训练成 reference tracker 的。我们把 planner
reference 硬包装成“虚拟门”，它能靠近第一门，但门口居中和穿门动作不稳定。

## v54 的核心思路

不要让 PPO 自己想整条 Level3 赛道。

拆成两层：

```text
planner:
  远处用 nominal gate 粗略导航
  接近 0.7m-1.0m 主动减速
  真门/障碍物可见后重新生成局部轨迹

PPO tracker:
  只看 reference point / velocity / heading / gate error / obstacle distance
  输出 roll / pitch / yaw / thrust
```

这样 PPO 学的是一个简单得多的任务：

```text
悬停
跟点
跟低速轨迹
对准 heading
穿一个局部门洞
避开局部障碍物
```

## 下一步不是长训练

下一步应该先实现 v54 的训练/评估支撑：

1. reference trajectory generator；
2. tracker observation；
3. tracker reward；
4. tracker PPO training entrypoint；
5. hover / point tracking / gate aperture smoke；
6. Level3 `101-105` smoke。

只有 smoke 出现非零第一门进展，才值得跑 dev `1-20` 或更长训练。
