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
ax.set_rticks([2**n for n in range(n_rotations + 1)])
ax.set_yticklabels([]) # 移除所有径向刻度标签

# Plot the logarithmic spiral (blue)
ax.plot(theta, r, 'b-', linewidth=2, alpha=0.7)

# Create 12 divisions (每个音程30°，一个八度12个半音)
angles = np.linspace(0, 2 * np.pi, 13)  # 13 points for 12 divisions

# Draw dividing lines (light gray)
for angle in angles[:-1]:
    ax.plot([angle, angle], [1, 2**n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

# --- 恢复之前的“黑键”填充 (浅灰色) ---
# 对应钢琴的黑键位置：#C, #D, #F, #G, #A
# 0-C, 1-#C, 2-D, 3-#D, 4-E, 5-F, 6-#F, 7-G, 8-#G, 9-A, 10-#A, 11-B
# 所以填充扇区对应索引 1, 3, 6, 8, 10
sectors_to_fill_gray = [1, 3, 6, 8, 10]

# 填充指定扇区 (浅灰色)
for i in sectors_to_fill_gray:
    sector_theta = np.linspace(angles[i], angles[i+1], 100)
    # 径向从 1 到 2^n_rotations 填充，覆盖所有八度
    ax.fill_between(sector_theta, 1, 2**n_rotations, color='gray', alpha=0.1) # 颜色更浅，更像背景

# --- 定义 C 大调和弦的音，并计算其对应的扇区 ---
# 和弦音的八度 (C1=0, C2=1, C3=2, C4=3, C5=4) 和半音偏移 (C=0, #C=1, ..., B=11)
cmaj_chord_notes = [
    {'octave': 2, 'semitone_offset': 0},  # C3
    {'octave': 2, 'semitone_offset': 7},  # G3
    {'octave': 3, 'semitone_offset': 0},  # C4
    {'octave': 3, 'semitone_offset': 4},  # E4
    {'octave': 3, 'semitone_offset': 7}   # G4
]

# 填充和弦音的扇区 (深黑色)
for note in cmaj_chord_notes:
    octave = note['octave']
    semitone = note['semitone_offset']

    # 计算该音符在螺旋线上的径向位置 (r)
    # 完整一圈是 2*pi，一个半音是 2*pi/12
    # 每个音符在八度内的角度是 semitone * (2*pi/12)
    # 整体角度是 octave * 2*pi + semitone * (2*pi/12)
    # 对应的径向值 r = exp(b * theta)
    current_theta_start = octave * 2 * np.pi + semitone * (2 * np.pi / 12)
    current_theta_end = octave * 2 * np.pi + (semitone + 1) * (2 * np.pi / 12)

    # 绘制一个弧形的扇区，从螺旋线内部边缘到螺旋线外部边缘
    # 为了可视化效果，我们让这个激活区域的径向宽度稍微固定一点，或者跟随螺旋线的粗细
    # 我们可以沿着螺旋线绘制一个带状区域
    # r_mid = np.exp(b * current_theta_start)
    # r_patch_start = r_mid * (1 - 0.05) # 稍微在螺旋线内侧
    # r_patch_end = r_mid * (1 + 0.05)   # 稍微在螺旋线外侧

    # 更精确地，我们填充从当前八度起始线到螺旋线的区域，或者一个固定的宽度
    # 这里的难点在于 `fill_between` 是在径向绘制，需要我们手动构建多边形
    # 绘制一个沿螺旋线的小扇区
    # 为了沿螺旋线涂黑，我们不再使用 fill_between(theta, r_start, r_end) 这种径向填充方式
    # 而是绘制一个更精确的带状区域

    # 我们可以通过绘制多边形来实现沿螺旋线的精确填充
    # 获取该扇区在螺旋线上的角度范围
    fill_theta = np.linspace(current_theta_start, current_theta_end, 50) # 更细致的角度点
    fill_r_inner = np.exp(b * fill_theta) * 0.95 # 略微靠近中心
    fill_r_outer = np.exp(b * fill_theta) * 1.05 # 略微远离中心

    # 创建多边形的点
    # 沿着内径向线从起点到终点
    points_inner = np.array([fill_theta, fill_r_inner]).T
    # 沿着外径向线从终点到起点（逆序连接形成闭合图形）
    points_outer = np.array([fill_theta, fill_r_outer]).T[::-1]
    points = np.vstack([points_inner, points_outer, points_inner[0]]) # 闭合多边形

    # 将极坐标点转换为笛卡尔坐标点进行填充
    x_coords = points[:, 1] * np.cos(points[:, 0])
    y_coords = points[:, 1] * np.sin(points[:, 0])
    ax.fill(x_coords, y_coords, color='black', alpha=0.8, edgecolor='none')


# 配置绘图外观
ax.set_xticks(angles[:-1])
ax.set_xticklabels([]) # 去掉角度刻度标签（度数）
ax.grid(True, which='both', alpha=0.3)
ax.set_title("Spiral Piano Keyboard: C Major Chord (C3, G3, C4, E4, G4)", pad=20)

# --- 标记 C 键 ---
# 找出 C 键的中心角度 (0 或 2*pi 的位置)
c_angle = 0 # 对应 C 键的径向位置

# 标记 C1, C2, C3, C4, C5
c_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
for i in range(n_rotations): # 循环 n_rotations 次，因为 C 键在每圈都有
    # 计算 C 键的径向位置 (2^i)
    current_r = 2**i
    # 放置 C 键的标签
    ax.text(c_angle, current_r * 1.1, c_labels[i],
            horizontalalignment='center', verticalalignment='bottom',
            color='red', fontsize=12, weight='bold')

plt.tight_layout()
plt.show()