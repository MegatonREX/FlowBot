# === FILE: README.md ===
# FlowBot - AI Workflow Assistant 🤖

A local-first AI assistant that records, analyzes, and automates your workflows.
Built for the Hackathon: "The AGI Assistant" - implements Observe → Understand → Act pipeline.

## 🎯 Features

- **🎙️ Workflow Recording**: Captures keyboard, mouse, screen, and audio
- **🔍 AI Analysis**: Uses Ollama LLM to understand your workflows
- **🧹 Smart Cleaning**: Removes noise and formats for LLM consumption
- **📊 Workflow Visualization**: Modern PyQt6 GUI to view and manage recordings
- **🎤 Audio Transcription**: Offline transcription with Vosk or online with Whisper
- **⚡ Automation (Coming Soon)**: Execute workflows automatically
- **🗑️ File Management**: Delete sessions and clean up storage

## 📁 Project Structure

```
├── gui.py                      # 🎨 Modern PyQt6 GUI interface
├── main.py                     # 🎯 CLI orchestrator
├── recorder.py                 # 📹 Screen/audio/input recorder
├── analyzer.py                 # 🔍 Workflow analyzer with OCR
├── clean_workflow.py           # 🧹 Workflow cleaner
├── ollama_workflow_analyzer.py # 🤖 AI analysis with Ollama
├── automator.py                # ⚡ Workflow automation
├── launch_gui.bat/sh           # 🚀 GUI launchers
├── requirements_gui.txt        # 📦 GUI dependencies
└── README.md                   # 📖 This file
```

IMPORTANT: This is an MVP/proof-of-concept. Test only on your own machine. ALWAYS run dry-run first.

---

## 🚀 Quick Start

### Option 1: Modern GUI (Recommended)

1. **Install Dependencies**
```bash
pip install -r requirements_gui.txt
```

2. **Install Ollama** (for AI analysis)
- Download from: https://ollama.ai
- Install the model: `ollama pull mistral:latest`

3. **Launch the GUI**
```bash
# Windows
launch_gui.bat

# Linux/macOS
chmod +x launch_gui.sh
./launch_gui.sh

# Or directly
python gui.py
```

### Option 2: Command Line Interface

1. **Setup Environment**
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements_gui.txt
```

2. **Install System Dependencies**
- **Tesseract OCR**: Required for text recognition
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`
  - Windows: Download from [GitHub](https://github.com/tesseract-ocr/tesseract)

- **Ollama**: Required for AI analysis
  - Download from: https://ollama.ai
  - Run: `ollama pull mistral:latest`

3. **Record and Analyze**
```bash
# Single recording session with auto-analysis
python main.py --mode once

# Continuous recording mode
python main.py --mode continuous
```

---

## 🎨 GUI Features

### Main Interface

The FlowBot GUI provides a modern, dark-themed interface with:

**Left Panel - Control Center**
- 🎙️ Recording controls (Start/Stop)
- ⚙️ Configuration options (Vosk/Whisper, auto-analysis)
- 📋 Session browser with status icons
- 🗑️ Delete sessions

**Right Panel - Tabbed Views**

1. **📋 Workflow Tab**
   - View raw and cleaned workflows
   - Analyze, clean, and run Ollama analysis
   - See detailed action steps

2. **🤖 AI Analysis Tab**
   - View Ollama-generated insights
   - See automation suggestions
   - Understand workflow intent

3. **🎤 Transcripts Tab**
   - Browse audio transcriptions
   - See what was said during recording
   - Correlate speech with actions

4. **⚡ Automation Tab** (Coming Soon)
   - Extract automation steps
   - Execute automated workflows
   - Monitor execution progress

### Session Status Icons

- 📝 = Events recorded
- 📊 = Workflow analyzed
- 🧹 = Workflow cleaned
- 🤖 = AI analysis complete

---

## 📖 Usage Guide

### Recording a Workflow

1. Click **"⏺️ Start Recording"**
2. Perform your workflow (typing, clicking, etc.)
3. Speak to describe what you're doing (optional)
4. Click **"⏹️ Stop Recording"**
5. Wait for auto-analysis to complete (if enabled)

### Viewing Results

1. Select a session from the list
2. Navigate through tabs to see:
   - Raw workflow data
   - Cleaned workflow
   - AI insights
   - Audio transcripts

### AI Analysis

The AI analysis provides:
- **Summary**: What you did in plain English
- **Transcript Insight**: What your voice revealed about intent
- **Automation**: Suggestions for automating repetitive tasks
- **Steps**: Detailed automation steps

### Managing Sessions

- **Refresh**: Update session list
- **Delete**: Remove session and all related files
  - Deletes: recordings, workflows, analyses, transcripts

---

## 🛠️ Configuration

### Transcription Options

- **Vosk (Offline)**: Fast, local transcription. Good for privacy.
- **Whisper (Online)**: Higher quality, requires internet.

### Auto-Analysis

Enable to automatically:
1. Analyze workflow after recording
2. Clean workflow JSON
3. Run Ollama AI analysis

---

## 🔧 Command Line Tools

All features are also available via command line:

```bash
# Record a workflow
python recorder.py

# Analyze a recording
python analyzer.py recordings/20251028_075237

# Clean a workflow
python clean_workflow.py workflows/workflow_20251028_075237.json

# Run AI analysis
python ollama_workflow_analyzer.py clean_workflows/cleaned_20251028_075237.json

# Full pipeline (one session)
python main.py --mode once --vosk
```

---

## 🔒 Safety & Privacy

- ✅ **100% Local**: Everything runs on your machine
- ✅ **No Cloud**: No data sent to external servers (except Ollama if configured for remote)
- ✅ **Offline First**: Works without internet (use Vosk for transcription)
- ⚠️ **Review Before Automation**: Always dry-run workflows before execution
- 🗑️ **Easy Cleanup**: Delete recordings containing sensitive data

## 🐛 Troubleshooting

### Ollama Connection Error
```bash
# Make sure Ollama is running
ollama serve

# Check if model is installed
ollama list

# Install the model
ollama pull mistral:latest
```

### Timeout Errors
- Increase timeout in `ollama_workflow_analyzer.py` (currently 300s)
- Use a smaller/faster model: `ollama pull mistral:latest`

### Recording Issues
- Ensure you have microphone permissions
- Check Tesseract is installed: `tesseract --version`
- Install missing Python packages: `pip install -r requirements_gui.txt`

### GUI Won't Start
```bash
# Install PyQt6
pip install PyQt6

# Check Python version (need 3.8+)
python --version

# Try running directly
python gui.py
```

---

## 📦 Dependencies

### Core Requirements
- Python 3.8+
- PyQt6 (GUI framework)
- pynput (keyboard/mouse capture)
- Pillow (screenshots)
- pytesseract (OCR)
- vosk (offline transcription)
- requests (Ollama communication)

### System Requirements
- Tesseract OCR binary
- Ollama (for AI analysis)

---

## 🚧 Roadmap

- [x] Workflow recording
- [x] Audio transcription
- [x] OCR and action analysis
- [x] Workflow cleaning
- [x] AI analysis with Ollama
- [x] Modern PyQt6 GUI
- [x] Session management
- [ ] Workflow automation execution
- [ ] Custom automation scripts
- [ ] Workflow templates
- [ ] Cloud sync (optional)
- [ ] Mobile companion app

---

## 📄 License

This is a hackathon MVP/proof-of-concept. Test only on your own machine.

---

## 🤝 Contributing

This project is part of "The AGI Assistant" hackathon. Contributions welcome!

---

**Built with ❤️ for local-first AI assistance**

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
