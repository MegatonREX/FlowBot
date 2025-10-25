# === FILE: recorder.py ===
"""
Recorder: captures screenshots, mouse/keyboard events, and audio chunks.
Saves into recordings/<session_id>/
"""
import os, time, json, threading
from datetime import datetime
from PIL import ImageGrab
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from pynput import mouse, keyboard

OUT_DIR = "recordings"
os.makedirs(OUT_DIR, exist_ok=True)

SCREENSHOT_INTERVAL = 1.0  # seconds
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SECONDS = 5

session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_dir = os.path.join(OUT_DIR, session_id)
os.makedirs(session_dir, exist_ok=True)

events = []
recording_flag = {'on': True}
audio_buffer = []

# Screenshot worker
def screenshot_worker():
    idx = 0
    while recording_flag['on']:
        ts = time.time()
        img = ImageGrab.grab()
        path = os.path.join(session_dir, f"screenshot_{idx:05d}.png")
        img.save(path)
        events.append({"ts": ts, "type": "screenshot", "file": path})
        idx += 1
        time.sleep(SCREENSHOT_INTERVAL)

# Audio worker
def audio_worker():
    def callback(indata, frames, time_info, status):
        audio_buffer.append(indata.copy())
    stream = sd.InputStream(samplerate=AUDIO_SAMPLE_RATE, channels=1, callback=callback)
    stream.start()
    chunk_idx = 0
    try:
        while recording_flag['on']:
            time.sleep(AUDIO_CHUNK_SECONDS)
            if audio_buffer:
                chunk = np.concatenate(audio_buffer, axis=0)
                fn = os.path.join(session_dir, f"audio_{chunk_idx:04d}.wav")
                wavfile.write(fn, AUDIO_SAMPLE_RATE, (chunk * 32767).astype('int16'))
                events.append({"ts": time.time(), "type": "audio_chunk", "file": fn})
                audio_buffer.clear()
                chunk_idx += 1
    finally:
        stream.stop()

# Input listeners
def on_move(x, y):
    events.append({"ts": time.time(), "type": "mouse_move", "x": x, "y": y})

def on_click(x, y, button, pressed):
    events.append({"ts": time.time(), "type": "mouse_click", "x": x, "y": y, "button": str(button), "pressed": pressed})

def on_scroll(x, y, dx, dy):
    events.append({"ts": time.time(), "type": "mouse_scroll", "x": x, "y": y, "dx": dx, "dy": dy})

def on_press(key):
    try:
        k = key.char
    except:
        k = str(key)
    events.append({"ts": time.time(), "type": "key_down", "key": k})

def on_release(key):
    try:
        k = key.char
    except:
        k = str(key)
    events.append({"ts": time.time(), "type": "key_up", "key": k})

if __name__ == "__main__":
    print("Starting local recorder. Press ENTER to stop.")

    t_ss = threading.Thread(target=screenshot_worker, daemon=True)
    t_audio = threading.Thread(target=audio_worker, daemon=True)
    t_ss.start()
    t_audio.start()

    ms = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    ks = keyboard.Listener(on_press=on_press, on_release=on_release)
    ms.start(); ks.start()

    try:
        input("Recording... press ENTER to stop.\n")
    except KeyboardInterrupt:
        pass

    recording_flag['on'] = False
    time.sleep(0.5)

    # write events log
    with open(os.path.join(session_dir, "events.json"), "w") as f:
        json.dump(events, f, indent=2)
    print("Saved session to", session_dir)


# === FILE: analyzer.py ===
"""
Analyzer: convert recordings into structured workflow JSON and a short summary.
- Performs simple OCR with pytesseract
- Optionally uses Whisper (if installed) for transcription
- Heuristic segmentation of steps based on clicks and key events
"""
import os, json, cv2, pytesseract, time
from datetime import datetime
from collections import defaultdict
import pytesseract

RECORDINGS = "recordings"
WORKFLOWS = "workflows"
os.makedirs(WORKFLOWS, exist_ok=True)

# Optional: whisper import if available (not required)
try:
    import whisper
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def ocr_image(path):
    img = cv2.imread(path)
    if img is None:
        return ""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip()


def transcribe_audio(path):
    if WHISPER_AVAILABLE:
        model = whisper.load_model("small")
        res = model.transcribe(path)
        return res.get("text","")
    else:
        # basic fallback: return filename only
        return f"[audio:{os.path.basename(path)}]"


def load_session(session_dir):
    with open(os.path.join(session_dir, "events.json"), "r") as f:
        events = json.load(f)
    screenshots = [e for e in events if e['type'] == 'screenshot']
    screenshots.sort(key=lambda e: e['ts'])
    ocr_cache = {}
    for s in screenshots:
        ocr_cache[s['file']] = ocr_image(s['file'])
    return events, ocr_cache


def heuristics_segment(events, ocr_cache):
    steps = []
    idx = 0
    for e in events:
        if e['type'] in ('mouse_click', 'key_down'):
            before_screens = [s for s in events if s['type'] == 'screenshot' and s['ts'] <= e['ts']]
            snap = before_screens[-1]['file'] if before_screens else None
            step = {
                "step_id": f"step_{idx}",
                "ts": e['ts'],
                "action": e['type'],
                "details": {k: v for k, v in e.items() if k not in ('ts', 'type')},
                "screenshot": snap,
                "ocr_text": ocr_cache.get(snap, "") if snap else ""
            }
            steps.append(step)
            idx += 1
    return steps


