import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import collections # 用于 deque

# --- Jupyter Notebook 交互式后端配置 ---
# 如果在 Jupyter Notebook 中运行，取消下面一行的注释
# %matplotlib widget

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(12, 10), subplot_kw={'polar': True})

        self.notes_data = {} # 存储所有音符线段及其状态
        self.active_notes_list = [] # 存储当前激活的音符名称
        self.decaying_animations = [] # 存储正在衰减的动画对象，以便管理

        # 生成完整的螺旋线数据，供所有音符线段使用
        self.theta_full = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        self.r_full = np.exp(self.b * self.theta_full)

        # 音符名称映射
        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display()
        self._connect_events()

    def _init_plot(self):
        # Plot the base logarithmic spiral (light blue for context)
        self.ax.plot(self.theta_full, self.r_full, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

        # Create 12 divisions
        self.angles = np.linspace(0, 2 * np.pi, 13)

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
        self.ax.set_title("Interactive Spiral Piano Keyboard with Decay Effect", pad=20)

        # --- 标记 C 键 ---
        c_angle = 0
        c_labels_map = {0: 'C1', 1: 'C2', 2: 'C3', 3: 'C4', 4: 'C5'}
        for i in range(self.n_rotations):
            current_r = 2**i
            label = c_labels_map.get(i, f'C{i+1}')
            self.ax.text(c_angle, current_r * 1.1, label,
                         horizontalalignment='center', verticalalignment='bottom',
                         color='red', fontsize=12, weight='bold')

        plt.tight_layout()

    def _get_note_name(self, octave_idx, semitone_idx):
        octave_number = octave_idx + 1
        return f"{self.semitone_names[semitone_idx]}{octave_number}"

    def _draw_notes_segments(self):
        # 预先绘制所有可能的音符线段
        for octave_idx in range(self.n_rotations):
            for semitone_idx in range(12):
                start_angle_for_note = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                end_angle_for_note = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                segment_indices = np.where((self.theta_full >= start_angle_for_note) & (self.theta_full <= end_angle_for_note))

                if len(segment_indices[0]) > 0:
                    segment_theta = self.theta_full[segment_indices]
                    segment_r = self.r_full[segment_indices]

                    # 在极坐标轴上绘制时，传入 theta, r
                    line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0) # 初始不可见

                    note_name = self._get_note_name(octave_idx, semitone_idx)
                    self.notes_data[(octave_idx, semitone_idx)] = {
                        'line': line_obj,
                        'highlighted': False,
                        'name': note_name,
                        'base_theta': segment_theta, # 存储原始角度数据
                        'base_r': segment_r # 存储原始径向数据
                    }

    def _add_status_display(self):
        self.status_text = self.fig.text(0.02, 0.95,
                                          "Active Notes: None",
                                          fontsize=12,
                                          verticalalignment='top',
                                          horizontalalignment='left',
                                          bbox=dict(boxstyle='round,pad=0.5', fc='wheat', ec='k', lw=1, alpha=0.8))
        self._update_status_display()

    def _update_status_display(self):
        if not self.active_notes_list:
            display_text = "Active Notes: None"
        else:
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
                if not current_state:
                    data['highlighted'] = True
                    # 在启动动画前，确保线段数据回到原始状态，并设置为可见
                    line_obj.set_data(data['base_theta'], data['base_r']) # 使用 set_data
                    line_obj.set_alpha(1.0)

                    # 启动衰减动画
                    self._start_decay_animation(note_key, data['line'], data['base_theta'], data['base_r'])

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)
                    self._update_status_display()
                else:
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0)
                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)
                    self._update_status_display()

                self.fig.canvas.draw_idle()
                return

    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data):
        n_frames = 60
        animation_duration = 1.0
        decay_factor = 0.5 # 径向衰减到原始值的 0.5 倍

        # 计算径向和透明度的每帧变化
        r_steps = np.linspace(original_r_data, original_r_data * decay_factor, n_frames)
        alpha_steps = np.linspace(1.0, 0.0, n_frames)

        # 定义动画更新函数
        def animate_frame(frame_idx):
            if frame_idx < n_frames:
                # 获取当前帧的径向数据
                current_r = r_steps[frame_idx]
                current_alpha = alpha_steps[frame_idx]

                # 重新计算笛卡尔坐标 (x, y)
                x_data = current_r * np.cos(original_theta_data)
                y_data = current_r * np.sin(original_theta_data)

                # 使用 set_data 更新线段
                line_obj.set_data(x_data, y_data)
                line_obj.set_alpha(current_alpha)
            else:
                # 动画结束，确保线段最终不可见，并重置其状态
                line_obj.set_alpha(0.0)
                # 理论上，当动画完成时，该音符不应再被视为“高亮”
                # 这里的 note_key 在动画结束时可能已经不是 'highlighted' 状态了
                # 确保只在它确实是“高亮”时才将其重置为非高亮，避免与点击行为冲突
                if note_key in self.notes_data and self.notes_data[note_key]['highlighted']:
                    self.notes_data[note_key]['highlighted'] = False
                    # 动画结束后，如果该音符名称仍在列表中，也应移除
                    note_name = self.notes_data[note_key]['name']
                    if note_name in self.active_notes_list:
                         self.active_notes_list.remove(note_name)
                    self._update_status_display() # 动画结束后更新状态显示
            return line_obj, # FuncAnimation 需要返回可绘制对象列表

        anim = animation.FuncAnimation(self.fig, animate_frame, frames=n_frames + 1,
                                       interval=(animation_duration / n_frames) * 1000,
                                       blit=True, repeat=False)
        self.decaying_animations.append(anim)

    def show(self):
        plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    piano = InteractiveSpiralPiano(n_rotations=5)
    piano.show()