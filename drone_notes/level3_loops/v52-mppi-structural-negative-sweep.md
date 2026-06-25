# v52 MPPI 结构试验负结果

这轮只看 MPPI，不碰 PPO，也没有生成 teacher data。

结论很直接：当前这个 MPPI 版本还不能靠调小参数、改一点 guide、加 samples 来跑通 Level3。

保留下来的 MPPI baseline 还是：

- smoke 101-105：0% 完赛，平均 0.80 个门；
- dev 1-10：0% 完赛，平均 0.20 个门；
- 主要失败是撞门框和近门障碍。

这轮试过但都没保留：

- 门坐标速度控制；
- 门前刹车/居中；
- 门框 clearance cost；
- 更大的 roll/pitch 权限；
- 去掉动作低通；
- 更低 MPPI temperature；
- 1024 samples；
- gate-axis pure pursuit；
- yaw 对齐；
- 姿态响应 rollout；
- 多分支 guide。

通俗讲，飞机不是“不知道门在哪”。它会飞到门附近，但经常带着横向或高度速度撞到门框。当前 MPPI 的内部预测模型太粗，guide 又太强，导致它更像是在一条手写路线附近抖动，而不是在真正规划一条能穿门避障的轨迹。

下一步应该开 v53：重新设计 MPPI/controller。重点不是再加一个 penalty，而是先做一个更可靠的 gate-aware 几何控制器和 aperture-point 选择，让它至少稳定过第一门，再考虑完整 MPPI 或 teacher data。