def summarize_workflow(steps):
    if not steps:
        return "No deterministic steps detected."
    first = steps[0]['ocr_text'][:120].replace('\n',' ')
    last = steps[-1]['ocr_text'][:120].replace('\n',' ')
    return f"Workflow of {len(steps)} steps. Starts near: '{first}' and ends near: '{last}'."


def detect_repeats(read_dir):
    seq_map = defaultdict(list)
    for session in os.listdir(read_dir):
        sd = os.path.join(read_dir, session)
        if not os.path.isdir(sd):
            continue
        evts, ocr = load_session(sd)
        steps = heuristics_segment(evts, ocr)
        key = " | ".join([s['ocr_text'][:50] for s in steps])
        if key.strip():
            seq_map[key].append(session)
    repeats = {k: v for k, v in seq_map.items() if len(v) > 1}
    return repeats


if __name__ == '__main__':
    sessions = sorted(os.listdir(RECORDINGS))
    if not sessions:
        print("No recordings found. Run recorder.py first.")
        exit(1)
    session = sessions[-1]
    session_dir = os.path.join(RECORDINGS, session)
    print("Analyzing", session_dir)
    events, ocr_cache = load_session(session_dir)
    steps = heuristics_segment(events, ocr_cache)

    # transcribe any audio chunks (optional)
    for e in events:
        if e['type'] == 'audio_chunk':
            txt = transcribe_audio(e['file'])
            events_text = next((s for s in steps if abs(s['ts'] - e['ts']) < 3), None)
            if events_text:
                events_text.setdefault('transcripts', []).append(txt)

    summary = summarize_workflow(steps)
    workflow = {
        "session": session,
        "generated_at": datetime.now().isoformat(),
        "num_steps": len(steps),
        "steps": steps,
        "summary": summary
    }
    out_fn = os.path.join(WORKFLOWS, f"workflow_{session}.json")
    with open(out_fn, "w") as f:
        json.dump(workflow, f, indent=2)
    print("Saved workflow:", out_fn)

    repeats = detect_repeats(RECORDINGS)
    if repeats:
        print("Detected repeated sequences across sessions (keys truncated):")
        for k, v in repeats.items():
            print(" - seen in", v)


# === FILE: automator.py ===
"""
Automator: dry-run and replay workflows produced by analyzer.py
Uses pyautogui to simulate clicks and typing. Always dry-run first.
"""
import os, json, time, pyautogui

WORKFLOWS = "workflows"

pyautogui.FAILSAFE = True  # move mouse to corner to abort


def load_workflow(path):
    with open(path, "r") as f:
        return json.load(f)


def dry_run(workflow):
    print("Dry run: sequence of actions to perform:")
    for s in workflow['steps']:
        print(f" - {s['step_id']} @ {s['ts']}: {s['action']} {s['details']} (ocr: {s['ocr_text'][:60]!r})")


def replay(workflow, speed=1.0):
    print("Starting replay in 5 seconds. Move mouse to top-left corner to abort.")
    time.sleep(5)
    for s in workflow['steps']:
        act = s['action']
        d = s['details']
        if act == 'mouse_click':
            x, y = int(d['x']), int(d['y'])
            pyautogui.moveTo(x, y, duration=0.2 * speed)
            pyautogui.click()
        elif act == 'key_down':
            k = d['key']
            # If it's a string of characters, type it; else try press
            try:
                pyautogui.typewrite(str(k), interval=0.01 * speed)
            except Exception:
                try:
                    pyautogui.press(str(k))
                except Exception:
                    pass
        time.sleep(0.2 * speed)


if __name__ == '__main__':
    flows = sorted([f for f in os.listdir(WORKFLOWS) if f.endswith('.json')])
    if not flows:
        print("No workflows found. Run analyzer.py first.")
        exit(1)
    print("Workflows:")
    for i, f in enumerate(flows):
        print(i, f)
    idx = int(input("Choose workflow index to run: "))
    wf = load_workflow(os.path.join(WORKFLOWS, flows[idx]))
    dry_run(wf)
    ok = input("Type YES to run this workflow (will send real input): ")
    if ok.strip().upper() == "YES":
        replay(wf)
    else:
        print("Aborted.")


# === FILE: gui.py ===
"""
Minimal PySimpleGUI frontend to orchestrate recorder -> analyzer -> automator
"""
import os, threading, subprocess
import PySimpleGUI as sg

RECORDER = 'recorder.py'
ANALYZER = 'analyzer.py'
AUTOMATOR = 'automator.py'

layout = [
    [sg.Text('AGI Assistant MVP', font=('Any', 16))],
    [sg.Button('Start Recorder'), sg.Button('Analyze Last'), sg.Button('Run Automator')],
    [sg.Multiline(size=(80,20), key='-LOG-')]
]

window = sg.Window('AGI Assistant MVP', layout)

def log(msg):
    window['-LOG-'].print(msg)

while True:
    event, values = window.read(timeout=100)
    if event == sg.WIN_CLOSED:
        break
    if event == 'Start Recorder':
        log('Starting recorder in a new terminal...')
        # spawn recorder in background
        threading.Thread(target=lambda: os.system(f'python {RECORDER}'), daemon=True).start()
    if event == 'Analyze Last':
        log('Running analyzer...')
        os.system(f'python {ANALYZER}')
        log('Analyzer finished.')
    if event == 'Run Automator':
        log('Starting automator...')
        os.system(f'python {AUTOMATOR}')
        log('Automator finished.')

window.close()
