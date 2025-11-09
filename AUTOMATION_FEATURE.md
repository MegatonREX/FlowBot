# 🤖 Workflow Automation Feature

## Overview
FlowBot now includes a **workflow automation** feature that allows you to replay recorded workflows automatically using the `automator.py` module.

## How to Use

### 1. Record a Workflow
1. Click **"▶️ Start Recording"** in the FlowBot GUI
2. Perform your actions (clicks, typing, etc.)
3. Click **"⏹️ Stop Recording"** when done

### 2. Analyze the Workflow
1. Select the recorded session from the list
2. Click **"🔍 Analyze Workflow"** to process the recording
3. Wait for analysis to complete

### 3. Automate the Workflow
1. Select the analyzed workflow from the session list
2. Click **"▶️ Automate"** button (green button next to Refresh and Delete)
3. Review the **dry run** output in the console
4. Click **"YES"** to confirm automation
5. **Move your mouse to the top-left corner to abort** if needed

## Features

### Safety First
- **Dry Run Preview**: Shows all actions before execution
- **5-Second Countdown**: Gives you time to prepare
- **Failsafe**: Move mouse to corner to abort (PyAutoGUI safety feature)
- **Confirmation Dialog**: Requires explicit YES to proceed

### Smart Automation
- **Anchor-Based Clicking**: Uses visual templates for robust clicking
- **Fallback to Coordinates**: Uses absolute/relative positions when anchors unavailable
- **Post-Condition Waiting**: Waits for UI changes instead of blind sleeps
- **Retry Logic**: Automatically retries failed steps

### Supported Actions
- ✅ Mouse clicks (single, double, with coordinates)
- ✅ Keyboard input (typing, special keys)
- ✅ Keyboard shortcuts (Ctrl+C, Alt+Tab, etc.)
- ✅ Wait conditions (anchor appears/disappears, OCR text, window title, process)

## Requirements

### Essential Dependencies
```bash
pip install opencv-python pyautogui imagehash
```

### Optional Dependencies (for advanced features)
```bash
pip install pytesseract psutil pygetwindow
```

### What Each Package Does
- **opencv-python (cv2)**: Template matching for anchor-based clicking
- **pyautogui**: Controls mouse and keyboard
- **imagehash**: Perceptual hashing for image comparison
- **pytesseract**: OCR-based post-conditions (optional)
- **psutil**: Process detection post-conditions (optional)
- **pygetwindow**: Window title detection (optional)

## GUI Changes

