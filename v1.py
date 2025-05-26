import numpy as np
import matplotlib.pyplot as plt

# 参数设置
a = 1       # 螺线缩放系数
b = 0.2     # 螺线增长率
theta = np.linspace(0, 8*np.pi, 1000)  # 角度范围

# 等角螺线计算
r = a * np.exp(b * theta)
x = r * np.cos(theta)
y = r * np.sin(theta)

# 创建图形
plt.figure(figsize=(10, 10))
ax = plt.subplot(111, projection='polar')
ax.plot(theta, r, 'b-', linewidth=2, label='等角螺线 r = e^{0.2θ}')

# 绘制12等分直线
for k in range(12):
    angle = k * np.pi / 6  # 每30度一条线
    ax.plot([angle, angle], [0, r.max()], 'r--', alpha=0.5)
    # 标注角度
    ax.text(angle, r.max()*1.05, f"{k*30}°", ha='center')

ax.set_rticks(np.linspace(0, r.max(), 5))  # 径向刻度
ax.grid(True)
ax.set_title("等角螺线与十二等分直线", pad=20)
ax.legend(loc='upper right')
plt.tight_layout()
plt.show()