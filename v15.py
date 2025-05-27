import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import collections

# --- Jupyter Notebook 交互式后端配置 ---
# 如果在 Jupyter Notebook 中运行，取消下面一行的注释
# %matplotlib widget

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(12, 10), subplot_kw={'polar': True})

        self.notes_data = {}
        self.active_notes_list = []
        self.decaying_animations = []

        # 生成完整的螺旋线数据，供所有音符线段使用
        self.theta_full = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        self.r_full = np.exp(self.b * self.theta_full)

        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display()
        self._connect_events()

    def _init_plot(self):
        self.ax.plot(self.theta_full, self.r_full, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

        self.angles = np.linspace(0, 2 * np.pi, 13)

        for angle in self.angles[:-1]:
            self.ax.plot([angle, angle], [1, 2**self.n_rotations], color='lightgray', linestyle='-', linewidth=0.5)

        sectors_to_fill_gray = [1, 3, 6, 8, 10]
        for i in sectors_to_fill_gray:
            sector_theta = np.linspace(self.angles[i], self.angles[i+1], 100)
            self.ax.fill_between(sector_theta, 1, 2**self.n_rotations, color='gray', alpha=0.05)

        self.ax.set_rscale('log')
        self.ax.set_rticks([2**n for n in range(self.n_rotations + 1)])
        self.ax.set_yticklabels([])
        self.ax.set_xticks(self.angles[:-1])
        self.ax.set_xticklabels([])
        self.ax.grid(True, which='both', alpha=0.3)
        self.ax.set_title("Interactive Spiral Piano Keyboard with Radial Decay Effect", pad=20)

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
                # 计算该音符对应的在完整螺旋线上的角度范围
                start_angle_for_note = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                end_angle_for_note = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                # 找到该角度范围内的 theta 索引
                segment_indices = np.where((self.theta_full >= start_angle_for_note) & (self.theta_full <= end_angle_for_note))

                if len(segment_indices[0]) > 0:
                    segment_theta = self.theta_full[segment_indices]
                    segment_r = self.r_full[segment_indices] # 原始径向数据

                    # 初始绘制透明线，用于后续激活
                    line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0)

                    note_name = self._get_note_name(octave_idx, semitone_idx)
                    self.notes_data[(octave_idx, semitone_idx)] = {
                        'line': line_obj,
                        'highlighted': False,
                        'name': note_name,
                        'base_theta': segment_theta,
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
                if not current_state: # 只有当音符当前未被高亮时才触发动画
                    data['highlighted'] = True
                    # 确保线段数据回到原始状态，并设置为可见
                    line_obj.set_data(data['base_theta'], data['base_r'])
                    line_obj.set_alpha(1.0) # 立即变黑

                    # 启动衰减动画
                    self._start_decay_animation(note_key, data['line'], data['base_theta'], data['base_r'])

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)
                    self._update_status_display()
                else: # 如果点击已经高亮的音符，就取消高亮，不触发动画
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0) # 立即消失
                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)
                    self._update_status_display()

                self.fig.canvas.draw_idle()
                return

    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data):
        n_frames = 40 # 减少帧数，加快衰减速度
        animation_duration = 0.5 # 缩短动画持续时间
        
        # 衰减的径向比例 (从当前径向值到目标径向值)
        # 例如，从 r 到 r * 0.5
        decay_start_r_factor = 1.0 # 动画开始时，线段的径向值因子
        decay_end_r_factor = 0.5   # 动画结束时，线段的径向值因子

        # 计算每帧的径向因子和透明度
        r_factors = np.linspace(decay_start_r_factor, decay_end_r_factor, n_frames)
        alpha_steps = np.linspace(1.0, 0.0, n_frames) # 透明度从1到0

        # 缓存原始的径向数据，避免在animate_frame中重复访问data['base_r']
        _original_r_data = original_r_data 

        def animate_frame(frame_idx):
            if frame_idx < n_frames:
                current_r_factor = r_factors[frame_idx]
                current_alpha = alpha_steps[frame_idx]

                # 计算当前帧的径向数据：原始径向值 * 当前径向因子
                # 这会使得线段整体向圆心收缩
                current_r_data = _original_r_data * current_r_factor

                # 重新计算笛卡尔坐标 (x, y)
                x_data = current_r_data * np.cos(original_theta_data)
                y_data = current_r_data * np.sin(original_theta_data)

                line_obj.set_data(x_data, y_data)
                line_obj.set_alpha(current_alpha)
            else:
                line_obj.set_alpha(0.0)
                if note_key in self.notes_data and self.notes_data[note_key]['highlighted']:
                    self.notes_data[note_key]['highlighted'] = False
                    note_name = self.notes_data[note_key]['name']
                    if note_name in self.active_notes_list:
                         self.active_notes_list.remove(note_name)
                    self._update_status_display()
            return line_obj,

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