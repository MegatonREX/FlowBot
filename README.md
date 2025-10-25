# === FILE: README.md ===
# AGI Assistant MVP (Local-only)

This repository contains a local-first MVP for the Hackathon: "The AGI Assistant".
It implements the Observe -> Understand -> Act pipeline with simple Python scripts.

Folders / files included in this single-file bundle:
- recorder.py        # capture screenshots, mouse/keyboard events, audio
- analyzer.py        # OCR, basic STT (if whisper installed), create workflow JSON
- automator.py       # dry-run and replay workflow using pyautogui
- gui.py             # simple PySimpleGUI orchestration (optional)
- requirements.txt   # pip install -r requirements.txt
- README.md          # this file

IMPORTANT: This is an MVP/proof-of-concept. Test only on your own machine. ALWAYS run dry-run first.

---

# Quick setup

1. Create a virtualenv and activate it (recommended).

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

2. Install Tesseract OCR binary on your system (required for OCR):
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt install tesseract-ocr`
- Windows: download installer from https://github.com/tesseract-ocr/tesseract

3. (Optional) Install whisper or faster-whisper for local STT if you want higher-quality transcription.

4. Run `python recorder.py` to record a session. Press ENTER to stop.
5. Run `python analyzer.py` to create a workflow JSON from the most recent recording.
6. Run `python automator.py` to dry-run and (optionally) replay.
7. Optionally run `python gui.py` to use a simple GUI orchestration.

---

# Safety & Privacy
- Everything is local. No network calls by default.
- Review and delete `recordings/` if they contain sensitive data.
- The automator will synthesize input. Use dry-run and confirm before real runs.

# File: requirements.txt
# ----------------------
# Minimal Python packages (CPU-friendly)

opencv-python
pillow
numpy
pytesseract
pyautogui
pynput
sounddevice
scipy
PySimpleGUI
python-dotenv

# Optional (for better STT)
# whisper or faster-whisper (CPU/GPU)
