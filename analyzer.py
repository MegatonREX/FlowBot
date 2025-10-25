# analyzer.py
"""
Analyzer module (refactored).

Provides:
- analyze_session(session_dir, out_dir=WORKFLOWS, use_whisper=False)
    -> returns workflow dict and writes workflows/workflow_<session>.json

- analyze_latest(recordings_dir=RECORDINGS)
- detect_repeats(read_dir=RECORDINGS)
- CLI behavior when run directly

Improvements vs the simple script:
- OCR caching per screenshot (avoids re-run)
- Graceful errors on missing files / unreadable images
- Optional Whisper model loaded once
- Returns workflow dict for programmatic use
"""
import os
import json
import cv2
import time
import pytesseract
from datetime import datetime
from collections import defaultdict

# Config
RECORDINGS = "recordings"
WORKFLOWS = "workflows"
os.makedirs(WORKFLOWS, exist_ok=True)

# If your tesseract is in a nonstandard place, change here
DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.name == "nt":
    # Guard in case user did not add to PATH
    pytesseract.pytesseract.tesseract_cmd = DEFAULT_TESSERACT_CMD

# Whisper lazy load
WHISPER_AVAILABLE = False
_whisper_model = None
def _ensure_whisper(model_name="small"):
    global WHISPER_AVAILABLE, _whisper_model
    if WHISPER_AVAILABLE and _whisper_model is not None:
        return _whisper_model
    try:
        import whisper
        _whisper_model = whisper.load_model(model_name)
        WHISPER_AVAILABLE = True
        return _whisper_model
    except Exception:
        WHISPER_AVAILABLE = False
        _whisper_model = None
        return None

# -------------------
# Utility functions
# -------------------
def _safe_imread(path):
    try:
        img = cv2.imread(path)
        return img
    except Exception:
        return None

def ocr_image(path, ocr_cache=None):
    """
    Read image at path, run OCR (Tesseract), and return text.
    Uses optional ocr_cache dict to avoid repeated OCR calls.
    """
    if ocr_cache is None:
        ocr_cache = {}
    if path in ocr_cache:
        return ocr_cache[path]

    img = _safe_imread(path)
    if img is None:
        ocr_cache[path] = ""
        return ""
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        text = text.strip()
    except Exception:
        text = ""
    ocr_cache[path] = text
    return text

def transcribe_audio(path, use_whisper=False, model_name="small"):
    """
    Transcribe audio at path. If use_whisper==True and whisper is installed,
    uses Whisper model (loaded once). Otherwise returns placeholder text.
    """
    if not use_whisper:
        return f"[audio:{os.path.basename(path)}]"

    model = _ensure_whisper(model_name=model_name)
    if model is None:
        return f"[audio:{os.path.basename(path)}]"
    try:
        res = model.transcribe(path)
        return res.get("text", "")
    except Exception:
        return f"[audio:{os.path.basename(path)}]"

