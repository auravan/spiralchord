import numpy as np
import matplotlib.pyplot as plt

# --- Jupyter Notebook 交互式后端配置 ---
# 如果在 Jupyter Notebook 中运行，取消下面一行的注释
# %matplotlib widget

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(10, 10), subplot_kw={'polar': True})

        # 全局存储所有音符的几何信息和对应的 Line2D 对象
        # key: (octave, semitone_offset), value: {'line': Line2D_obj, 'highlighted': bool}
        self.notes_data = {}

        self._init_plot()
        self._draw_notes_segments() # 预先绘制所有音符的“高亮”线条（初始为不活跃）
        self._connect_events()

    def _init_plot(self):
        # Spiral parameters
        theta_full = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        r_full = np.exp(self.b * theta_full)

        # Create logarithmic radial scale
        self.ax.set_rscale('log')
        self.ax.set_rticks([2**n for n in range(self.n_rotations + 1)])
        self.ax.set_yticklabels([]) # 移除所有径向刻度标签

        # Plot the base logarithmic spiral (light blue for context)
        self.ax.plot(theta_full, r_full, 'skyblue', linewidth=2, alpha=0.5)

        # Create 12 divisions (每个音程30°，一个八度12个半音)
        self.angles = np.linspace(0, 2 * np.pi, 13)  # 13 points for 12 divisions

        # Draw dividing lines (light gray)
        for angle in self.angles[:-1]:
            self.ax.plot([angle, angle], [1, 2**self.n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

        # --- 恢复并应用“黑键”填充 (浅灰色) ---
        # 对应钢琴的黑键位置：#C, #D, #F, #G, #A
        sectors_to_fill_gray = [1, 3, 6, 8, 10]
        for i in sectors_to_fill_gray:
            sector_theta = np.linspace(self.angles[i], self.angles[i+1], 100)
            self.ax.fill_between(sector_theta, 1, 2**self.n_rotations, color='gray', alpha=0.05)

        # Configure plot appearance
        self.ax.set_xticks(self.angles[:-1])
        self.ax.set_xticklabels([]) # 去掉角度刻度标签（度数）
        self.ax.grid(True, which='both', alpha=0.3)
        self.ax.set_title("Interactive Spiral Piano Keyboard", pad=20)

        # --- 标记 C 键 ---
        c_angle = 0
        c_labels = ['C1', 'C2', 'C3', 'C4', 'C5']
        for i in range(self.n_rotations):
            current_r = 2**i
            self.ax.text(c_angle, current_r * 1.1, c_labels[i],
                         horizontalalignment='center', verticalalignment='bottom',
                         color='red', fontsize=12, weight='bold')

        plt.tight_layout()

    def _draw_notes_segments(self):
        # 预先绘制所有可能的音符线段，并将其初始设置为不可见或低透明度
        # 我们可以模拟 5 个八度 (C1到C5) x 12 个半音
        for octave_idx in range(self.n_rotations): # 0到4对应C1到C5
            for semitone_idx in range(12): # 0到11
                start_angle_for_note = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                end_angle_for_note = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                # 找到这个角度范围内的 theta 值
                theta_segment_indices = np.where((theta_full >= start_angle_for_note) & (theta_full <= end_angle_for_note))

                if len(theta_segment_indices[0]) > 0:
                    segment_theta = theta_full[theta_segment_indices]
                    segment_r = r_full[theta_segment_indices]
                    # 初始绘制为完全透明的线，方便后面修改
                    line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0) # 初始不可见
                    self.notes_data[(octave_idx, semitone_idx)] = {'line': line_obj, 'highlighted': False}

    def _connect_events(self):
        # 连接鼠标点击事件
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _on_click(self, event):
        if event.inaxes != self.ax: # 确保点击发生在我们的极坐标图上
            return

        if event.button == 1: # 左键点击
            # 获取点击的极坐标
            clicked_theta = event.xdata % (2 * np.pi) # 将角度归一化到 0-2*pi
            clicked_r = event.ydata

            # 确定点击的八度
            # r = e^(b*theta) => theta = log(r)/b
            # 每个八度的 r_start 是 2^octave_idx
            # 判断 clicked_r 落在哪个八度范围内
            octave_idx = int(np.log2(clicked_r))

            # 确定点击的半音 (角度)
            # 找到 clicked_theta 落在哪个角度扇区内
            semitone_idx = None
            for i in range(12):
                if self.angles[i] <= clicked_theta < self.angles[i+1]:
                    semitone_idx = i
                    break
            # 如果点击在 0-2*pi 边界处，特殊处理，例如 2*pi 落在最后一个扇区
            if semitone_idx is None and np.isclose(clicked_theta, self.angles[12]):
                 semitone_idx = 11 # 最后一个半音

            if octave_idx is not None and semitone_idx is not None:
                note_key = (octave_idx, semitone_idx)
                if note_key in self.notes_data:
                    current_state = self.notes_data[note_key]['highlighted']
                    self.notes_data[note_key]['highlighted'] = not current_state # 切换状态
                    self.notes_data[note_key]['line'].set_alpha(1.0 if not current_state else 0.0) # 切换可见性
                    self.fig.canvas.draw_idle() # 请求重绘

    def show(self):
        plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    # 需要先定义 theta_full 和 r_full，因为 _draw_notes_segments 引用了它们
    n_rotations_global = 5
    b_global = np.log(2) / (2 * np.pi)
    theta_full = np.linspace(0, 2 * np.pi * n_rotations_global, 1000)
    r_full = np.exp(b_global * theta_full)

    piano = InteractiveSpiralPiano(n_rotations=n_rotations_global)
    piano.show()