import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse

# --- Jupyter Notebook Interactive Backend Configuration ---
# %matplotlib widget # Uncomment if using Jupyter

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5, enable_animation=True):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(12, 10), subplot_kw={'polar': True})

        self.enable_animation = enable_animation
        self.notes_data = {}
        self.active_notes_list = []
        self.current_decay_animations = {}

        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display()
        self._connect_events()

    def _init_plot(self):
        theta_full_base = np.linspace(0, 2 * np.pi * self.n_rotations, 1000)
        r_full_base = np.exp(self.b * theta_full_base)
        self.ax.plot(theta_full_base, r_full_base, 'skyblue', linewidth=2, alpha=0.5, label='_nolegend_')

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
        self._update_title()

        c_angle = 0
        c_labels_map = {0: 'C1', 1: 'C2', 2: 'C3', 3: 'C4', 4: 'C5'}
        for i in range(self.n_rotations):
            current_r = 2**i
            label = c_labels_map.get(i, f'C{i+1}')
            self.ax.text(c_angle, current_r * 1.1, label,
                         horizontalalignment='center', verticalalignment='bottom',
                         color='red', fontsize=12, weight='bold')

        plt.tight_layout()

    def _update_title(self):
        if self.enable_animation:
            self.ax.set_title("Interactive Spiral Piano Keyboard (Animation ON)", pad=20)
        else:
            self.ax.set_title("Interactive Spiral Piano Keyboard (Animation OFF)", pad=20)
        self.fig.canvas.draw_idle()

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
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

    def _on_key_press(self, event):
        if event.key == ' ': # Spacebar for batch decay when animation is OFF
            if not self.enable_animation:
                self._trigger_batch_decay()
        elif event.key == 'a': # Toggle animation with 'a' key
            self.enable_animation = not self.enable_animation
            self._update_title()
            print(f"Animation is now {'ON' if self.enable_animation else 'OFF'}")
            
            # If animation is just turned ON, trigger batch decay for currently active notes
            if self.enable_animation and self.active_notes_list:
                print("Animation enabled. Triggering batch decay for currently active notes.")
                # Pass force_animation=True to ensure animations run even if enable_animation was false before
                self._trigger_batch_decay(force_animation=True)

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return

        for note_key, data in self.notes_data.items():
            line_obj = data['line']
            contains, _ = line_obj.contains(event)
            if contains:
                # Stop and clear any existing animation for this note
                if note_key in self.current_decay_animations:
                    self.current_decay_animations[note_key].event_source.stop()
                    del self.current_decay_animations[note_key]
                    line_obj.set_alpha(0.0)

                if not data['highlighted']:
                    data['highlighted'] = True
                    line_obj.set_data(data['base_theta'], data['base_r'])
                    line_obj.set_alpha(1.0)

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)

                    if self.enable_animation: # Only start individual animation if enable_animation is True
                        self._start_decay_animation(note_key, data['line'], data['base_theta'], data['base_r'])
                    
                else: # Only callable when animation is OFF
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0)

                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)

                self._update_status_display()
                self.fig.canvas.draw_idle()
                return

    # Modified _start_decay_animation to accept a 'force_start' flag
    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data, force_start=False):
        # Animation will run if self.enable_animation is True OR if force_start is True
        if not self.enable_animation and not force_start:
            return

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
                line_obj.set_alpha(0.0)

                if note_key in self.current_decay_animations:
                    del self.current_decay_animations[note_key] 
                
                if note_key in self.notes_data:
                    if self.notes_data[note_key]['highlighted']:
                        self.notes_data[note_key]['highlighted'] = False
                        # Only remove from active_notes_list if it was part of individual clicks
                        # For batch decay, active_notes_list is cleared upfront
                        # This check prevents errors if the list is already clear
                        note_name = self.notes_data[note_key]['name']
                        if note_name in self.active_notes_list:
                            self.active_notes_list.remove(note_name)
                        self._update_status_display()
            return line_obj,

        anim = animation.FuncAnimation(self.fig, animate_frame, frames=n_frames + 1,
                                       interval=(animation_duration / n_frames) * 1000,
                                       blit=True, repeat=False)
        self.current_decay_animations[note_key] = anim

    # Modified _trigger_batch_decay to pass force_start to _start_decay_animation
    def _trigger_batch_decay(self, force_animation=False):
        if not self.enable_animation and not force_animation:
            return

        # It's crucial to clear the list *before* starting animations for them
        # as the animation completion will try to remove from a (now cleared) list.
        # So we get the list of names first, then clear.
        notes_to_decay_names = list(self.active_notes_list)
        self.active_notes_list.clear() # Clear the list visually and logically
        self._update_status_display() # Update status display immediately

        for note_name_to_decay in notes_to_decay_names:
            note_key_found = None
            for key, data in self.notes_data.items():
                if data['name'] == note_name_to_decay:
                    note_key_found = key
                    break
            
            if note_key_found:
                line_obj = self.notes_data[note_key_found]['line']
                base_theta = self.notes_data[note_key_found]['base_theta']
                base_r = self.notes_data[note_key_found]['base_r']

                # Crucial: Ensure the line is set to its initial state before animating
                line_obj.set_data(base_theta, base_r)
                line_obj.set_alpha(1.0) # Make it fully visible to start the decay from

                # Pass force_start=True to _start_decay_animation
                self._start_decay_animation(note_key_found, line_obj, base_theta, base_r, force_start=True)

        self.fig.canvas.draw_idle()


    def show(self):
        plt.show()

# --- Main Program Entry ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive Spiral Piano Keyboard.")
    parser.add_argument(
        "--enable-animation",
        action="store_true",
        help="Enable note decay animation on click. If omitted, notes remain highlighted until batch decay (Spacebar)."
    )
    args = parser.parse_args()

    piano = InteractiveSpiralPiano(n_rotations=5, enable_animation=args.enable_animation)
    piano.show()