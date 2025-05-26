import numpy as np
import matplotlib.pyplot as plt

# Set up polar plot with logarithmic radial scale
fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(111, polar=True)

# Spiral parameters
n_rotations = 5  # 增加圈数到5圈，模拟更多八度
b = np.log(2) / (2 * np.pi)  # Growth rate for doubling each rotation (e^(bθ))
theta = np.linspace(0, 2 * np.pi * n_rotations, 1000)
r = np.exp(b * theta)  # Logarithmic spiral r = e^(bθ)

# Create logarithmic radial scale
ax.set_rscale('log')
# 径向刻度从 2^0 开始，到 2^n_rotations
ax.set_rticks([2**n for n in range(n_rotations + 1)])
# 去掉径向刻度的数字标签，或者只保留 C1, C2, C3, C4, C5
ax.set_yticklabels([]) # 移除所有径向刻度标签，我们手动添加

# Plot the logarithmic spiral (blue)
ax.plot(theta, r, 'b-', linewidth=2, alpha=0.7)

# Create 12 divisions (每个音程30°，一个八度12个半音)
angles = np.linspace(0, 2 * np.pi, 13)  # 13 points for 12 divisions

# Draw dividing lines (light gray)
# 这些线代表钢琴的音高分割
for angle in angles[:-1]:
    ax.plot([angle, angle], [1, 2**n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

# 填充特定“黑键”扇区 (0-based index)
# 对应钢琴的黑键位置：#C, #D, #F, #G, #A
# 0-C, 1-#C, 2-D, 3-#D, 4-E, 5-F, 6-#F, 7-G, 8-#G, 9-A, 10-#A, 11-B
# 所以填充扇区对应索引 1, 3, 6, 8, 10
sectors_to_fill = [1, 3, 6, 8, 10]

# 填充指定扇区 (黑色)
for i in sectors_to_fill:
    sector_theta = np.linspace(angles[i], angles[i+1], 100)
    ax.fill_between(sector_theta, 1, 2**n_rotations, color='black', alpha=0.3)

# 配置绘图外观
ax.set_xticks(angles[:-1])
ax.set_xticklabels([]) # 去掉角度刻度标签（度数）
ax.grid(True, which='both', alpha=0.3)
ax.set_title("Spiral Piano Keyboard Representation", pad=20)

# --- 标记 C 键 ---
# 找出 C 键的中心角度 (0 或 2*pi 的位置)
c_angle = 0 # 对应 C 键的径向位置

# 标记 C1, C2, C3, C4, C5
# 从内圈到外圈依次是 C1, C2, C3, C4, C5
# 径向位置 r 对应 2^n，n=0, 1, 2, 3, 4
c_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
for i in range(n_rotations): # 循环 n_rotations 次，因为 C 键在每圈都有
    # 计算 C 键的径向位置 (2^i)
    current_r = 2**i
    # 放置 C 键的标签
    # 调整文本位置，使其更靠近标记点
    ax.text(c_angle, current_r * 1.1, c_labels[i],
            horizontalalignment='center', verticalalignment='bottom',
            color='red', fontsize=12, weight='bold')

plt.tight_layout()
plt.show()