# Build FlowBot as Windows Executable
# This script uses PyInstaller to create a standalone .exe

# First, install PyInstaller
# pip install pyinstaller

# Run this script to build the executable
# python build_exe.py

import PyInstaller.__main__
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the executable
PyInstaller.__main__.run([
    'gui.py',                           # Main script
    '--name=FlowBot',                   # Name of the executable
    '--onefile',                        # Create a single executable file
    '--windowed',                       # GUI application (no console)
    '--icon=NONE',                      # Add icon if you have one
    '--add-data=models;models',         # Include Vosk models
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=pynput',
    '--hidden-import=pynput.mouse',
    '--hidden-import=pynput.keyboard',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageGrab',
    '--hidden-import=pytesseract',
    '--hidden-import=vosk',
    '--hidden-import=sounddevice',
    '--hidden-import=scipy',
    '--hidden-import=scipy.io',
    '--hidden-import=scipy.io.wavfile',
    '--hidden-import=cv2',
    '--hidden-import=numpy',
    '--hidden-import=pyautogui',
    '--hidden-import=requests',
    '--hidden-import=pygetwindow',
    '--hidden-import=easyocr',
    '--hidden-import=torch',
    '--collect-all=PyQt6',
    '--collect-all=vosk',
    '--collect-all=sounddevice',
    '--collect-all=easyocr',
    '--noconfirm',                      # Overwrite without asking
])

print("\n" + "="*60)
print("✅ Build complete!")
print("="*60)
print("\nExecutable location: dist/FlowBot.exe")
print("\nYou can now distribute the FlowBot.exe file!")
print("\nNote: Users will need:")
print("  - Tesseract OCR installed on their system")
print("  - Ollama installed for AI analysis")
print("="*60)
