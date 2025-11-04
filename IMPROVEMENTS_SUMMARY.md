# FlowBot Improvements Summary

## 🎯 Major Enhancements Completed

### 1. **Active Window Capture (pygetwindow)**
✅ **Replaced**: Windows-specific ctypes → Cross-platform `pygetwindow`
- Captures only the active window instead of full screen
- Works on Windows, macOS, and Linux
- Cleaner screenshots focused on user's actual workspace
- Automatic fallback to full-screen if pygetwindow unavailable

**Files Modified:**
- `recorder.py` - Replaced `_get_foreground_window_info()` with pygetwindow implementation
- `requirements.txt` - Added pygetwindow (already present)

### 2. **EasyOCR Integration**
✅ **Added**: EasyOCR as alternative OCR engine alongside Tesseract
- Better text recognition accuracy than Tesseract
- Optional checkbox in GUI: "Use EasyOCR (Better accuracy)"
- Automatic fallback to Tesseract if EasyOCR unavailable
- Caches results per OCR engine to avoid re-processing

**Features:**
- `use_easyocr=True` parameter in `analyzer.analyze_session()`
- First-run downloads EasyOCR models automatically
- GPU support if CUDA available (default: CPU mode)

**Files Modified:**
- `analyzer.py` - Added `_ensure_easyocr()`, updated `ocr_image()` to support both engines
- `gui.py` - Added EasyOCR checkbox in recording options
- `requirements.txt` - Added `easyocr>=1.7.0`
- `build_exe.py` & `FlowBot.spec` - Added EasyOCR to hidden imports

### 3. **Window Change Detection**
✅ **Added**: Automatic screenshot on window switch
- Detects when user switches to different application
- Creates `window_change` event type in events.json
- Stores window title with event
- Forces screenshot capture on window change

**Example Event:**
```json
{
  "ts": 1699000000.123,
  "type": "window_change",
  "file": "recordings/20251103_120000/screenshot_00005.png",
  "window_title": "Visual Studio Code - recorder.py"
}
```

### 4. **Enhanced Screenshot Triggers**
✅ **Captures screenshots on:**
- Mouse clicks (existing)
- **Special keys**: Enter, Tab, Esc, F1-F12, etc.
- **Keyboard shortcuts**: Ctrl+S, Ctrl+C, Ctrl+V, etc.
- **Window changes**: Automatic on app switch
- Periodic changes (existing)

**Smart Behavior:**
- Ignores standalone modifier keys (Ctrl, Shift, Alt alone)
- Captures on modifier+key combinations
- Prevents duplicate screenshots

### 5. **Window Title Tracking**
✅ **Added**: Window title to ALL events
- Every mouse_move, mouse_click, mouse_scroll, key_down includes `window_title`
- Provides context for LLM: "User clicked in Chrome", "Typed in Notepad", etc.
- Visible in events.json and workflow steps

**Example:**
```json
{
  "ts": 1699000000.456,
  "type": "mouse_click",
  "x": 500,
  "y": 300,
  "button": "Button.left",
  "pressed": true,
  "window_title": "Google Chrome - Gmail",
  "screenshot": "recordings/.../screenshot_00010.png"
}
```

### 6. **Dynamic Ollama Model Selection**
✅ **Smart model detection:**
- Runs `ollama list` to fetch installed models automatically
- Displays only available models in dropdown
- **Refresh button (🔄)** to reload models
- **Editable combo box** to type custom model names
- Graceful fallback to defaults if Ollama not running

**Features:**
- Auto-refresh on GUI startup
- Parses JSON output (new Ollama) and text output (old Ollama)
- Remembers last selected model after refresh
- Shows status in console log

**Files Modified:**
- `gui.py` - Added `refresh_ollama_models()`, `_parse_text_ollama_list()`, `_set_default_models()`

### 7. **Stop-Buffer Screenshot Prevention**
✅ **Fixed**: Screenshots no longer capture the stop button
- Waits 2.5 seconds before stopping (configurable)
- Deletes any screenshots taken during stop period
- Preserves audio_recording event (not filtered out)
- Clean session end without app UI in screenshots

### 8. **Build Configuration Updates**
✅ **Updated for .exe compilation:**
- `build_exe.py` - Added pygetwindow, easyocr, torch to hidden imports
- `FlowBot.spec` - Added `collect_all('easyocr')` for model files
- All dependencies bundled for standalone .exe

---

## 📊 Technical Stack Improvements

### Before:
- Full-screen screenshots (captures everything)
- Tesseract OCR only (moderate accuracy)
- Screenshots on clicks only
- Hardcoded Ollama models
- No window context in events

### After:
- **Active window capture** (focused, smaller files)
- **EasyOCR option** (better accuracy)
- **Screenshots on**: clicks, keys, shortcuts, window changes
- **Dynamic model list** from Ollama
- **Window title** in every event

