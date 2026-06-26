# v56 几何 planner 门前穿越调参 loop

现在不是“要不要 planner”的阶段了，而是进入一个很适合 loop 的阶段：

```text
每轮只改几何 planner 的门前策略
固定 seeds 101-120
固定 500 steps
看 trace 指标是否变好
```

当前基线：

```text
first-gate progress = 20/20
gate0 pass = 3/20
contact = 15/20
```

v56 的目标先不是完赛，而是把第一道门变稳定：

```text
gate0 pass >= 10/20
contact <= 8/20
first-gate progress = 20/20
config/level3.toml 不变
```

这个 loop 只做四类 planner 调参：

```text
1. align 更稳：Y/Z 没对准就不要进入 cross
2. cross 更慢：让 tracker 有时间修正
3. 偏太远就回退：靠近门平面但偏出门洞时，先回 pre-gate 对准
4. recover 等真实过门：不能只看 local_x，就以为已经过门
```

它不训练 PPO，不换 checkpoint，不改 reward，不改 Level3 赛道。  
通俗讲：先把“门前慢下来、对准、穿过去”这件事调成稳定动作。
