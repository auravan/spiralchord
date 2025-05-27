import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import argparse
import time

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

        self.active_decay_animations = []
        self.master_animation = None

        self.semitone_names = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ]

        self._init_plot()
        self._draw_notes_segments()
        self._add_status_display()
        self._connect_events()
        
        # --- Manual Blitting Setup ---
        self.background = None # Store the background for blitting
        self.fig.canvas.mpl_connect('draw_event', self._on_draw) # Connect to draw event for initial background capture
        # -----------------------------
        
        self._start_master_animation_loop()

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

                num_points_in_segment = 30
                segment_theta = np.linspace(total_start_theta, total_end_theta, num_points_in_segment)
                segment_r = np.exp(self.b * segment_theta)

                line_obj, = self.ax.plot(segment_theta, segment_r, 'black', linewidth=4, alpha=0.0, picker=5)
                line_obj.set_visible(False) # Start invisible

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

    # --- Manual Blitting Method: Capture Background ---
    def _on_draw(self, event):
        # When the figure is drawn (e.g., initially, or after resize/full redraw),
        # capture the current state as background.
        if event.canvas == self.fig.canvas:
            self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
            # Ensure all animated artists are not part of the background when captured
            for note_key, data in self.notes_data.items():
                data['line'].set_visible(False) # Keep them invisible when background is captured
            self.fig.canvas.draw_idle() # Redraw once more without the lines after background is captured
    # ---------------------------------------------------

    def _on_key_press(self, event):
        if event.key == ' ':
            if not self.enable_animation:
                self._trigger_batch_decay()
        elif event.key == 'a':
            self.enable_animation = not self.enable_animation
            self._update_title()
            print(f"Animation is now {'ON' if self.enable_animation else 'OFF'}")
            
            if self.enable_animation and self.active_notes_list:
                print("Animation enabled. Triggering batch decay for currently active notes.")
                self._trigger_batch_decay(force_animation=True)

    def _on_click(self, event):
        if event.inaxes != self.ax:
            return

        for note_key, data in self.notes_data.items():
            line_obj = data['line']
            contains, _ = line_obj.contains(event)
            if contains:
                # Cancel any ongoing decay for this specific note
                self._cancel_decay_animation_for_note(note_key)

                if not data['highlighted']:
                    data['highlighted'] = True
                    line_obj.set_ydata(data['base_r']) # Reset r to base
                    line_obj.set_alpha(1.0)
                    line_obj.set_visible(True) # Ensure visible

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)

                    if self.enable_animation:
                        self._add_note_to_decay_queue(note_key)
                    
                else: # Un-highlighting a note (typically animation OFF mode)
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0)
                    line_obj.set_visible(False) # Make it logically invisible

                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)

                self._update_status_display()
                # Instead of draw_idle, we might need a full redraw if not manually blitting
                # but with manual blitting below, the animation will handle it
                if not self.enable_animation: # Only force draw if animation is off
                    self.fig.canvas.draw_idle()
                return

    def _start_master_animation_loop(self):
        # We explicitly set blit=False because we are doing manual blitting.
        # This will prevent FuncAnimation's internal blitting logic from interfering.
        self.master_animation = animation.FuncAnimation(self.fig, self._update_decay_animations,
                                                        interval=30,
                                                        blit=False, # Crucial: Turn off FuncAnimation's blitting
                                                        cache_frame_data=False)

    def _update_decay_animations(self, frame):
        # --- Manual Blitting Logic ---
        if self.background is None:
            # First time, or if background was invalidated, force a full redraw to capture background
            self.fig.canvas.draw()
            self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
            # Hide all lines after background captured
            for note_key, data in self.notes_data.items():
                data['line'].set_visible(False)
            self.fig.canvas.draw_idle()

        # Restore the saved background
        self.fig.canvas.restore_region(self.background)
        # -----------------------------

        current_time = time.time()
        lines_to_redraw = []
        notes_to_remove_from_queue = []

        for decay_info in list(self.active_decay_animations):
            note_key, start_time, duration, decay_end_factor, line_obj = decay_info
            
            elapsed_time = current_time - start_time
            progress = min(1.0, elapsed_time / duration)

            if progress < 1.0:
                original_r_data = self.notes_data[note_key]['base_r']
                current_r_factor = 1.0 - progress * (1.0 - decay_end_factor)
                current_alpha = 1.0 - progress

                line_obj.set_ydata(original_r_data * current_r_factor)
                line_obj.set_alpha(current_alpha)
                line_obj.set_visible(True) # Ensure it's visible during animation
                lines_to_redraw.append(line_obj)

                # --- Manual Blitting: Draw individual artist on top of background ---
                self.ax.draw_artist(line_obj)
                # ------------------------------------------------------------------
            else:
                # Animation finished for this note
                line_obj.set_alpha(0.0)
                line_obj.set_visible(False) # Make it logically invisible
                
                if note_key in self.notes_data:
                    self.notes_data[note_key]['highlighted'] = False
                
                notes_to_remove_from_queue.append(decay_info)
        
        # Remove finished animations from the list
        for note_info in notes_to_remove_from_queue:
            if note_info in self.active_decay_animations:
                self.active_decay_animations.remove(note_info)

        # Update status display
        self._update_status_display() # This will call draw_idle, which is fine outside animation loop

        # --- Manual Blitting: Blit the updated region to the screen ---
        # Only blit the changed area, which is the entire axes in this case for simplicity
        # For more fine-grained blitting, you'd need to identify bbox of changed artists.
        self.fig.canvas.blit(self.ax.bbox)
        # -------------------------------------------------------------

        # In manual blitting, we do not return artists, as we draw them directly.
        return [] # Return an empty list for FuncAnimation since we handle drawing manually.


    def _add_note_to_decay_queue(self, note_key):
        self._cancel_decay_animation_for_note(note_key) 
        
        duration = 0.5
        decay_end_factor = 0.5
        line_obj = self.notes_data[note_key]['line']
        
        self.active_decay_animations.append((note_key, time.time(), duration, decay_end_factor, line_obj))

    def _cancel_decay_animation_for_note(self, target_note_key):
        found = False
        for decay_info in list(self.active_decay_animations):
            note_key, _, _, _, line_obj = decay_info
            if note_key == target_note_key:
                line_obj.set_alpha(0.0)
                line_obj.set_visible(False) 
                
                if target_note_key in self.notes_data:
                    self.notes_data[target_note_key]['highlighted'] = False

                self.active_decay_animations.remove(decay_info)
                found = True
                break
        return found

    def _trigger_batch_decay(self, force_animation=False):
        if not self.enable_animation and not force_animation:
            return

        notes_to_decay_keys = []
        for key, data in self.notes_data.items():
            if data['highlighted']:
                notes_to_decay_keys.append(key)
        
        self.active_notes_list.clear()
        self._update_status_display()

        for note_key in notes_to_decay_keys:
            data = self.notes_data[note_key]
            line_obj = data['line']
            
            line_obj.set_ydata(data['base_r'])
            line_obj.set_alpha(1.0)
            line_obj.set_visible(True)

            self._add_note_to_decay_queue(note_key)

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