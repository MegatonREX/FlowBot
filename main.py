# main.py
import threading
import time
import os
import argparse

from recorder import start_recording, stop_recording
import analyzer

RECORDINGS_DIR = "recordings"

def analyze_one(session_dir, use_whisper=False):
    try:
        print(f"[Analyzer] Processing {session_dir} ...")
        wf = analyzer.analyze_session(session_dir, use_whisper=use_whisper)
        print(f"[Analyzer] Saved workflow for {wf['session']} ({wf['num_steps']} steps).")
    except Exception as e:
        print("[Analyzer] Error analyzing session:", e)

def analyzer_watcher(stop_event, use_whisper=False, poll_interval=2):
    """Watches recordings/ and analyzes any new sessions found."""
    seen = set()
    while not stop_event.is_set():
        try:
            sessions = sorted([d for d in os.listdir(RECORDINGS_DIR) if os.path.isdir(os.path.join(RECORDINGS_DIR, d))])
        except FileNotFoundError:
            sessions = []
        for s in sessions:
            if s in seen:
                continue
            session_dir = os.path.join(RECORDINGS_DIR, s)
            events_file = os.path.join(session_dir, "events.json")
            if os.path.exists(events_file):
                analyze_one(session_dir, use_whisper=use_whisper)
                seen.add(s)
        time.sleep(poll_interval)

def interactive_record_once(use_whisper=False):
    rec = start_recording()
    print("Recording... press ENTER to stop.")
    try:
        input()
    except KeyboardInterrupt:
        print("\nInterrupted by user (Ctrl+C). Stopping recorder.")
    session_dir = stop_recording()
    if session_dir:
        analyze_one(session_dir, use_whisper=use_whisper)
    else:
        print("No session saved.")

def continuous_mode(use_whisper=False):
    # start watcher thread & keep recorder running until Ctrl+C
    stop_event = threading.Event()
    watcher = threading.Thread(target=analyzer_watcher, args=(stop_event, use_whisper), daemon=True)
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
        # give watcher a moment to finish
        time.sleep(0.5)
        print("Stopped. Last session:", sd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGI Assistant main orchestrator")
    parser.add_argument("--mode", choices=["once", "continuous"], default="once",
                        help="once: record one session and analyze it; continuous: keep recording and auto-analyze")
    parser.add_argument("--whisper", action="store_true", help="Use Whisper transcription if available (local)")
    args = parser.parse_args()

    if args.mode == "once":
        interactive_record_once(use_whisper=args.whisper)
    else:
        continuous_mode(use_whisper=args.whisper)