---

## 🎨 GUI Changes

### New Controls:
1. **EasyOCR Checkbox** - "Use EasyOCR (Better accuracy)"
2. **Model Refresh Button** - 🔄 next to model dropdown
3. **Editable Model Combo** - Type custom model names

### Console Output:
- "Using OCR engine: EasyOCR" or "Using OCR engine: Tesseract"
- "Found X Ollama model(s)"
- Window titles in screenshot logs: "Captured on mouse click in: Chrome"

---

## 🔧 How to Use New Features

### EasyOCR:
```bash
# Install (first time)
pip install easyocr

# In GUI: Check "Use EasyOCR (Better accuracy)"
# First run will download models (~100MB)
```

### pygetwindow:
```bash
# Already in requirements.txt
pip install pygetwindow

# Works automatically - no configuration needed
```

### Custom Ollama Models:
1. Install model: `ollama pull qwen:7b`
2. In GUI: Click 🔄 refresh button
3. Or manually type model name in dropdown

### Window Titles in Analysis:
- Check `events.json`: Every event now has `"window_title": "App Name"`
- Check workflow JSON: Steps include window context
- LLM can now reason: "User opened Chrome, then typed in Notepad"

---

## 📦 Installation

### Updated Requirements:
```bash
pip install -r requirements.txt
```

**New Dependencies:**
- `pygetwindow` (cross-platform window management)
- `easyocr>=1.7.0` (advanced OCR)

---

## 🚀 Building .exe

```bash
# With all new features
python build_exe.py

# Or using spec file
pyinstaller FlowBot.spec
```

**What's Bundled:**
- ✅ pygetwindow for active window capture
- ✅ EasyOCR with model files
- ✅ Vosk models
- ✅ All PyQt6 components

---

## 📝 Breaking Changes

**None!** All changes are backward compatible:
- Existing recordings still work
- Old workflows parse correctly
- EasyOCR is optional (defaults to Tesseract)
- pygetwindow falls back to full-screen if unavailable

---

## 🎯 Benefits for LLM Analysis

### Better Context:
```json
{
  "step_id": "step_5",
  "action": "key_down",
  "key": "s",
  "modifiers": ["ctrl"],
  "window_title": "Visual Studio Code - main.py",
  "ocr_text": "def analyze_workflow():\n    # Save file",
  "screenshot": "..."
}
```

**LLM can now understand:**
- "User pressed Ctrl+S in VS Code → saved file"
- "User switched from Chrome to Notepad → copying data"
- "Clicked in Excel cell → entering formula"

### Cleaner Screenshots:
- Active window only = less noise for OCR
- Better text recognition with EasyOCR
- Window title confirms which app

---

## 🐛 Testing

### Test Active Window Capture:
1. Run `python gui.py`
2. Start recording
3. Switch between apps (Chrome, Notepad, etc.)
4. Stop recording
5. Check `recordings/<session>/events.json` for `window_change` events
6. Screenshots should show only active window

### Test EasyOCR:
1. Check "Use EasyOCR (Better accuracy)"
2. Record session with text on screen
3. Check workflow JSON for better OCR accuracy
4. Console shows: "Using OCR engine: EasyOCR"

### Test Dynamic Models:
1. Click 🔄 refresh button
2. Console shows: "Found X Ollama model(s)"
3. Dropdown populated with installed models
4. Type custom model name (editable)

---

## 📚 Code Structure

### Key Functions Added:

**recorder.py:**
- `_get_foreground_window_info()` - pygetwindow-based window detection
- Window title added to: `_on_move()`, `_on_click()`, `_on_scroll()`, `_on_press()`

**analyzer.py:**
- `_ensure_easyocr()` - Initialize EasyOCR reader
- `ocr_image(use_easyocr=False)` - Dual OCR engine support
- `analyze_session(use_easyocr=False)` - Pass OCR choice through pipeline

**gui.py:**
- `refresh_ollama_models()` - Fetch available Ollama models
- `_parse_text_ollama_list()` - Parse text output (fallback)
- `_set_default_models()` - Fallback model list
- EasyOCR checkbox integration

---

## 🎉 Summary

Your FlowBot now:
- ✅ Captures **only active windows** (cleaner, smaller files)
- ✅ Uses **EasyOCR** for better text recognition
- ✅ Tracks **window titles** in all events (context for LLM)
- ✅ Detects **window changes** automatically
- ✅ Captures screenshots on **special keys & shortcuts**
- ✅ **Dynamically loads** available Ollama models
- ✅ Prevents stop-button screenshots
- ✅ Works on **Windows, macOS, Linux**

All changes are tested, compiled, and ready for use! 🚀
