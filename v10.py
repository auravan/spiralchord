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

# Plot the base logarithmic spiral (light blue for context)
# 我们先画一个更浅的蓝色作为背景，这样被激活的黑色会更明显
ax.plot(theta, r, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

# Create 12 divisions (每个音程30°，一个八度12个半音)
angles = np.linspace(0, 2 * np.pi, 13)  # 13 points for 12 divisions

# Draw dividing lines (light gray)
for angle in angles[:-1]:
    ax.plot([angle, angle], [1, 2**n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

# --- 恢复并应用“黑键”填充 (浅灰色) ---
# 对应钢琴的黑键位置：#C, #D, #F, #G, #A
# 0-C, 1-#C, 2-D, 3-#D, 4-E, 5-F, 6-#F, 7-G, 8-#G, 9-A, 10-#A, 11-B
# 所以填充扇区对应索引 1, 3, 6, 8, 10
sectors_to_fill_gray = [1, 3, 6, 8, 10]

# 填充指定扇区 (浅灰色)
for i in sectors_to_fill_gray:
    sector_theta = np.linspace(angles[i], angles[i+1], 100)
    # 径向从 1 到 2^n_rotations 填充，覆盖所有八度
    ax.fill_between(sector_theta, 1, 2**n_rotations, color='gray', alpha=0.05) # 颜色更浅，更像背景

# --- 定义 C 大调和弦的音，并计算其对应的螺旋线段 ---
# 和弦音的八度 (C1=0, C2=1, C3=2, C4=3, C5=4) 和半音偏移 (C=0, #C=1, ..., B=11)
cmaj_chord_notes = [
    {'octave': 2, 'semitone_offset': 0},  # C3
    {'octave': 2, 'semitone_offset': 7},  # G3
    {'octave': 3, 'semitone_offset': 0},  # C4
    {'octave': 3, 'semitone_offset': 4},  # E4
    {'octave': 3, 'semitone_offset': 7}   # G4
]

# 在和弦音对应的螺旋线段上进行覆盖 (深黑色，更粗的线)
for note in cmaj_chord_notes:
    octave = note['octave']
    semitone = note['semitone_offset']

    # 计算该音符在螺旋线上的角度范围
    # 完整一圈是 2*pi，一个半音是 2*pi/12
    # 整体起始角度 = 八度数 * 2*pi + 半音偏移 * (2*pi/12)
    start_angle_for_note = octave * 2 * np.pi + semitone * (2 * np.pi / 12)
    end_angle_for_note = octave * 2 * np.pi + (semitone + 1) * (2 * np.pi / 12)

    # 找到这个角度范围内的 theta 值
    # filter the theta values that fall within the note's angle range
    # 确保 theta 值在这个音符的有效范围内
    note_segment_indices = np.where((theta >= start_angle_for_note) & (theta <= end_angle_for_note))

    # 如果找到了对应的线段，则在其上绘制黑线
    if len(note_segment_indices[0]) > 0:
        segment_theta = theta[note_segment_indices]
        segment_r = r[note_segment_indices]
        ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=1.0) # 更粗的黑色线

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