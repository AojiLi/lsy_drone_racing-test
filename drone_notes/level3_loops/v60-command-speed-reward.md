# v60：给 tracker 加一点“听懂命令”的速度奖励

你的判断是对的：v60 不能只靠“离 reference 点近一点”来学。

底层 PPO tracker 现在要学的不是过门，而是这些低层动作能力：

```text
该走就走
该刹就刹
该慢速穿过就慢速穿过
该恢复速度就平滑恢复
```

所以这次加的不是 gate reward，而是 command reward：

```text
hold_or_brake:
  速度超过 0.12 m/s 就惩罚

low_speed_through:
  速度偏离 desired_speed 就惩罚
  速度太低、停死也惩罚

recover_speed:
  恢复速度偏离 desired_speed 就惩罚
```

现在默认系数是：

```text
semantic_brake_speed_coef = 1.0
semantic_slow_speed_coef = 0.8
semantic_slow_stop_coef = 0.8
semantic_recover_speed_coef = 0.4
```

同时保留 v60 的边界：

```text
不加 gate pass bonus
不加 aperture crossing bonus
不加 finish bonus
不加 race progress
不加 stage progress
不改 level3.toml
```

通俗说：

```text
不是教 PPO 自己过门
而是教 PPO 听 planner 的低层驾驶指令
```

因为 reward 默认值变了，之前的 4096-step smoke 已经不代表新版 v60。下一步应该先
重跑一次 bounded v60 smoke，再考虑 8M 正式 maturation。
