"""
Recorder: captures screenshots, mouse/keyboard events, and audio chunks.
Saves into recordings/<session_id>/

Provides a Recorder class with start() and stop() so main.py can orchestrate it.
"""
import os, time, json, threading
from datetime import datetime
from PIL import ImageGrab
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from pynput import mouse, keyboard
from pynput.keyboard import Key
import platform
import cv2  # for efficient image processing

OUT_DIR = "recordings"
os.makedirs(OUT_DIR, exist_ok=True)

# Screenshot configuration
SCREENSHOT_INTERVAL = 1.0  # seconds between checks
SCREENSHOT_DIFF_THRESHOLD = 10  # minimum average pixel difference to save
SCREENSHOT_FORCE_INTERVAL = 10  # force save every 10 seconds if no changes

AUDIO_SAMPLE_RATE = 16000

def compute_frame_difference(frame1, frame2):
    """
    Compute average pixel difference between two frames.
    Returns difference value between 0-255.
    """
    if frame1 is None or frame2 is None:
        return float('inf')  # Guarantee save if either frame is None
    
    # Convert to grayscale numpy arrays for efficient comparison
    gray1 = cv2.cvtColor(np.array(frame1), cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(np.array(frame2), cv2.COLOR_RGB2GRAY)
    
    # Compute absolute difference and average
    diff = np.mean(np.abs(gray2.astype(float) - gray1.astype(float)))
    return diff

class Recorder:
    def __init__(self, out_dir=OUT_DIR, screenshot_interval=SCREENSHOT_INTERVAL,
                 audio_sr=AUDIO_SAMPLE_RATE, audio_device=None):
        self.out_dir = out_dir
        self.screenshot_interval = screenshot_interval
        self.audio_sr = audio_sr
        self.audio_device = audio_device

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.out_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        # File for continuous audio recording
        self.audio_file = os.path.join(self.session_dir, "recording.wav")

        self.events = []
        self.recording_flag = {'on': False}
        self.audio_buffer = []

        # Screenshot state tracking
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_count = 0
        self._screenshot_lock = threading.Lock()

        # Track currently pressed modifier keys
        self.pressed_modifiers = set()
        self.modifier_keys = {
            Key.ctrl, Key.ctrl_l, Key.ctrl_r,
            Key.shift, Key.shift_l, Key.shift_r,
            Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr,
            Key.cmd, Key.cmd_l, Key.cmd_r  # Mac Command key
        }

        self._threads = []
        self._mouse_listener = None
        self._key_listener = None
        
    def _capture_event_screenshot(self, ts):
        """
        Capture and save a screenshot triggered by an event (click/keypress).
        Uses a lock to prevent concurrent screenshot saves.
        Returns the path to the saved screenshot.
        """
        with self._screenshot_lock:
            try:
                img = ImageGrab.grab()
                path = os.path.join(self.session_dir, f"screenshot_{self.screenshot_count:05d}.png")
                img.save(path)
                self.screenshot_count += 1
                self.last_screenshot = img
                self.last_screenshot_time = ts
                print(f"\033[36m[Screenshot]\033[0m Saved event-triggered capture to {os.path.basename(path)}")
                return path
            except Exception as e:
                print(f"\033[31m[Error]\033[0m Screenshot capture failed: {e}")
                return None

    # --- workers ---
    def _screenshot_worker(self):
        """
        Smart screenshot worker that:
        1. Captures screen every SCREENSHOT_INTERVAL
        2. Saves if significant changes detected (diff > 5)
        3. Forces save every 5 seconds if no activity
        """
        last_force_save = 0
        last_activity = time.time()
        
        while self.recording_flag['on']:
            ts = time.time()
            try:
                current_frame = ImageGrab.grab()
                
                # Compute difference from last saved frame
                diff = compute_frame_difference(self.last_screenshot, current_frame)
                
                # Check conditions for saving
                significant_change = diff >= SCREENSHOT_DIFF_THRESHOLD
                time_since_last_save = ts - last_force_save
                should_force_save = time_since_last_save >= SCREENSHOT_FORCE_INTERVAL
                
                # Save if we detect changes or it's time for forced save
                if significant_change or should_force_save:
                    with self._screenshot_lock:
                        path = os.path.join(self.session_dir, f"screenshot_{self.screenshot_count:05d}.png")
                        current_frame.save(path)
                        self.events.append({"ts": ts, "type": "screenshot", "file": path})
                        self.screenshot_count += 1
                        self.last_screenshot = current_frame
                        self.last_screenshot_time = ts
                        last_force_save = ts
                        
                        if significant_change:
                            print(f"\033[36m[Screenshot]\033[0m Saved on change (diff: {diff:.1f})")
                        else:
                            print(f"\033[36m[Screenshot]\033[0m Periodic save after {time_since_last_save:.1f}s")
                else:
                    print(f"\033[90m[Screenshot]\033[0m No significant changes (diff: {diff:.1f})\033[0m", end="\r")
                    
            except Exception as e:
                print(f"\033[31m[Error]\033[0m Screenshot error: {e}")
                
            # Sleep for the interval
            time.sleep(self.screenshot_interval)

    def _audio_worker(self):
        def callback(indata, frames, time_info, status):
            if status:
                print(f"Audio callback status: {status}")
            # copy buffer frames to avoid referencing ephemeral memory
            self.audio_buffer.append(indata.copy())

        try:
            stream = sd.InputStream(samplerate=self.audio_sr, channels=1,
                                    callback=callback, device=self.audio_device)
            stream.start()
            print("Started audio recording...")
        except Exception as e:
            print("Audio input unavailable:", e)
            return  # exit audio thread if audio can't start

        try:
            # Keep the stream running until recording is stopped
            while self.recording_flag['on']:
                time.sleep(0.1)  # Short sleep to prevent CPU hogging
            
            # When recording stops, save the complete buffer
            if self.audio_buffer:
                complete_audio = np.concatenate(self.audio_buffer, axis=0)
                try:
                    wavfile.write(self.audio_file, self.audio_sr, (complete_audio * 32767).astype('int16'))
                    self.events.append({
                        "ts": time.time(),
                        "type": "audio_recording",
                        "file": self.audio_file,
                        "duration": len(complete_audio) / self.audio_sr
                    })
                    print(f"Saved audio recording ({len(complete_audio) / self.audio_sr:.1f} seconds)")
                except Exception as e:
                    print("Failed to write audio file:", e)
        finally:
            try:
                stream.stop()
                print("Stopped audio recording.")
            except Exception:
                pass

    # input listeners
    def _on_move(self, x, y):
        self.events.append({"ts": time.time(), "type": "mouse_move", "x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        ts = time.time()
        event = {"ts": ts, "type": "mouse_click", "x": x, "y": y,
                 "button": str(button), "pressed": pressed}
        
        # Take screenshot on mouse click (when pressed, not released)
        if pressed:
            screenshot_path = self._capture_event_screenshot(ts)
            if screenshot_path:
                event["screenshot"] = screenshot_path
                print(f"\033[36m[Screenshot]\033[0m Captured on mouse click")
                
        self.events.append(event)

    def _on_scroll(self, x, y, dx, dy):
        self.events.append({"ts": time.time(), "type": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy})

    def _get_key_string(self, key):
        """Convert key to string representation"""
        try:
            return key.char
        except AttributeError:
            return str(key)

    def _on_press(self, key):
        ts = time.time()
        k = self._get_key_string(key)
        
        # Track modifier keys - UPDATE modifiers BEFORE recording the event
        if key in self.modifier_keys:
            self.pressed_modifiers.add(key)
        
        # Build modifiers string for the event
        modifiers = []
        if any(k in self.pressed_modifiers for k in [Key.ctrl, Key.ctrl_l, Key.ctrl_r]):
            modifiers.append("ctrl")
        if any(k in self.pressed_modifiers for k in [Key.shift, Key.shift_l, Key.shift_r]):
            modifiers.append("shift")
        if any(k in self.pressed_modifiers for k in [Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr]):
            modifiers.append("alt")
        if any(k in self.pressed_modifiers for k in [Key.cmd, Key.cmd_l, Key.cmd_r]):
            modifiers.append("cmd")
        
        event = {
            "ts": ts, 
            "type": "key_down", 
            "key": k,
            "modifiers": modifiers if modifiers else []
        }
        
        # DON'T record standalone modifier key presses - they're just part of shortcuts
        if key in self.modifier_keys:
            # Skip recording this event - modifiers are tracked but not logged separately
            return
        
        # Only capture screenshot on Enter key WITHOUT modifiers
        # This prevents screenshots when doing shortcuts like Cmd+Enter
        if k == 'Key.enter' and not modifiers:
            screenshot_path = self._capture_event_screenshot(ts)
            if screenshot_path:
                event["screenshot"] = screenshot_path
                print(f"\033[36m[Screenshot]\033[0m Captured on Enter key press")
        
        # Log keyboard shortcuts for debugging
        if modifiers and key not in self.modifier_keys:
            shortcut = "+".join(modifiers) + "+" + k
            print(f"\033[33m[Shortcut]\033[0m {shortcut}")
            
        self.events.append(event)

    def _on_release(self, key):
        k = self._get_key_string(key)
        
        # Remove from pressed modifiers
        if key in self.modifier_keys:
            self.pressed_modifiers.discard(key)
            # Don't record modifier releases either
            return
        
        self.events.append({"ts": time.time(), "type": "key_up", "key": k})

    # --- public control ---
    def start(self, start_listeners=True):
        if self.recording_flag['on']:
            print("Recorder already running.")
            return
        self.recording_flag['on'] = True

        t_ss = threading.Thread(target=self._screenshot_worker, daemon=True)
        self._threads.append(t_ss)
        t_ss.start()

        t_audio = threading.Thread(target=self._audio_worker, daemon=True)
        self._threads.append(t_audio)
        t_audio.start()

        if start_listeners:
            # start mouse & keyboard listeners
            self._mouse_listener = mouse.Listener(
                on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll)
            self._key_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._mouse_listener.start()
            self._key_listener.start()

        print(f"Recorder started (session: {self.session_id}).")

    def stop(self):
        if not self.recording_flag['on']:
            print("Recorder not running.")
            return
        self.recording_flag['on'] = False
        # wait a short moment for threads to flush buffers
        time.sleep(0.5)

        # stop listeners
        try:
            if self._mouse_listener:
                self._mouse_listener.stop()
            if self._key_listener:
                self._key_listener.stop()
        except Exception:
            pass

        # write events log
        try:
            with open(os.path.join(self.session_dir, "events.json"), "w") as f:
                json.dump(self.events, f, indent=2)
            print("Saved session to", self.session_dir)
        except Exception as e:
            print("Failed to save events.json:", e)

    def get_session_dir(self):
        return self.session_dir

    def get_events(self):
        return list(self.events)  # return a copy

# Convenience functions for quick usage
_recorder_singleton = None

def start_recording(audio_device=None, countdown=3):
    global _recorder_singleton
    if _recorder_singleton is None:
        _recorder_singleton = Recorder(audio_device=audio_device)

    if countdown > 0:
        print(f"Starting recording in {countdown} seconds...")
        for i in range(countdown, 0, -1):
            print(f"{i}...", end="\r", flush=True)
            time.sleep(1)
        print("Recording started!\n")

    _recorder_singleton.start()
    return _recorder_singleton

def stop_recording():
    global _recorder_singleton
    if _recorder_singleton:
        _recorder_singleton.stop()
        # return the session dir just saved
        sd = _recorder_singleton.get_session_dir()
        _recorder_singleton = None
        return sd
    return None

# keep backwards-compatibility as script
if __name__ == "__main__":
    print("Starting local recorder. Press ENTER to stop.")
    r = start_recording()
    try:
        input("Recording... press ENTER to stop.\n")
    except KeyboardInterrupt:
        pass
    stop_recording()