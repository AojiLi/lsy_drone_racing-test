# v55 tracker 改成并行 PPO

这次 loop 先停在了一个关键工程问题上：不是 reward 或网络还没调好，而是
tracker 的训练脚本还是单环境 PPO。

通俗说，之前的 trainer 是：

```text
1 架飞机自己飞 1M 步
```

这太慢了。实际跑 hover 的 1M 训练时，约 11 分钟才写出 250k checkpoint。
如果按这个速度跑完整 12 阶段，会非常不现实。

而之前 Level2/Level3 PPO 的训练方式是：

```text
1024 个环境同时飞
每个环境飞 32 步
一次 PPO update 收集 32768 个样本
```

所以这次做的事情是把 tracker trainer 也改成这种并行采样模式。

现在 tracker trainer 支持：

```text
--num-envs 1024
--num-steps 32
--jax-device gpu
```

并且已经做过一个 1024 并行 smoke：

```text
1024 envs x 32 steps = 32768 env steps
```

这个 smoke 成功跑完并写出了 checkpoint。它只证明并行训练管线能跑，不代表
hover 已经学会。

下一步应该重新跑 hover 的正式 maturation：

```text
hover
1M env steps
1024 envs x 32 steps
250k checkpoint interval
```

如果之后发现 32 步太短，时间信用分配不够，可以改成：

```text
256 envs x 128 steps
```

这样每次 PPO update 还是 32768 个样本，但每个环境连续飞得更久，更适合需要
连续控制记忆的阶段。

结论：这次不是在判断 hover 学没学会，而是在修训练速度和训练结构。修完后，
tracker loop 才真正适合跑 12 阶段。
