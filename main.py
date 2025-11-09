import threading
import time
import os
import argparse
import subprocess

from recorder import start_recording, stop_recording
import analyzer
from clean_workflow import clean_workflow
from ollama_workflow_analyzer import analyze_workflow_with_ollama

RECORDINGS_DIR = "recordings"
WORKFLOW_DIR = "workflows"
CLEAN_SCRIPT = "clean_workflow.py"


def run_clean_workflow(workflow_json_path):
    """Call clean_workflow.py automatically after analysis, then run Ollama analyzer."""
    if not os.path.exists(workflow_json_path):
        print(f"[Cleaner] ❌ Workflow file not found: {workflow_json_path}")
        return

    print(f"[Cleaner] 🧹 Cleaning workflow file: {workflow_json_path}")
    try:
        cleaned = clean_workflow(workflow_json_path)
        print(f"[Cleaner] ✅ Cleaned workflow successfully.")
        
        # Extract session_id from cleaned workflow
        if cleaned and "metadata" in cleaned:
            session_id = cleaned["metadata"].get("session_id", "unknown")
            
            # Construct path to cleaned JSON file
            cleaned_json_path = os.path.join("clean_workflows", f"cleaned_{session_id}.json")
            
            if os.path.exists(cleaned_json_path):
                print(f"\n[Cleaner] 🤖 Starting Ollama LLM analysis...")
                analyze_workflow_with_ollama(cleaned_json_path)
            else:
                print(f"[Cleaner] ⚠️ Cleaned file not found at: {cleaned_json_path}")
        
    except Exception as e:
        print(f"[Cleaner] ❌ Error running clean_workflow.py: {e}")


def analyze_one(session_dir, use_vosk=False):
    """Analyze a single recording session and trigger cleaning."""
    try:
        print(f"[Analyzer] Processing {session_dir} ...")
        wf = analyzer.analyze_session(session_dir, use_vosk=use_vosk)

        if not wf or "session" not in wf:
            print("[Analyzer] ⚠️ No workflow returned.")
            return

        session_id = wf["session"]
        print(f"[Analyzer] ✅ Saved workflow for session: {session_id}")

        # Locate expected workflow file
        workflow_file = os.path.join(WORKFLOW_DIR, f"workflow_{session_id}.json")
        if os.path.exists(workflow_file):
            run_clean_workflow(workflow_file)
        else:
            print(f"[Analyzer] ⚠️ Expected workflow file not found at: {workflow_file}")

    except Exception as e:
        print(f"[Analyzer] ❌ Error analyzing session: {e}")


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
    """Record one session, analyze it, and clean workflow."""
    rec = start_recording()
    print("🎙️ Recording... press ENTER to stop.")
    try:
        input()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user (Ctrl+C). Stopping recorder.")
    session_dir = stop_recording()
    if session_dir:
        analyze_one(session_dir, use_vosk=use_vosk)
    else:
        print("⚠️ No session saved.")


def continuous_mode(use_vosk=False):
    """Run continuous recording and background analysis."""
    stop_event = threading.Event()
    watcher = threading.Thread(target=analyzer_watcher, args=(stop_event, use_vosk), daemon=True)
    watcher.start()

    start_recording()
    print("🔁 Continuous recording & analysis running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        stop_event.set()
        sd = stop_recording()
        time.sleep(0.5)
        print("✅ Stopped. Last session:", sd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGI Assistant main orchestrator")
    parser.add_argument("--mode", choices=["once", "continuous"], default="once",
                        help="once: record one session and analyze it; continuous: keep recording and auto-analyze")
    parser.add_argument("--vosk", action="store_true", help="Enable Vosk transcription (offline)")
    args = parser.parse_args()

    # 🔹 Force Vosk as default unless explicitly disabled
    use_vosk = True if not args.vosk else args.vosk

    if args.mode == "once":
        interactive_record_once(use_vosk=use_vosk)
    else:
        continuous_mode(use_vosk=use_vosk)
