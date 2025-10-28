"""
Test script to verify Vosk model path resolution
Run this to test if the model path works correctly in both dev and exe
"""
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(f"✅ Running in PyInstaller mode")
        print(f"   Base path: {base_path}")
    except Exception:
        base_path = os.path.abspath(".")
        print(f"✅ Running in development mode")
        print(f"   Base path: {base_path}")
    
    full_path = os.path.join(base_path, relative_path)
    return full_path

# Test the model path
model_path = "models/vosk-model-small-en-us-0.15"
actual_path = get_resource_path(model_path)

print(f"\n📁 Model Path Resolution:")
print(f"   Requested: {model_path}")
print(f"   Resolved:  {actual_path}")
print(f"   Exists:    {os.path.exists(actual_path)}")

if os.path.exists(actual_path):
    print(f"\n✅ SUCCESS! Model found at:")
    print(f"   {actual_path}")
    
    # List model contents
    print(f"\n📂 Model directory contents:")
    try:
        for item in os.listdir(actual_path):
            item_path = os.path.join(actual_path, item)
            if os.path.isdir(item_path):
                print(f"   📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                print(f"   📄 {item} ({size:,} bytes)")
    except Exception as e:
        print(f"   ❌ Error listing contents: {e}")
else:
    print(f"\n❌ ERROR! Model not found!")
    print(f"\n💡 Solutions:")
    print(f"   1. Make sure models folder exists in project directory")
    print(f"   2. When building exe, ensure --add-data=models;models is used")
    print(f"   3. Check PyInstaller spec file has: datas = [('models', 'models')]")

# Try to load Vosk
print(f"\n🔧 Testing Vosk import...")
try:
    from vosk import Model, KaldiRecognizer
    print(f"   ✅ Vosk module imported successfully")
    
    if os.path.exists(actual_path):
        print(f"\n🎯 Attempting to load model...")
        model = Model(actual_path)
        print(f"   ✅ Model loaded successfully!")
        print(f"\n🎉 Everything works! Transcription should work.")
    else:
        print(f"   ⚠️  Model path doesn't exist, cannot load")
except ImportError as e:
    print(f"   ❌ Vosk not installed: {e}")
except Exception as e:
    print(f"   ❌ Error loading model: {e}")

input("\nPress Enter to exit...")
