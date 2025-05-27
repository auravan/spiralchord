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

        self.notes_data = {} # 存储所有音符线段及其状态
        self.active_notes_list = [] # 存储当前激活的音符名称
        # 存储正在衰减的动画对象，用字典映射 note_key -> anim_object
        # 这样可以方便地查找和取消特定音符的动画
        self.current_decay_animations = {}

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
        for octave_idx in range(self.n_rotations):
            for semitone_idx in range(12):
                total_start_theta = octave_idx * 2 * np.pi + semitone_idx * (2 * np.pi / 12)
                total_end_theta = octave_idx * 2 * np.pi + (semitone_idx + 1) * (2 * np.pi / 12)

                num_points_in_segment = 50
                segment_theta = np.linspace(total_start_theta, total_end_theta, num_points_in_segment)
                segment_r = np.exp(self.b * segment_theta)

                line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0, picker=5)

                note_name = self._get_note_name(octave_idx, semitone_idx)
                self.notes_data[(octave_idx, semitone_idx)] = {
                    'line': line_obj,
                    'highlighted': False,
                    'name': note_name,
                    'base_theta': segment_theta,
                    'base_r': segment_r
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
                # 停止并清理当前音符可能正在进行的衰减动画
                if note_key in self.current_decay_animations:
                    self.current_decay_animations[note_key].event_source.stop() # 停止动画
                    del self.current_decay_animations[note_key] # 从字典中移除
                    # 确保线段回到完全透明状态（动画被中断，但没播放完）
                    line_obj.set_alpha(0.0)

                # 重置该音符的高亮状态为 False
                # 这样不论是主动取消还是重新触发，都能从一个干净的状态开始
                data['highlighted'] = False
                
                # 重新开始高亮和动画
                data['highlighted'] = True
                line_obj.set_data(data['base_theta'], data['base_r'])
                line_obj.set_alpha(1.0) # 立即变黑

                self._start_decay_animation(note_key, data['line'], data['base_theta'], data['base_r'])

                note_name = data['name']
                if note_name not in self.active_notes_list:
                    self.active_notes_list.append(note_name)
                self._update_status_display()
                
                self.fig.canvas.draw_idle()
                return # 找到并处理后即可返回

    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data):
        n_frames = 40
        animation_duration = 0.5
        
        decay_start_factor = 1.0
        decay_end_factor = 0.5

        r_factors = np.linspace(decay_start_factor, decay_end_factor, n_frames)
        alpha_steps = np.linspace(1.0, 0.0, n_frames)

        def animate_frame(frame_idx):
            if frame_idx < n_frames:
                current_r_factor = r_factors[frame_idx]
                current_alpha = alpha_steps[frame_idx]

                current_r_data = original_r_data * current_r_factor

                line_obj.set_data(original_theta_data, current_r_data)
                line_obj.set_alpha(current_alpha)
            else:
                # 动画自然结束
                line_obj.set_alpha(0.0) # 确保最终不可见

                # 清理动画实例
                if note_key in self.current_decay_animations:
                    # 不再需要调用 .stop() 因为动画已完成，但仍需从字典中移除引用
                    del self.current_decay_animations[note_key] 
                
                # 重置音符高亮状态，并更新显示
                if note_key in self.notes_data: # 确保音符数据仍然存在
                    self.notes_data[note_key]['highlighted'] = False
                    note_name = self.notes_data[note_key]['name']
                    if note_name in self.active_notes_list:
                         self.active_notes_list.remove(note_name)
                    self._update_status_display()
            return line_obj,

        # 为每个音符创建一个新的动画，并将其存储在字典中
        anim = animation.FuncAnimation(self.fig, animate_frame, frames=n_frames + 1,
                                       interval=(animation_duration / n_frames) * 1000,
                                       blit=True, repeat=False)
        self.current_decay_animations[note_key] = anim # 将动画实例与音符键关联

    def show(self):
        plt.show()

# --- 主程序入口 ---
if __name__ == "__main__":
    piano = InteractiveSpiralPiano(n_rotations=5)
    piano.show()