"""
FlowBot Setup Checker
Verifies that all dependencies and requirements are met before launching the GUI.
"""

import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_module(module_name, package_name=None):
    """Check if a Python module is installed"""
    package_name = package_name or module_name
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"❌ {package_name} not installed")
        return False
    print(f"✅ {package_name}")
    return True

def check_command(command, name):
    """Check if a system command is available"""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ {name}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print(f"❌ {name} not found")
    return False

def check_ollama():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            if "mistral:latest" in model_names or "llama3:8b" in model_names:
                print("✅ Ollama running with models")
                return True
            else:
                print("⚠️  Ollama running but no models found")
                print("   Run: ollama pull mistral:latest")
                return False
    except:
        pass
    print("❌ Ollama not running")
    print("   Start with: ollama serve")
    return False

def main():
    print("\n" + "="*60)
    print("  FlowBot Setup Checker")
    print("="*60 + "\n")
    
    all_good = True
    
    # Check Python version
    print("Checking Python...")
    if not check_python_version():
        all_good = False
    print()
    
    # Check required Python packages
    print("Checking Python packages...")
    required_packages = [
        ("PyQt6", "PyQt6"),
        ("PIL", "Pillow"),
        ("pynput", "pynput"),
        ("pytesseract", "pytesseract"),
        ("vosk", "vosk"),
        ("pyautogui", "pyautogui"),
        ("requests", "requests"),
    ]
    
    for module, package in required_packages:
        if not check_module(module, package):
            all_good = False
    print()
    
    # Check system dependencies
    print("Checking system dependencies...")
    if not check_command("tesseract", "Tesseract OCR"):
        all_good = False
        print("   Install from: https://github.com/tesseract-ocr/tesseract")
    print()
    
    # Check Ollama
    print("Checking Ollama...")
    ollama_ok = check_ollama()
    print()
    
    # Summary
    print("="*60)
    if all_good:
        print("✅ All required dependencies are installed!")
        if not ollama_ok:
            print("⚠️  Ollama not ready (optional for AI analysis)")
        print("\nYou can now run: python gui.py")
    else:
        print("❌ Some dependencies are missing")
        print("\nTo install Python packages:")
        print("   pip install -r requirements_gui.txt")
        print("\nTo install system dependencies:")
        print("   - Tesseract: https://github.com/tesseract-ocr/tesseract")
        print("   - Ollama: https://ollama.ai")
    print("="*60 + "\n")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    sys.exit(main())