### New Button: "▶️ Automate"
- **Location**: Left panel, Session controls section
- **Color**: Green (#107c10)
- **Enabled**: When a workflow has been analyzed
- **Action**: Loads workflow and starts automation

### Visual Feedback
- Progress bar shows during automation
- Console displays detailed automation steps
- Status bar updates with automation progress
- Success/error message boxes

## How It Works

### 1. Dry Run
```python
automator.dry_run(workflow)
```
Displays sequence of actions without executing them.

### 2. Replay
```python
automator.replay(workflow, speed=1.0, anchor_threshold=0.80)
```
Executes the workflow with:
- **speed**: Playback speed multiplier (1.0 = normal)
- **anchor_threshold**: Template matching confidence (0.80 = 80%)

### 3. Action Resolution
For each step:
1. Try to find anchor template on screen
2. Fall back to relative coordinates (if available)
3. Fall back to absolute coordinates
4. Execute action (click, type, keypress)
5. Wait for post-condition (if specified)
6. Retry on failure (if configured)

### 4. Post-Conditions
Intelligent waiting instead of blind sleeps:
- `anchor_appears`: Wait for template to appear
- `anchor_gone`: Wait for template to disappear
- `ocr_contains`: Wait for OCR text in region
- `window_title`: Wait for window title
- `process`: Wait for process to start

## Example Workflow

### Recording:
1. User opens browser
2. User clicks search box
3. User types "FlowBot automation"
4. User presses Enter
5. User clicks first result

### Analysis:
```json
{
  "steps": [
    {"step_id": "1", "action": "click", "anchor": "anchors/browser_icon.png"},
    {"step_id": "2", "action": "click", "anchor": "anchors/search_box.png"},
    {"step_id": "3", "action": "type", "text": "FlowBot automation"},
    {"step_id": "4", "action": "press", "key": "Key.enter"},
    {"step_id": "5", "action": "click", "anchor": "anchors/first_result.png"}
  ]
}
```

### Automation:
1. FlowBot finds browser icon on screen (template matching)
2. Clicks on it
3. Waits for search box to appear
4. Types the search query
5. Presses Enter
6. Waits for results page
7. Clicks first result

## Tips for Better Automation

### 1. Clean Workflows
- Remove unnecessary clicks (e.g., stop recording click)
- Ensure actions are sequential
- Add appropriate delays

### 2. Robust Anchors
- Use distinctive UI elements for anchors
- Avoid generic patterns (e.g., white backgrounds)
- Ensure anchors are visible in different states

### 3. Post-Conditions
- Add `post_condition` for UI changes
- Use `anchor_appears` for dialogs/windows
- Use `ocr_contains` for text verification

### 4. Testing
- Always review dry run output
- Test on similar environment first
- Start with simple workflows

## Troubleshooting

### "Missing Dependencies" Error
**Solution**: Install required packages
```bash
pip install opencv-python pyautogui imagehash
```

### "Workflow not found" Error
**Solution**: Analyze the workflow first using "🔍 Analyze Workflow" button

### "Template not found" Warning
**Cause**: Anchor image doesn't match screen
**Solutions**:
- Ensure UI hasn't changed
- Check screen resolution matches recording
- Lower `anchor_threshold` (e.g., 0.70)

### Automation Clicks Wrong Location
**Causes**:
- Screen resolution different from recording
- UI layout changed
- Anchor template not distinctive enough

**Solutions**:
- Re-record on same screen resolution
- Update anchor templates
- Use more distinctive UI elements

### Automation Too Fast/Slow
**Solution**: Adjust speed parameter
```python
automator.replay(workflow, speed=0.5)  # Half speed (slower)
automator.replay(workflow, speed=2.0)  # Double speed (faster)
```

## Safety Features

### PyAutoGUI Failsafe
- Move mouse to **top-left corner** (0,0) to abort
- Raises `pyautogui.FailSafeException`
- Enabled by default: `pyautogui.FAILSAFE = True`

### Screen Bounds Protection
- Clicks are clamped to screen dimensions
- Prevents out-of-bounds mouse movements

### Error Handling
- Exceptions are caught and logged
- Workflow continues on non-critical errors
- Failed steps logged to console

## Advanced Usage

### Manual Automation (CLI)
```bash
python automator.py
```
Choose workflow interactively, review dry run, type YES to execute.

### Programmatic Automation
```python
import automator

# Load workflow
workflow = automator.load_workflow("workflows/workflow_20251028_075237.json")

# Preview
automator.dry_run(workflow)

# Execute
automator.replay(workflow, speed=1.0, anchor_threshold=0.80)
```

### Custom Speed and Threshold
```python
# Slower, more careful
automator.replay(workflow, speed=0.5, anchor_threshold=0.85)

# Faster, less strict matching
automator.replay(workflow, speed=2.0, anchor_threshold=0.75)
```

## Future Enhancements

### Planned Features
- [ ] Visual playback with overlay
- [ ] Step-by-step debugging mode
- [ ] Edit workflow before automation
- [ ] Schedule automated workflows
- [ ] Record and replay macros
- [ ] Cross-platform support improvements
- [ ] AI-guided automation adjustments

## Technical Details

### Architecture
```
GUI (gui.py)
  ↓ user clicks "Automate"
  ↓ loads workflow JSON
  ↓ calls automator.dry_run()
  ↓ displays preview
  ↓ user confirms
  ↓ calls automator.replay()
  ↓
Automator (automator.py)
  ↓ for each step:
  ↓   1. resolve click point (anchor/coords)
  ↓   2. perform action (click/type/press)
  ↓   3. wait for post-condition
  ↓   4. retry on failure
  ↓
PyAutoGUI
  ↓ controls mouse/keyboard
  ↓ executes actions on OS
```

### Thread Safety
- Automation runs in `WorkerThread`
- GUI remains responsive
- Console logs streamed in real-time
- Can cancel via mouse failsafe

### Error Recovery
- Failed steps logged but don't stop workflow
- Post-condition timeouts logged as warnings
- Retry logic for transient failures
- Fallback delays when post-conditions unavailable

## Code Examples

### Adding Custom Post-Condition to Workflow
```json
{
  "step_id": "5",
  "action": "click",
  "anchor": "anchors/submit_button.png",
  "post_condition": {
    "type": "anchor_appears",
    "file": "anchors/success_message.png",
    "timeout": 10,
    "retries": 3
  }
}
```

### Creating Keyboard Shortcut Step
```json
{
  "step_id": "10",
  "action": "press",
  "details": {
    "key": "s",
    "modifiers": ["ctrl"]
  }
}
```

### Type Text with Delay
```json
{
  "step_id": "3",
  "action": "type",
  "text": "Hello World",
  "details": {
    "speed": 0.5
  }
}
```

## License
This feature is part of FlowBot and follows the same license.

## Contributing
Improvements welcome! Key areas:
- Better anchor matching algorithms
- More post-condition types
- Cross-platform compatibility
- Error recovery strategies

---

**Happy Automating! 🚀**
