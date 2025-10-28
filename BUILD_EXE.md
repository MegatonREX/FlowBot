# 📦 Building FlowBot as Windows Executable

## 🎯 Quick Build (Recommended)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build the Executable
```bash
python build_exe.py
```

**That's it!** Your executable will be in `dist/FlowBot.exe`

---

## 🛠️ Manual Build Options

### Option 1: Simple One-File Build
```bash
pyinstaller --onefile --windowed --name=FlowBot gui.py
```

### Option 2: Using Spec File (Recommended for Advanced Users)
```bash
pyinstaller FlowBot.spec
```

### Option 3: With All Features
```bash
pyinstaller ^
  --onefile ^
  --windowed ^
  --name=FlowBot ^
  --add-data="models;models" ^
  --hidden-import=PyQt6 ^
  --hidden-import=pynput ^
  --hidden-import=PIL ^
  --hidden-import=pytesseract ^
  --hidden-import=vosk ^
  --collect-all=PyQt6 ^
  gui.py
```

---

## 📁 Output Files

After building, you'll have:
```
dist/
  └── FlowBot.exe          # Your standalone executable!

build/                     # Temporary build files (can delete)
FlowBot.spec              # Build configuration (keep for rebuilding)
```

---

## 🚀 Distribution

### What to Distribute:
1. **FlowBot.exe** - The main executable
2. **models/** folder (optional, for offline Vosk transcription)
3. **README.md** - Usage instructions

### What Users Need to Install:
1. **Tesseract OCR** - For text recognition
   - Download: https://github.com/tesseract-ocr/tesseract
   - Must be in system PATH

2. **Ollama** (optional) - For AI analysis
   - Download: https://ollama.ai
   - Run: `ollama pull mistral:latest`

### First-time User Setup:
```bash
# 1. Install Tesseract OCR (Windows)
# Download installer from GitHub and add to PATH

# 2. Install Ollama
# Download from ollama.ai

# 3. Pull AI model
ollama serve
ollama pull mistral:latest

# 4. Run FlowBot
FlowBot.exe
```

---

## ⚙️ Build Configurations

### Console vs Windowed

**Windowed Mode** (Default - No console):
```bash
pyinstaller --windowed gui.py
```

**Console Mode** (Shows debug output):
```bash
pyinstaller --console gui.py
```

### Single File vs Directory

**Single File** (Easier to distribute):
```bash
pyinstaller --onefile gui.py
```
- Slower startup (extracts to temp)
- Easier to share
- ~50-100 MB file

**Directory** (Faster startup):
```bash
pyinstaller --onedir gui.py
```
- Faster startup
- Multiple files in folder
- Better for local use

---

## 🐛 Troubleshooting

### Transcription Not Working in .exe

**Problem:** Vosk transcription works in VSCode but not in the .exe file.

**Solution:**
1. The code now includes `get_resource_path()` function in `analyzer.py` that handles PyInstaller's temporary directory
2. Rebuild the .exe after pulling the latest code:
   ```bash
   python build_exe.py
   ```

**Test the fix:**
```bash
# In development
python test_vosk_path.py

# After building .exe, copy test_vosk_path.py to dist/ and test
cd dist
copy ..\test_vosk_path.py .
.\test_vosk_path.exe  # (if you build it separately)
```

**Why it happens:**
- PyInstaller `--onefile` extracts files to `sys._MEIPASS` temp directory
- Hardcoded paths like `models/vosk-model-small-en-us-0.15` don't work
- `get_resource_path()` detects PyInstaller and uses correct base path

### Build Fails

**Error: "Module not found"**
```bash
# Install missing module
pip install <module-name>

# Or add to hidden imports in spec file
hiddenimports=['module_name']
```

**Error: "Failed to execute script"**
```bash
# Build with console to see errors
pyinstaller --console gui.py
```

### Large File Size

**Reduce executable size:**
```bash
# Use UPX compression (included in spec file)
pip install upx-ucl

# Exclude unnecessary packages
pyinstaller --exclude-module=matplotlib gui.py
```

### Missing Dependencies

**If Vosk models are missing:**
1. Copy `models/` folder next to FlowBot.exe
2. Or rebuild with: `--add-data="models;models"`

**If Tesseract not found:**
1. User must install Tesseract separately
2. Add to PATH: `C:\Program Files\Tesseract-OCR`

---

## 📊 File Sizes

Expected executable sizes:
- **Single file**: ~80-120 MB
- **Directory**: ~100-150 MB (total)
- **With models**: +500 MB (Vosk models)

---

## 🔄 Rebuilding

To rebuild after code changes:
```bash
# Clean previous build
rmdir /s /q build dist
del FlowBot.spec

# Rebuild
python build_exe.py
```

Or keep the spec file:
```bash
pyinstaller FlowBot.spec --clean
```

---

## 📝 Adding an Icon

1. Get/create an icon file (`.ico` format)
2. Save as `icon.ico` in project folder
3. Build with icon:
```bash
pyinstaller --icon=icon.ico gui.py
```

Or update spec file:
```python
exe = EXE(
    ...
    icon='icon.ico',
)
```

---

## 🎁 Creating an Installer

For professional distribution, create an installer with **Inno Setup**:

### Install Inno Setup
Download from: https://jrsoftware.org/isinfo.php

### Create installer script (`FlowBot_Installer.iss`):
```ini
[Setup]
AppName=FlowBot
AppVersion=1.0
DefaultDirName={pf}\FlowBot
DefaultGroupName=FlowBot
OutputDir=installer
OutputBaseFilename=FlowBot_Setup

[Files]
Source: "dist\FlowBot.exe"; DestDir: "{app}"
Source: "models\*"; DestDir: "{app}\models"; Flags: recursesubdirs
Source: "README.md"; DestDir: "{app}"

[Icons]
Name: "{group}\FlowBot"; Filename: "{app}\FlowBot.exe"
Name: "{commondesktop}\FlowBot"; Filename: "{app}\FlowBot.exe"

[Run]
Filename: "{app}\FlowBot.exe"; Description: "Launch FlowBot"; Flags: postinstall nowait skipifsilent
```

Compile with Inno Setup to create `FlowBot_Setup.exe`

---

## ✅ Testing the Executable

### Before Distribution:
1. ✅ Test on clean Windows machine
2. ✅ Verify Tesseract detection
3. ✅ Test recording functionality
4. ✅ Test Ollama connection
5. ✅ Check all tabs work
6. ✅ Verify console output
7. ✅ Test file operations

### Test Checklist:
```bash
# 1. Launch FlowBot.exe
FlowBot.exe

# 2. Record a test workflow
# Click "Start Recording" → Perform actions → Stop

# 3. Verify analysis
# Check workflow, transcripts, screenshots, audio

# 4. Test Ollama
# Select model → Run analysis

# 5. Test console
# Check logs appear correctly
```

---

## 🌐 Platform Support

### Windows
✅ Fully supported
- Build: `pyinstaller gui.py`
- Output: `FlowBot.exe`

### Linux
✅ Supported (build on Linux)
```bash
pyinstaller --onefile gui.py
# Output: dist/FlowBot
```

### macOS
✅ Supported (build on macOS)
```bash
pyinstaller --onefile --windowed gui.py
# Output: dist/FlowBot.app
```

**Note:** Must build on target platform!

---

## 📦 Distribution Checklist

Before releasing:
- [ ] Build executable
- [ ] Test on clean machine
- [ ] Include README
- [ ] List system requirements
- [ ] Provide Tesseract install link
- [ ] Provide Ollama install link
- [ ] Test all features
- [ ] Check file size
- [ ] Virus scan (optional)
- [ ] Create installer (optional)

---

## 🎯 Quick Commands Reference

```bash
# Install PyInstaller
pip install pyinstaller

# Simple build
pyinstaller --onefile --windowed gui.py

# Build with spec
pyinstaller FlowBot.spec

# Clean rebuild
pyinstaller FlowBot.spec --clean

# With console (debug)
pyinstaller --console gui.py

# Test executable
dist\FlowBot.exe
```

---

## 🔒 Security Notes

### Antivirus False Positives
PyInstaller executables may trigger antivirus warnings. This is normal.

**Solutions:**
1. Submit to antivirus vendors for whitelisting
2. Code sign your executable (requires certificate)
3. Use established installer (Inno Setup reduces flags)

### Code Signing (Professional)
```bash
# Requires code signing certificate
signtool sign /f certificate.pfx /p password FlowBot.exe
```

---

## 📚 Additional Resources

- **PyInstaller Docs**: https://pyinstaller.org/
- **Inno Setup**: https://jrsoftware.org/isinfo.php
- **UPX Compression**: https://upx.github.io/
- **Windows Code Signing**: https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools

---

**Ready to build!** Just run:
```bash
python build_exe.py
```

And share `dist/FlowBot.exe` with the world! 🚀
