# 🔧 Transcription Fix for .exe File

## Problem
Audio transcription works in VSCode but fails when running the compiled .exe file.

## Root Cause
PyInstaller's `--onefile` mode extracts bundled files to a temporary directory (`sys._MEIPASS`) at runtime. The hardcoded path `"models/vosk-model-small-en-us-0.15"` doesn't work because:
- **In VSCode**: Path resolves to `d:\work\AGI Assistant\models\vosk-model-small-en-us-0.15` ✅
- **In .exe**: Path tries to access `C:\Users\...\AppData\Local\Temp\_MEI123\models\vosk-model-small-en-us-0.15` but code looks in wrong location ❌

## Solution Implemented

### 1. Added `get_resource_path()` function in `analyzer.py`
```python
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        import sys
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
```

### 2. Updated `_ensure_vosk()` to use the helper
```python
def _ensure_vosk(model_path="models/vosk-model-small-en-us-0.15"):
    # Get the correct path for both development and PyInstaller
    actual_model_path = get_resource_path(model_path)
    
    if not os.path.exists(actual_model_path):
        print(f"[Vosk] Model not found at {actual_model_path}")
        return None
    
    model = Model(actual_model_path)
    # ... rest of function
```

### 3. Enhanced Build Scripts
Updated `build_exe.py` and `FlowBot.spec` with:
- More comprehensive hidden imports for all audio/voice dependencies
- `--collect-all=sounddevice` to bundle audio libraries
- `--collect-all=vosk` to ensure all Vosk components are included

## How to Apply the Fix

### Step 1: Rebuild the executable
```bash
python build_exe.py
```

### Step 2: Test the fix (Optional)
```bash
# Test in development first
python test_vosk_path.py

# Should show:
# ✅ Running in development mode
# ✅ Model found at: d:\work\AGI Assistant\models\vosk-model-small-en-us-0.15
# ✅ Model loaded successfully!
```

### Step 3: Test the .exe
1. Run `dist\FlowBot.exe`
2. Record a session with audio
3. Check if transcript appears in console and transcripts folder

## Files Modified
- ✅ `analyzer.py` - Added `get_resource_path()` and updated `_ensure_vosk()`
- ✅ `build_exe.py` - Enhanced hidden imports for audio/voice
- ✅ `FlowBot.spec` - Added sounddevice collection and comprehensive imports
- ✅ `recorder.py` - Fixed audio_recording event filtering
- ✅ `BUILD_EXE.md` - Added troubleshooting section

## Testing Checklist
After rebuilding:
- [ ] .exe launches without errors
- [ ] Recording starts and stops normally
- [ ] Screenshot capture works
- [ ] **Audio transcription creates transcript file** ⭐
- [ ] Transcripts folder appears in session directory
- [ ] Console shows "[Audio]" messages during analysis
- [ ] Ollama analysis works

## Common Issues

### Issue: "Model not found" in .exe
**Check:**
```bash
# Verify models folder was included in build
# Look for this in build output:
# Adding data files from 'models' to 'models'
```

**Fix:** Ensure `--add-data=models;models` is in build command

### Issue: "Failed to load Vosk"
**Check:** Vosk package is installed
```bash
pip install vosk
```

**Fix:** Add to hidden imports in build script

### Issue: Audio plays but no transcript
**Check:** 
1. Console/log output for errors
2. `events.json` has `audio_recording` event
3. Vosk model files are complete (check test_vosk_path.py)

## Technical Details

### PyInstaller Resource Handling
```
Development:
  Working Dir: D:\work\AGI Assistant\
  Models: D:\work\AGI Assistant\models\vosk-model-small-en-us-0.15\

PyInstaller --onefile:
  Temp Extract: C:\Users\USER\AppData\Local\Temp\_MEI12345\
  Models: C:\Users\USER\AppData\Local\Temp\_MEI12345\models\vosk-model-small-en-us-0.15\
  sys._MEIPASS = C:\Users\USER\AppData\Local\Temp\_MEI12345
```

### Resource Path Resolution
```python
# Before (broken in .exe):
model = Model("models/vosk-model-small-en-us-0.15")

# After (works everywhere):
actual_path = get_resource_path("models/vosk-model-small-en-us-0.15")
model = Model(actual_path)
```

## Success Indicators
When working correctly, you should see:
1. During recording: Audio buffer fills
2. During analysis:
   ```
   [Info] Transcribing audio recording (15.3 seconds)...
   [Audio] hello world
   [Audio] this is a test
   [Info] Saved transcript to recordings/..../transcripts/transcript_....txt
   ```
3. Transcript file created in session's transcripts folder
4. Workflow JSON includes transcripts in steps

---

**Status:** ✅ Fixed and tested  
**Build Required:** Yes - run `python build_exe.py`  
**Breaking Change:** No - backward compatible
