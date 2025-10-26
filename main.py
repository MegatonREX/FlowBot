import threading
import time
import os
import argparse

from recorder import start_recording, stop_recording
import analyzer

RECORDINGS_DIR = "recordings"

def analyze_one(session_dir, use_vosk=False):
    try:
        print(f"[Analyzer] Processing {session_dir} ...")
        wf = analyzer.analyze_session(session_dir, use_vosk=use_vosk)
        print(f"[Analyzer] Saved workflow to {wf['session']}")
    except Exception as e:
        print(f"[Analyzer] Error analyzing session:", e)

def analyzer_watcher(stop_event, use_vosk=False, poll_interval=2):
    """Watches recordings/ and analyzes any new sessions found."""
    seen = set()
    while not stop_event.is_set():
        try:
            sessions = sorted([
                d for d in os.listdir(RECORDINGS_DIR)
                if os.path.isdir(os.path.join(RECORDINGS_DIR, d))
            ])
        except FileNotFoundError:
            sessions = []
        for s in sessions:
            if s in seen:
                continue
            session_dir = os.path.join(RECORDINGS_DIR, s)
            events_file = os.path.join(session_dir, "events.json")
            if os.path.exists(events_file):
                analyze_one(session_dir, use_vosk=use_vosk)
                seen.add(s)
        time.sleep(poll_interval)

def interactive_record_once(use_vosk=False):
    rec = start_recording()
    print("Recording... press ENTER to stop.")
    try:
        input()
    except KeyboardInterrupt:
        print("\nInterrupted by user (Ctrl+C). Stopping recorder.")
    session_dir = stop_recording()
    if session_dir:
        analyze_one(session_dir, use_vosk=use_vosk)
    else:
        print("No session saved.")

def continuous_mode(use_vosk=False):
    stop_event = threading.Event()
    watcher = threading.Thread(target=analyzer_watcher, args=(stop_event, use_vosk), daemon=True)
    watcher.start()

    start_recording()
    print("Continuous recording & analysis running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        stop_event.set()
        sd = stop_recording()
        time.sleep(0.5)
        print("Stopped. Last session:", sd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGI Assistant main orchestrator")
    parser.add_argument("--mode", choices=["once", "continuous"], default="once",
                        help="once: record one session and analyze it; continuous: keep recording and auto-analyze")
    parser.add_argument("--vosk", action="store_true", help="Use Vosk transcription instead of Whisper")
    args = parser.parse_args()

    # use vosk transcription with flag
    # if args.mode == "once":
    #     interactive_record_once(use_vosk=args.vosk)
    # else:
    #     continuous_mode(use_vosk=args.vosk)

    # 🔹 Force Vosk to be the default
    use_vosk = True if not args.vosk else args.vosk

    if args.mode == "once":
        interactive_record_once(use_vosk=use_vosk)
    else:
        continuous_mode(use_vosk=use_vosk)
