# v55 zigzag attempt001 做了什么

这一轮是在训练底层 PPO tracker 的第 10 个能力：跟随更急一点的 zigzag / lemniscate 轨迹。

通俗说，就是让飞机不只是会飞直线、L 形和圆滑曲线，还要能跟着更频繁转向的小轨迹走，而且不能左右乱甩。

## 结果

这轮通过了。

我评估了从 1M 到 11M 以及 final 的所有 checkpoint。所有 checkpoint 都是：

- 路径完成率：100%
- crash：0%
- 动作都是 finite

最后选的是 8M checkpoint：

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

它的指标是：

```text
completion: 100%
crash: 0%
mean cross-track error: 0.099 m
p90 cross-track error: 0.285 m
mean action delta: 0.0105
p90 action delta: 0.0145
```

## 为什么不选 final

final 的轨迹误差更低一点，但是动作变化更大。现在我们训练的是底层 tracker，目标不是“极限贴线”，而是“稳定、平滑、可靠地跟 reference 走”。

所以我选了 8M checkpoint。它已经很准，而且动作更平滑，更适合作为下一阶段 gate aperture 训练的起点。

## 下一步

下一阶段是 `gate_aperture_reference`。

这一步会开始让 tracker 练：

```text
门前点 -> 门洞中心 -> 门后恢复点
```

这仍然不是完整 Level3 比赛，而是一个“过门局部动作”的专项考试。等它也通过，再做 planner integration smoke，最后才考虑真正接上上层 planner 去跑 `config/level3.toml`。
