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
        # key: (octave, semitone_offset), value: {'line': Line2D_obj, 'highlighted': bool, 'base_alpha': float}
        self.notes_data = {}

        # 生成完整的螺旋线数据，供所有音符线段使用
        self.theta_full = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        self.r_full = np.exp(self.b * self.theta_full)

        self._init_plot()
        self._draw_notes_segments() # 预先绘制所有音符的“高亮”线条
        self._connect_events()

    def _init_plot(self):
        # Plot the base logarithmic spiral (light blue for context)
        self.ax.plot(self.theta_full, self.r_full, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

        # Create 12 divisions (每个音程30°，一个八度12个半音)
        self.angles = np.linspace(0, 2 * np.pi, 13)  # 13 points for 12 divisions

        # Draw dividing lines (light gray)
        for angle in self.angles[:-1]:
            self.ax.plot([angle, angle], [1, 2**self.n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

        # --- 恢复并应用“黑键”填充 (浅灰色) ---
        sectors_to_fill_gray = [1, 3, 6, 8, 10]
        for i in sectors_to_fill_gray:
            sector_theta = np.linspace(self.angles[i], self.angles[i+1], 100)
            self.ax.fill_between(sector_theta, 1, 2**self.n_rotations, color='gray', alpha=0.05)

        # Configure plot appearance
        self.ax.set_rscale('log')
        self.ax.set_rticks([2**n for n in range(self.n_rotations + 1)])
        self.ax.set_yticklabels([])
        self.ax.set_xticks(self.angles[:-1])
        self.ax.set_xticklabels([])
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
        # 预先绘制所有可能的音符线段
        for octave_idx in range(self.n_rotations): # 0到n_rotations-1
            for semitone_idx in range(12): # 0到11
                start_angle_for_note = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                end_angle_for_note = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                # 找到这个角度范围内的 theta 值
                segment_indices = np.where((self.theta_full >= start_angle_for_note) & (self.theta_full <= end_angle_for_note))

                if len(segment_indices[0]) > 0:
                    segment_theta = self.theta_full[segment_indices]
                    segment_r = self.r_full[segment_indices]
                    # 初始绘制为透明线，等待被点击激活
                    line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0) # 初始不可见
                    # 存储 Line2D 对象和其状态
                    self.notes_data[(octave_idx, semitone_idx)] = {'line': line_obj, 'highlighted': False}

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return

        # 遍历所有预先绘制的音符线段，检查哪个被点击
        for note_key, data in self.notes_data.items():
            line_obj = data['line']
            # 使用 contains 方法来检测点击是否落在该 Line2D 对象上
            # 容忍度参数 pickradius 可以调整点击检测的灵敏度
            # 这里设置了一个相对较大的 pickradius，让点击更容易命中
            contains, _ = line_obj.contains(event)
            if contains:
                current_state = data['highlighted']
                data['highlighted'] = not current_state # 切换状态
                data['line'].set_alpha(1.0 if not current_state else 0.0) # 切换可见性
                self.fig.canvas.draw_idle() # 请求重绘
                return # 找到一个就处理，避免重复操作

    def show(self):
        plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    piano = InteractiveSpiralPiano(n_rotations=5)
    piano.show()