# -------------------
# Core analyzer API
# -------------------
def load_session(session_dir):
    """
    Load events.json and precompute OCR for screenshots.
    Returns (events, ocr_cache)
    """
    events_path = os.path.join(session_dir, "events.json")
    if not os.path.exists(events_path):
        raise FileNotFoundError(f"events.json not found in {session_dir}")

    with open(events_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    # collect screenshots only around events
    screenshots = [e for e in events if e.get("type") == "screenshot"]
    screenshots.sort(key=lambda e: e.get("ts", 0))
    ocr_cache = {}
    for s in screenshots:
        fp = s.get("file")
        if fp and os.path.exists(fp):
            # lightweight - only OCR each screenshot once
            ocr_image(fp, ocr_cache=ocr_cache)
    return events, ocr_cache

def heuristics_segment(events, ocr_cache):
    """
    Convert raw events into step list using simple heuristics:
    - Create a step on mouse_click or key_down
    - Attach nearest previous screenshot and OCR text
    """
    steps = []
    idx = 0
    for e in events:
        if e.get("type") in ("mouse_click", "key_down"):
            # find latest screenshot before this event
            snaps = [s for s in events if s.get("type") == "screenshot" and s.get("ts", 0) <= e.get("ts", 0)]
            snap = snaps[-1]["file"] if snaps else None
            step = {
                "step_id": f"step_{idx}",
                "ts": e.get("ts"),
                "action": e.get("type"),
                "details": {k: v for k, v in e.items() if k not in ("ts", "type")},
                "screenshot": snap,
                "ocr_text": ocr_cache.get(snap, "") if snap else ""
            }
            steps.append(step)
            idx += 1
    return steps

def summarize_workflow(steps):
    if not steps:
        return "No deterministic steps detected."
    first = (steps[0].get("ocr_text","") or "")[:120].replace("\n"," ")
    last = (steps[-1].get("ocr_text","") or "")[:120].replace("\n"," ")
    return f"Workflow of {len(steps)} steps. Starts near: '{first}' and ends near: '{last}'."

def analyze_session(session_dir, out_dir=WORKFLOWS, use_whisper=False, whisper_model="small"):
    """
    Analyze a single recording session directory and produce workflow JSON.
    Returns the workflow dict.
    """
    # load and OCR
    events, ocr_cache = load_session(session_dir)
    steps = heuristics_segment(events, ocr_cache)

    # transcribe audio chunks and attach to nearest step
    for e in events:
        if e.get("type") == "audio_chunk":
            audio_path = e.get("file")
            if audio_path and os.path.exists(audio_path):
                txt = transcribe_audio(audio_path, use_whisper=use_whisper, model_name=whisper_model)
                # attach to nearest step within a threshold (seconds)
                nearest = None
                min_dt = 1e9
                for s in steps:
                    dt = abs((s.get("ts") or 0) - e.get("ts",0))
                    if dt < min_dt:
                        min_dt = dt
                        nearest = s
                if nearest and min_dt < 5:  # within 5 seconds
                    nearest.setdefault("transcripts", []).append(txt)

    summary = summarize_workflow(steps)
    workflow = {
        "session": os.path.basename(session_dir.rstrip(os.sep)),
        "generated_at": datetime.now().isoformat(),
        "num_steps": len(steps),
        "steps": steps,
        "summary": summary
    }

    # write to disk
    os.makedirs(out_dir, exist_ok=True)
    out_fn = os.path.join(out_dir, f"workflow_{workflow['session']}.json")
    try:
        with open(out_fn, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Failed to write workflow JSON:", e)

    return workflow

def analyze_latest(recordings_dir=RECORDINGS, out_dir=WORKFLOWS, use_whisper=False, whisper_model="small"):
    """
    Convenience: analyze the most recent session in recordings_dir.
    """
    sessions = sorted([d for d in os.listdir(recordings_dir) if os.path.isdir(os.path.join(recordings_dir, d))])
    if not sessions:
        raise FileNotFoundError("No recording sessions found")
    latest = sessions[-1]
    return analyze_session(os.path.join(recordings_dir, latest), out_dir=out_dir, use_whisper=use_whisper, whisper_model=whisper_model)

def detect_repeats(read_dir=RECORDINGS):
    """
    Naive repeat detector: groups sessions by concatenated OCR text sequence.
    Returns dict {sequence_key: [session_ids...]}
    """
    seq_map = defaultdict(list)
    for session in os.listdir(read_dir):
        sd = os.path.join(read_dir, session)
        if not os.path.isdir(sd):
            continue
        try:
            evts, ocr = load_session(sd)
            steps = heuristics_segment(evts, ocr)
            key = " | ".join([ (s.get("ocr_text","") or "")[:50] for s in steps ])
            if key.strip():
                seq_map[key].append(session)
        except Exception:
            continue
    repeats = {k: v for k, v in seq_map.items() if len(v) > 1}
    return repeats

# CLI behavior
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze a recording session into a workflow JSON.")
    parser.add_argument("--session", "-s", type=str, default=None, help="Path to session dir (default: latest in recordings/)")
    parser.add_argument("--whisper", action="store_true", help="Use Whisper transcription if available")
    args = parser.parse_args()

    if args.session:
        sd = args.session
    else:
        sessions = sorted([d for d in os.listdir(RECORDINGS) if os.path.isdir(os.path.join(RECORDINGS, d))])
        if not sessions:
            print("No recordings found. Run recorder.py first.")
            raise SystemExit(1)
        sd = os.path.join(RECORDINGS, sessions[-1])

    print("Analyzing", sd)
    wf = analyze_session(sd, use_whisper=args.whisper)
    print("Saved workflow for", wf["session"])
    repeats = detect_repeats(RECORDINGS)
    if repeats:
        print("Detected repeated sequences across sessions (keys truncated):")
        for k, v in repeats.items():
            print(" - seen in", v)
