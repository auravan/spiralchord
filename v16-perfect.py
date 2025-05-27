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
        self.decaying_animations = [] # 存储正在衰减的动画对象

        # 音符名称映射
        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display()
        self._connect_events()

    def _init_plot(self):
        # Full spiral for background
        theta_full_base = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        r_full_base = np.exp(self.b * theta_full_base)
        self.ax.plot(theta_full_base, r_full_base, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

        # Create 12 divisions
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
        # 这里的关键是确保 segment_theta 和 segment_r 精确地对应 1/12 圆的螺旋线段
        # 不再使用 self.theta_full 和 self.r_full 的全局索引
        # 而是为每个音符重新生成其精确的 theta 和 r 数据
        for octave_idx in range(self.n_rotations):
            for semitone_idx in range(12):
                # 计算该音符在螺旋线上的总角度范围
                total_start_theta = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                total_end_theta = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                # 为这个特定的音符片段生成更细致的角度点
                num_points_in_segment = 50 # 每个音符片段的点数
                segment_theta = np.linspace(total_start_theta, total_end_theta, num_points_in_segment)
                segment_r = np.exp(self.b * segment_theta) # 原始径向数据

                # 初始绘制透明线，用于后续激活
                # line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0)
                # 重要：为了让contains方法工作，必须确保line_obj是存在的并且可拾取的。
                # 初始alpha=0可能导致无法点击，或者需要一个足够大的pickradius
                # 最好一开始就画出，然后调整alpha
                line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0, picker=5) # picker=5像素容忍度

                note_name = self._get_note_name(octave_idx, semitone_idx)
                self.notes_data[(octave_idx, semitone_idx)] = {
                    'line': line_obj,
                    'highlighted': False,
                    'name': note_name,
                    'base_theta': segment_theta, # 存储这个音符的精确角度数据
                    'base_r': segment_r # 存储这个音符的原始径向数据
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
            # contains 方法是关键，它会考虑线条的粗细和picker属性
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
                return # 找到并处理后即可返回

    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data):
        n_frames = 40 # 动画帧数
        animation_duration = 0.5 # 动画持续时间（秒）
        
        # 衰减的径向比例 (从当前径向值到目标径向值)
        # 例如，从 r 到 r * 0.5。这个因子将作用于原始的 r 值
        # 注意：动画开始时，线条位于 original_r_data 的位置
        # 衰减的终点是 original_r_data * decay_end_factor
        decay_start_factor = 1.0 # 动画开始时，线段的径向值因子（保持原始位置）
        decay_end_factor = 0.5   # 动画结束时，线段的径向值因子（收缩到原径向的 0.5 倍）

        # 计算每帧的径向因子和透明度
        r_factors = np.linspace(decay_start_factor, decay_end_factor, n_frames)
        alpha_steps = np.linspace(1.0, 0.0, n_frames) # 透明度从1到0

        def animate_frame(frame_idx):
            if frame_idx < n_frames:
                current_r_factor = r_factors[frame_idx]
                current_alpha = alpha_steps[frame_idx]

                # 计算当前帧的径向数据：原始径向值 * 当前径向因子
                # 这将使得线段在保持其角度范围的同时，向圆心收缩
                current_r_data = original_r_data * current_r_factor

                # 重新设置线段数据
                line_obj.set_data(original_theta_data, current_r_data) # theta保持不变，r变化
                line_obj.set_alpha(current_alpha)
            else:
                line_obj.set_alpha(0.0) # 动画结束，确保最终不可见
                # 重置高亮状态，如果用户在动画期间没有再次点击
                if note_key in self.notes_data and self.notes_data[note_key]['highlighted']:
                    self.notes_data[note_key]['highlighted'] = False
                    note_name = self.notes_data[note_key]['name']
                    if note_name in self.active_notes_list:
                         self.active_notes_list.remove(note_name)
                    self._update_status_display()
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