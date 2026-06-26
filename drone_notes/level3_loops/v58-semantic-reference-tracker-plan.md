# v58：不是训练“追点”，而是训练“理解 reference 语义”

v57a 已经把 planner 的急跳问题修掉了：

```text
phase3 -> phase4 reference jump：0.740m -> 0.280m
reference error：0.783m -> 0.340m
action delta：0.727 -> 0.491
```

但是 gate 结果没有变好：

```text
gate0 pass：2/20
contact：20/20
phase4 实际速度还是偏高
```

这说明问题不只是“planner 路线画得太突然”。现在更像是：

```text
tracker 知道要去哪，
但不知道这个点到底是要路过、刹车、慢速穿越，还是恢复速度。
```

## v58 的关键变化

v58 不应该只是训练：

```text
给一个点，飞过去
```

而应该训练：

```text
给一段带语义的 reference trajectory，
PPO 按语义飞。
```

planner 应该告诉 PPO：

```text
reference_point
next_point
lookahead_point
desired_velocity
desired_speed
desired_heading
waypoint_type / stop_signal / brake_mask
```

通俗说，不只是：

```text
你去哪
```

还要告诉它：

```text
这个点是路过点，还是刹车点？
到这里要停稳，还是慢慢穿过去？
后面还要往哪走？
```

## 建议的 waypoint 类型

```text
through
    路过点，保持速度平滑穿过去

brake_or_hold
    刹车/对准点，速度降到 0.0-0.1m/s，稳定住

slow_through
    低速穿越点，不停死，但要慢慢穿，约 0.25-0.35m/s

recover
    门后恢复点，逐渐恢复速度
```

## 为什么这重要

如果所有 reference point 看起来都一样，PPO 很可能学成：

```text
每个点都冲过去
```

这样在 free-space 里可能看起来还行，但到了 Level3 门前就会：

```text
刹不住
过冲
速度压不下来
撞门/撞障碍
```

所以 v58 的目标应该是：

```text
让底层 tracker 学会“按 reference 的语义飞”，
而不是只学“朝 reference 的位置飞”。
```

## 下一步

下一条 goal 最好先做 builder/checker-gated 的 v58 semantic support：

```text
1. 检查当前 observation 是否已经能表达 waypoint 语义
2. 如果不能，做最小 observation 扩展
3. 添加 semantic reference 训练任务
4. 添加对应 reward / evaluator metrics
5. smoke 通过后，再开始长训练
```

这一步仍然不能改 `config/level3.toml`。
