import numpy as np
import matplotlib.pyplot as plt

# --- Jupyter Notebook 交互式后端配置 ---
# 如果在 Jupyter Notebook 中运行，取消下面一行的注释
# %matplotlib widget

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(12, 10), subplot_kw={'polar': True}) # 增加图的大小以便容纳文本

        # 全局存储所有音符的几何信息和对应的 Line2D 对象
        self.notes_data = {}
        # 存储当前被高亮的音符名称列表
        self.active_notes_list = []

        # 生成完整的螺旋线数据，供所有音符线段使用
        self.theta_full = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        self.r_full = np.exp(self.b * self.theta_full)

        # 音符名称映射 (C=0, #C=1, D=2, ..., B=11)
        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display() # 新增：添加状态显示组件
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
        # C1 对应八度索引 0
        c_labels_map = {0: 'C1', 1: 'C2', 2: 'C3', 3: 'C4', 4: 'C5'}
        for i in range(self.n_rotations):
            current_r = 2**i
            label = c_labels_map.get(i, f'C{i+1}') # 从映射中获取标签
            self.ax.text(c_angle, current_r * 1.1, label,
                         horizontalalignment='center', verticalalignment='bottom',
                         color='red', fontsize=12, weight='bold')

        plt.tight_layout()

    def _get_note_name(self, octave_idx, semitone_idx):
        """根据八度索引和半音索引获取音符名称"""
        # NEMU的C1对应octave_idx=0，这里也用C1对应octave_idx=0
        octave_number = octave_idx + 1
        return f"{self.semitone_names[semitone_idx]}{octave_number}"

    def _draw_notes_segments(self):
        # 预先绘制所有可能的音符线段
        for octave_idx in range(self.n_rotations): # 0到n_rotations-1
            for semitone_idx in range(12): # 0到11
                start_angle_for_note = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                end_angle_for_note = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                segment_indices = np.where((self.theta_full >= start_angle_for_note) & (self.theta_full <= end_angle_for_note))

                if len(segment_indices[0]) > 0:
                    segment_theta = self.theta_full[segment_indices]
                    segment_r = self.r_full[segment_indices]
                    line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0)
                    note_name = self._get_note_name(octave_idx, semitone_idx)
                    self.notes_data[(octave_idx, semitone_idx)] = {
                        'line': line_obj,
                        'highlighted': False,
                        'name': note_name # 存储音符名称
                    }

    def _add_status_display(self):
        """添加一个文本框来显示当前激活的音符"""
        # 在图的左上角添加文本框，注意这里的坐标是轴坐标（0-1）
        # bbox 可以让文本有一个背景框
        self.status_text = self.fig.text(0.02, 0.95,
                                          "Active Notes: None",
                                          fontsize=12,
                                          verticalalignment='top',
                                          horizontalalignment='left',
                                          bbox=dict(boxstyle='round,pad=0.5', fc='wheat', ec='k', lw=1, alpha=0.8))
        self._update_status_display() # 初始显示

    def _update_status_display(self):
        """更新文本框显示的内容"""
        if not self.active_notes_list:
            display_text = "Active Notes: None"
        else:
            # 排序以便显示更清晰
            sorted_notes = sorted(self.active_notes_list, key=lambda x: (x[-1], self.semitone_names.index(x[:-1].rstrip('#'))))
            display_text = "Active Notes: " + ", ".join(sorted_notes)
        self.status_text.set_text(display_text)
        self.fig.canvas.draw_idle()

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return

        for note_key, data in self.notes_data.items():
            line_obj = data['line']
            contains, _ = line_obj.contains(event)
            if contains:
                current_state = data['highlighted']
                data['highlighted'] = not current_state

                # 切换线段的可见性
                data['line'].set_alpha(1.0 if not current_state else 0.0)

                # 更新激活音符列表
                note_name = data['name']
                if data['highlighted']:
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)
                else:
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)

                self._update_status_display() # 更新显示
                self.fig.canvas.draw_idle()
                return # 找到并处理后即可返回

    def show(self):
        plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    piano = InteractiveSpiralPiano(n_rotations=5)
    piano.show()