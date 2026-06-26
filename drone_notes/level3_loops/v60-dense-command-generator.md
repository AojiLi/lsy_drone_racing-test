# v60 dense command generator

这轮做的事情很具体：不是训练，也不是改 reward，而是把 v60 的训练
reference 生成方式改对。

之前的问题是，PPO 看到的 reference 像几个稀疏点：

```text
去这里
再去那里
```

这样它可能还是学成“追点”，不知道什么时候该刹车、什么时候该慢慢穿、
什么时候该恢复速度。

现在改成：

```text
连续小轨迹 + 期望速度 + 期望方向 + command 类型
```

移动阶段的 `desired_velocity` 沿着 `current -> lookahead`，也就是沿轨迹飞。
刹车阶段的 `current / next / lookahead` 都挤在刹车点附近，速度接近 0。
低速穿越阶段给很密、很慢、连续的小轨迹。恢复阶段速度平滑回升。

训练时每个 episode 的轨迹还会随机方向、长度、高度、曲率、速度和阶段时长，
避免 PPO 背一条固定路线。

这对 Level3 的意义是：

```text
planner 以后给一小段轨迹
PPO tracker 知道该怎么稳稳跟过去
```

这轮没有改 `config/level3.toml`，没有加 gate reward，也没有让 PPO 学过门语义。
它还是一个干净的底层 tracker 基线。

检查结果：

```text
ruff passed
pytest 41 passed
1024-step trainer smoke passed
checkpoint-backed evaluator smoke passed plumbing
stage gate 未通过是预期，因为 1024 steps 不是学习训练
```

下一步应该正式跑 v60 的 8M maturation，看这个更合理的 generator 能不能把
brake、slow-through、recover 学出来。
