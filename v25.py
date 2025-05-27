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
        self._draw_notes_segments() # All notes start invisible
        self._add_status_display()
        self._connect_events()
        
        # --- Manual Blitting Setup (Moved background capture to a more controlled point) ---
        self.background = None 
        # Connect to 'draw_event' only for the *first* background capture and subsequent redraws
        # when the entire figure is drawn (e.g., resizing window).
        # We'll trigger the initial capture explicitly.
        self.fig.canvas.mpl_connect('draw_event', self._on_initial_draw_capture)
        # ---------------------------------------------------------------------------------
        
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
                line_obj.set_visible(False) # All notes start invisible

                note_name = self._get_note_name(octave_idx, semitone_idx)
                self.notes_data[(octave_idx, semitone_idx)] = {
                    'line': line_obj,
                    'highlighted': False, # Logical state for if note *should* be visible/highlighted
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
        # Use fig.canvas.draw_idle() to allow event loop to update it later
        self.status_text.set_text(display_text)
        self.fig.canvas.draw_idle()

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)

    # --- Manual Blitting Method: Initial Background Capture ---
    # This will be called *once* when figure is first drawn.
    # Also serves for redraws (e.g. window resize) but must be careful.
    def _on_initial_draw_capture(self, event):
        if event.canvas == self.fig.canvas and self.background is None: # Only capture if background is not set
            print("Capturing initial background...")
            # Temporarily hide all lines to capture a clean background
            for note_data in self.notes_data.values():
                note_data['line'].set_visible(False)
            
            # The figure is already drawn by the initial plt.show() or draw_idle,
            # so we just copy the content. No need to call draw() here.
            self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
            
            # Now, restore visibility for notes that should be highlighed
            # This is typically for animation OFF mode when notes are clicked and stay.
            for note_data in self.notes_data.values():
                if note_data['highlighted'] and not self.enable_animation:
                    note_data['line'].set_visible(True)
                    note_data['line'].set_alpha(1.0)
            
            # Ensure the canvas updates to show any initially highlighted notes
            self.fig.canvas.draw_idle() 

    def _recreate_background(self):
        # Function to manually force a background recreation when needed
        print("Recreating background...")
        # Temporarily hide all lines
        for note_data in self.notes_data.values():
            note_data['line'].set_visible(False)
        
        # Force a full draw of the canvas. This will also trigger _on_initial_draw_capture
        # but the check `self.background is None` will prevent re-capturing if it's already set.
        self.fig.canvas.draw() 
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        
        # Restore visibility for notes that are supposed to be active (e.g., in animation OFF mode)
        for note_data in self.notes_data.values():
            if note_data['highlighted'] and not self.enable_animation:
                note_data['line'].set_visible(True)
                note_data['line'].set_alpha(1.0)
        self.fig.canvas.draw_idle()

    def _on_key_press(self, event):
        if event.key == ' ':
            if not self.enable_animation:
                self._trigger_batch_decay()
        elif event.key == 'a':
            # --- IMPORTANT: Before toggling, force a full redraw to update background if needed ---
            # This ensures that when animation is turned ON, the background is clean for blitting.
            # And when OFF, it's captured correctly.
            self._recreate_background() # Recapture background for clean state

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
                # Always cancel any ongoing decay for this specific note
                # This ensures the note is set to alpha=0.0 and visible=False initially if it was decaying
                self._cancel_decay_animation_for_note(note_key) # This will hide it if it was decaying

                if not data['highlighted']: # Clicking an unhighlighted note
                    data['highlighted'] = True
                    line_obj.set_ydata(data['base_r'])
                    line_obj.set_alpha(1.0)
                    line_obj.set_visible(True) 

                    note_name = data['name']
                    if note_name not in self.active_notes_list:
                        self.active_notes_list.append(note_name)

                    if self.enable_animation:
                        self._add_note_to_decay_queue(note_key)
                    
                else: # Clicking an already highlighted note (to un-highlight)
                    # This happens primarily in animation OFF mode
                    data['highlighted'] = False
                    line_obj.set_alpha(0.0)
                    line_obj.set_visible(False) # Make it disappear

                    note_name = data['name']
                    if note_name in self.active_notes_list:
                        self.active_notes_list.remove(note_name)

                self._update_status_display()
                # Request a redraw if animation is OFF, as manual blitting won't happen for static changes
                if not self.enable_animation:
                    # In animation OFF mode, after click, we need to redraw the canvas
                    # to show/hide the note instantly.
                    self.fig.canvas.draw_idle()
                return

    def _start_master_animation_loop(self):
        # We explicitly set blit=False because we are doing manual blitting.
        # This will prevent FuncAnimation's internal blitting logic from interfering.
        self.master_animation = animation.FuncAnimation(self.fig, self._update_decay_animations,
                                                        interval=30,
                                                        blit=False, 
                                                        cache_frame_data=False)

    def _update_decay_animations(self, frame):
        # --- Manual Blitting Logic ---
        # Ensure background is captured only once initially, or re-captured on resize/toggle 'a'
        if self.background is None:
            self._recreate_background() # Force initial background capture if not done
            if self.background is None: # Defensive check
                return [] # Cannot proceed without background

        # Restore the saved background to clear previous frame's artists
        self.fig.canvas.restore_region(self.background)
        # -----------------------------

        current_time = time.time()
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

        self._update_status_display() 
        
        # --- Manual Blitting: Blit the updated region to the screen ---
        self.fig.canvas.blit(self.ax.bbox)
        # -------------------------------------------------------------

        return [] # Return empty list for FuncAnimation with blit=False


    def _add_note_to_decay_queue(self, note_key):
        # Ensures that a note is not added to decay queue if it's already decaying
        # and resets its state to start decay properly.
        # This will set highlighted=False for the note if it was in active_decay_animations
        self._cancel_decay_animation_for_note(note_key, set_invisible=False) 
        
        duration = 0.5
        decay_end_factor = 0.5
        line_obj = self.notes_data[note_key]['line']
        
        self.active_decay_animations.append((note_key, time.time(), duration, decay_end_factor, line_obj))

    def _cancel_decay_animation_for_note(self, target_note_key, set_invisible=True):
        found = False
        for decay_info in list(self.active_decay_animations):
            note_key, _, _, _, line_obj = decay_info
            if note_key == target_note_key:
                if set_invisible: 
                    line_obj.set_alpha(0.0)
                    line_obj.set_visible(False) 
                
                if target_note_key in self.notes_data:
                    self.notes_data[target_note_key]['highlighted'] = False # This ensures logical state reset

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
            line_obj.set_visible(True) # Ensure visible before decay

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