# 🚀 FlowBot Quick Start Guide

## Installation (First Time Only)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements_gui.txt
```

### Step 2: Install System Dependencies

#### Tesseract OCR (Required for text recognition)
- **Windows**: Download installer from https://github.com/tesseract-ocr/tesseract
  - Add to PATH during installation
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

#### Ollama (Required for AI analysis)
- Download from: https://ollama.ai
- Install and start: `ollama serve`
- Pull the model: `ollama pull mistral:latest`

### Step 3: Verify Installation
```bash
# Check Tesseract
tesseract --version

# Check Ollama
ollama list

# Check Python packages
python -c "import PyQt6; print('PyQt6 OK')"
```

---

## 🎮 Using FlowBot GUI

### Launch the Application

**Windows:**
```bash
launch_gui.bat
```

**Linux/macOS:**
```bash
chmod +x launch_gui.sh
./launch_gui.sh
```

**Or directly:**
```bash
python gui.py
```

---

## 📝 Recording Your First Workflow

1. **Configure Settings** (Left Panel)
   - ✅ Check "Use Vosk (Offline)" for privacy
   - ✅ Check "Auto-analyze" to process automatically
   - ✅ Check "Auto Ollama Analysis" for AI insights

2. **Start Recording**
   - Click the **"⏺️ Start Recording"** button
   - Status changes to 🔴 Recording...

3. **Perform Your Workflow**
   - Do the actions you want to record (type, click, etc.)
   - Speak to describe what you're doing (optional but helpful)
   - Example: "I'm opening Chrome and searching for Python tutorials"

4. **Stop Recording**
   - Click **"⏹️ Stop Recording"**
   - Wait for automatic analysis to complete

5. **View Results**
   - Your session appears in the session list with status icons:
     - 📝 Events recorded
     - 📊 Workflow analyzed
     - 🧹 Workflow cleaned
     - 🤖 AI analysis complete

---

## 🔍 Exploring Your Workflow

### Select a Session
Click on any session in the left panel to view details.

### Navigate the Tabs

**📋 Workflow Tab**
- See all recorded actions
- View cleaned, LLM-friendly format
- Buttons:
  - 🔍 Analyze Workflow - Process raw recordings
  - 🧹 Clean Workflow - Format for AI
  - 🤖 Run Ollama - Get AI insights

**🤖 AI Analysis Tab**
- Read AI-generated summary of your workflow
- See automation suggestions
- Understand the intent behind your actions

**🎤 Transcripts Tab**
- View what you said during recording
- See correlation between speech and actions

**⚡ Automation Tab** (Coming Soon)
- Extract automation steps from AI analysis
- Execute workflows automatically

---

## 🗑️ Managing Sessions

### Delete a Session
1. Select the session in the list
2. Click **"🗑️ Delete"** button
3. Confirm deletion

This removes:
- Recording files
- Workflow JSON
- Cleaned workflow
- AI analysis
- All transcripts

### Refresh Session List
Click **"🔄 Refresh"** to update the session list.

---

## 💡 Tips for Best Results

### Recording Tips
1. **Speak clearly** when describing actions
2. **Be specific**: "Opening Chrome" vs "clicking mouse"
3. **Break into steps**: Don't rush through complex workflows
4. **Use meaningful names**: When typing, say what you're typing

### AI Analysis Tips
1. **Review transcripts**: They help AI understand intent
2. **Keep sessions focused**: One task per recording
3. **Use auto-analyze**: Let the system process immediately
4. **Wait for Ollama**: AI analysis takes 30-60 seconds

### Performance Tips
1. **Use Vosk for speed**: Offline and fast
2. **Close other apps**: Recording uses CPU
3. **Good microphone**: Better transcription = better AI analysis
4. **Check Ollama is running**: Before starting analysis

---

## 🔧 Troubleshooting

### "Ollama not available"
```bash
# Start Ollama server
ollama serve

# In another terminal, verify
ollama list
```

### "No module named 'PyQt6'"
```bash
pip install PyQt6
```

### Recording Doesn't Start
- Check microphone permissions
- Close other apps using microphone
- Restart the application

### Timeout Errors
- Normal for first-time Ollama use (downloading model)
- Increase timeout in settings (advanced)
- Use smaller model: `ollama pull mistral:latest`

### OCR Not Working
```bash
# Verify Tesseract installation
tesseract --version

# Windows: Add to PATH
# Control Panel > System > Advanced > Environment Variables
# Add: C:\Program Files\Tesseract-OCR
```

---

## 📚 Example Workflows

### Example 1: Web Search
1. Record yourself:
   - Opening browser
   - Typing "python tutorial"
   - Clicking search result
2. AI will suggest automation:
   - "Open browser"
   - "Navigate to google.com"
   - "Search for 'python tutorial'"

### Example 2: File Organization
1. Record yourself:
   - Creating folders
   - Moving files
   - Renaming documents
2. AI will identify patterns and suggest bulk operations

### Example 3: Form Filling
1. Record yourself:
   - Opening form
   - Entering data
   - Clicking submit
2. AI will extract repeatable steps for automation

---

## 🎯 Next Steps

1. ✅ Record several workflows
2. ✅ Review AI analysis
3. ✅ Build automation scripts (coming soon)
4. ✅ Share feedback and improvements

---

## 📞 Need Help?

- Check the main README.md for detailed documentation
- Review error messages in the status bar
- Check terminal output for debugging info

---

**Happy Automating! 🤖✨**
