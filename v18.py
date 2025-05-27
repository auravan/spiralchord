import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse # For command-line arguments

# --- Jupyter Notebook Interactive Backend Configuration ---
# If running in Jupyter Notebook, uncomment the line below
# %matplotlib widget

class InteractiveSpiralPiano:
    def __init__(self, n_rotations=5, enable_animation=True):
        self.n_rotations = n_rotations
        self.b = np.log(2) / (2 * np.pi)
        self.fig, self.ax = plt.subplots(figsize=(12, 10), subplot_kw={'polar': True})

        self.enable_animation = enable_animation # New configuration setting
        self.notes_data = {}
        self.active_notes_list = []
        self.current_decay_animations = {} # Stores active animation objects

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
        self.ax.set_title("Interactive Spiral Piano Keyboard", pad=20)
        if self.enable_animation:
            self.ax.set_title("Interactive Spiral Piano Keyboard (Animation ON)", pad=20)
        else:
            self.ax.set_title("Interactive Spiral Piano Keyboard (Animation OFF)", pad=20)


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

        # Add a key press event for batch decay (e.g., press 'Spacebar')
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

    def _on_key_press(self, event):
        if event.key == ' ': # Spacebar
            if not self.enable_animation: # Only trigger if animation is off
                self._trigger_batch_decay()

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
                    line_obj.set_alpha(0.0) # Ensure it goes invisible if an animation was interrupted

                # Toggle the highlighted state
                if not data['highlighted']: # If currently not highlighted (or animation just stopped)
                    data['highlighted'] = True
                    line_obj.set_data(data['base_theta'], data['base_r'])
                    line_obj.set_alpha(1.0) # Make it fully visible

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)

                    if self.enable_animation:
                        self._start_decay_animation(note_key, data['line'], data['base_theta'], data['base_r'])
                    
                else: # If it's already highlighted (only possible when animation is OFF)
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0) # Make it disappear immediately

                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)

                self._update_status_display()
                self.fig.canvas.draw_idle()
                return

    def _start_decay_animation(self, note_key, line_obj, original_theta_data, original_r_data):
        # We only start animation if animation is explicitly enabled
        if not self.enable_animation:
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
                # Animation naturally ended
                line_obj.set_alpha(0.0)

                # Clean up animation object reference
                if note_key in self.current_decay_animations:
                    del self.current_decay_animations[note_key] 
                
                # Update note state and display, if it was indeed highlighted
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
        self.current_decay_animations[note_key] = anim

    def _trigger_batch_decay(self):
        """Triggers decay animation for all currently active notes."""
        if self.enable_animation: # This method is typically used when animation is off
            return

        notes_to_decay = list(self.active_notes_list) # Create a copy to iterate
        
        # Clear the active notes list immediately, as they are about to decay
        self.active_notes_list.clear()
        self._update_status_display()

        for note_name_to_decay in notes_to_decay:
            # Find the corresponding note_key for the note_name
            note_key_found = None
            for key, data in self.notes_data.items():
                if data['name'] == note_name_to_decay:
                    note_key_found = key
                    break
            
            if note_key_found and self.notes_data[note_key_found]['highlighted']:
                # Set note to 'highlighted' so animation will run correctly
                self.notes_data[note_key_found]['highlighted'] = True 
                line_obj = self.notes_data[note_key_found]['line']
                base_theta = self.notes_data[note_key_found]['base_theta']
                base_r = self.notes_data[note_key_found]['base_r']

                # Ensure it's visible before starting the animation
                line_obj.set_data(base_theta, base_r)
                line_obj.set_alpha(1.0)

                # Start the decay animation for this note
                # Temporarily enable animation for this batch decay, then restore
                # A more robust way might be to pass a flag to _start_decay_animation
                # for batch mode. For now, we'll let it use its own logic.
                self.enable_animation = True # Temporarily enable animation for this run
                self._start_decay_animation(note_key_found, line_obj, base_theta, base_r)
                self.enable_animation = False # Revert after starting
        
        self.fig.canvas.draw_idle()


    def show(self):
        plt.show()

# --- Main Program Entry ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interactive Spiral Piano Keyboard.")
    parser.add_argument(
        "--enable-animation",
        action="store_true", # This flag will be True if present, False otherwise
        help="Enable note decay animation. If false, notes remain highlighted until batch decay (spacebar)."
    )
    args = parser.parse_args()

    # Pass the parsed argument to the piano constructor
    piano = InteractiveSpiralPiano(n_rotations=5, enable_animation=args.enable_animation)
    piano.show()