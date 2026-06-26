# v58 语义轨迹跟踪支持预检

这次不是训练，也不是让飞机直接去跑 Level3。

这次做的是把底层 PPO tracker 的“接口”升级好，让它以后不只是看到：

```text
去这个点
```

而是能看到：

```text
这个点是路过点 through
这个点要刹车/停稳 brake_or_hold
这个点要低速穿过 slow_through
这个点是恢复速度 recover
```

## 为什么要做这个

之前 v57a 已经把 planner 的 reference jump 从大跳变压小了，但是 gate0
pass 没有明显变好，contact 还是很高。

这说明问题可能不是单纯“路线画得不连续”，而是底层 tracker 不知道每个点的语义。

比如 planner 说：

```text
门前这个点：慢下来，对准
门洞这个点：慢慢穿，不要停死
门后这个点：恢复
```

如果 PPO 只看到一个普通 reference point，它可能把所有点都当成“冲过去的点”，于是门前刹不住。

## 这次改了什么

保留旧接口：

```text
level3_reference_tracker_v1
obs_dim = 65
```

新增 v58 语义接口：

```text
level3_reference_tracker_semantic_v2
obs_dim = 72
```

新增的 7 维大概是：

```text
waypoint type one-hot: through / brake_or_hold / slow_through / recover
stop_signal
brake_mask
slow_through_mask
```

也就是说，PPO 以后能明确知道“这个点到底该怎么飞”。

## 兼容性

旧 v55 checkpoint 没有被破坏。

当前这个 checkpoint 仍然可以正常按旧 v1 加载：

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/
  zigzag_or_lemniscate_tracking/
  v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

旧 planner smoke 也仍然走旧 v1，不会突然变成 72 维。

## 一个重要限制

因为 v58 的 observation 从 65 维变成 72 维，所以旧 v55 checkpoint
不能直接拿来当 v58 初始模型。

下一步有两个选择：

```text
1. v58 semantic tracker 从零开始训练
2. 之后专门写一个 v1 -> v2 权重迁移器
```

目前更稳的是先从零做一个很短的 v58 preflight，确认训练、W&B、checkpoint、evaluator 都能跑。

## 检查结果

这次 focused tests 通过：

```text
33 passed, 1 warning
```

还做了两个小 smoke：

```text
v58 semantic task tiny training 可以保存 checkpoint
旧 v55 planner smoke 仍然 finite
```

这里的 tiny training 不是学习效果，只是检查管线。

## 下一步

下一步应该开启：

```text
v58 semantic_planner_reference preflight
```

目标是确认：

```text
语义 observation 能训练
W&B 能记录
checkpoint metadata 正确
evaluator 能读 v2 checkpoint
semantic metrics 能输出
```

还不是 Level3 长训练。

如果 preflight 干净，再进入真正的 v58 semantic tracker maturation，比如 8M 步，并每 1M 做 checkpoint 评估。
