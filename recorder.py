# recorder.py
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
import platform

OUT_DIR = "recordings"
os.makedirs(OUT_DIR, exist_ok=True)

SCREENSHOT_INTERVAL = 1.0  # seconds
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SECONDS = 5

class Recorder:
    def __init__(self, out_dir=OUT_DIR, screenshot_interval=SCREENSHOT_INTERVAL,
                 audio_sr=AUDIO_SAMPLE_RATE, audio_chunk=AUDIO_CHUNK_SECONDS,
                 audio_device=None):
        self.out_dir = out_dir
        self.screenshot_interval = screenshot_interval
        self.audio_sr = audio_sr
        self.audio_chunk = audio_chunk
        self.audio_device = audio_device

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.out_dir, self.session_id)
        os.makedirs(self.session_dir, exist_ok=True)

        self.events = []
        self.recording_flag = {'on': False}
        self.audio_buffer = []

        self._threads = []
        self._mouse_listener = None
        self._key_listener = None

    # --- workers ---
    def _screenshot_worker(self):
        idx = 0
        while self.recording_flag['on']:
            ts = time.time()
            try:
                img = ImageGrab.grab()
                path = os.path.join(self.session_dir, f"screenshot_{idx:05d}.png")
                img.save(path)
                self.events.append({"ts": ts, "type": "screenshot", "file": path})
                idx += 1
            except Exception as e:
                # log and continue
                print("Screenshot error:", e)
            time.sleep(self.screenshot_interval)

    def _audio_worker(self):
        def callback(indata, frames, time_info, status):
            # copy buffer frames to avoid referencing ephemeral memory
            self.audio_buffer.append(indata.copy())

        try:
            stream = sd.InputStream(samplerate=self.audio_sr, channels=1,
                                    callback=callback, device=self.audio_device)
            stream.start()
        except Exception as e:
            print("Audio input unavailable:", e)
            return  # exit audio thread if audio can't start

        chunk_idx = 0
        try:
            while self.recording_flag['on']:
                time.sleep(self.audio_chunk)
                if self.audio_buffer:
                    chunk = np.concatenate(self.audio_buffer, axis=0)
                    fn = os.path.join(self.session_dir, f"audio_{chunk_idx:04d}.wav")
                    try:
                        wavfile.write(fn, self.audio_sr, (chunk * 32767).astype('int16'))
                        self.events.append({"ts": time.time(), "type": "audio_chunk", "file": fn})
                    except Exception as e:
                        print("Failed to write audio chunk:", e)
                    self.audio_buffer.clear()
                    chunk_idx += 1
        finally:
            try:
                stream.stop()
            except Exception:
                pass

    # input listeners
    def _on_move(self, x, y):
        self.events.append({"ts": time.time(), "type": "mouse_move", "x": x, "y": y})

    def _on_click(self, x, y, button, pressed):
        self.events.append({"ts": time.time(), "type": "mouse_click", "x": x, "y": y,
                            "button": str(button), "pressed": pressed})

    def _on_scroll(self, x, y, dx, dy):
        self.events.append({"ts": time.time(), "type": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy})

    def _on_press(self, key):
        try:
            k = key.char
        except Exception:
            k = str(key)
        self.events.append({"ts": time.time(), "type": "key_down", "key": k})

    def _on_release(self, key):
        try:
            k = key.char
        except Exception:
            k = str(key)
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

def start_recording(audio_device=None):
    global _recorder_singleton
    if _recorder_singleton is None:
        _recorder_singleton = Recorder(audio_device=audio_device)
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
