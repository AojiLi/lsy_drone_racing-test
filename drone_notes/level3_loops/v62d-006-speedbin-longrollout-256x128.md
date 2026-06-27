# v62d_006 这轮做了什么

这一轮不是训练 Level3 赛道本身，而是在训练底层 PPO tracker：

```text
上层 planner 给一段 reference trajectory
PPO tracker 负责稳、准、按速度地跟过去
```

v62d_006 改的东西很窄：

```text
原来: 1024 个环境 x 32 步
这次: 256 个环境 x 128 步
```

通俗说，就是让 PPO 每次更新时看更长一段时间，希望它能更好理解：

```text
慢慢减速
刹车/停稳
低速穿过
再恢复速度
```

## 结果

最好的 checkpoint 是 20M：

```text
lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m/v62d_006_speedbin_longrollout_256x128_30m_step_020000000.pkl
```

20M 的指标：

```text
position error: 0.1964
cross-track error: 0.1640
velocity error: 0.7789
done mean: 0.0
```

它说明飞机跟轨迹的位置很不错，也没有提前结束；但是速度跟踪还不够好。

## 为什么不继续用 final

30M/final 明显变差：

```text
20M velocity error: 0.7789
final velocity error: 1.0318
```

所以这轮不能说“训越久越好”。真正有用的是 20M，不是 final。

## 是否超过旧基线

没有达到 promotion。

原因是：

```text
比 v62c 7M default:
  位置更好，但速度反而差 5.3%

比 v62d_004 5M:
  位置、横向、速度都略差一点
```

所以 v62d_006 证明了长 rollout 可以跑、数学路径也没坏，但它不是新的最好路线。

## 下一步

下一轮建议做组合实验：

```text
v62d_007_speedbin_velocity_coef_2x
```

意思是把两个之前有用但单独不够强的信号合起来：

```text
speed_bin_balanced 轨迹生成器
+ velocity error 系数加到 1.2
```

并且回到更快的训练结构：

```text
1024 envs x 32 steps
```

这轮仍然不加过门奖励、不加赛道进度奖励、不改 Level3 赛道。目标还是训练一个干净的底层 tracker。
