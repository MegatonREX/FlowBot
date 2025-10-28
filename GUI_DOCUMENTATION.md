# 🎨 FlowBot GUI Documentation

## Interface Overview

The FlowBot GUI is built with PyQt6 and features a modern, dark-themed interface optimized for productivity.

## Main Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🤖 FlowBot - AI Workflow Assistant                          ▭ □ ✕  │
├───────────────┬─────────────────────────────────────────────────────┤
│               │  📋 Workflow  🤖 AI Analysis  🎤 Transcripts  ⚡      │
│  🤖 FlowBot   │ ┌─────────────────────────────────────────────────┐ │
│   Control     │ │                                                 │ │
│               │ │  🔍 Analyze  🧹 Clean  🤖 Run Ollama            │ │
│ ┌───────────┐ │ ├─────────────────────────────────────────────────┤ │
│ │ Recording │ │ │                                                 │ │
│ │           │ │ │  SESSION: 20251028_075237                       │ │
│ │ Mode:     │ │ │  RECORDED: 2025-10-28 07:53:18                 │ │
│ │ [Single▼] │ │ │  TOTAL ACTIONS: 21                              │ │
│ │           │ │ │                                                 │ │
│ │ ☑ Vosk    │ │ │  Summary:                                       │ │
│ │ ☑ Auto    │ │ │  User opened Opera browser, typed               │ │
│ │ ☑ Ollama  │ │ │  'youtube.com', and navigated to YouTube.       │ │
│ │           │ │ │                                                 │ │
│ │ ┌───────┐ │ │ │  DETAILED ACTIONS:                              │ │
│ │ │ ⏺️ Rec │ │ │ │  Step 1: Typed 'o'                              │ │
│ │ └───────┘ │ │ │  Step 2: Typed 'p'                              │ │
│ │           │ │ │  ...                                            │ │
│ │ ⚪ Idle   │ │ │                                                 │ │
│ └───────────┘ │ │                                                 │ │
│               │ └─────────────────────────────────────────────────┘ │
│ ┌───────────┐ │                                                     │
│ │ Sessions  │ │                                                     │
│ │           │ │                                                     │
│ │ 20251028  │ │                                                     │
│ │ 📝📊🧹🤖  │ │                                                     │
│ │           │ │                                                     │
│ │ 20251027  │ │                                                     │
│ │ 📝📊🧹    │ │                                                     │
│ │           │ │                                                     │
│ │ 🔄 🗑️    │ │                                                     │
│ └───────────┘ │                                                     │
├───────────────┴─────────────────────────────────────────────────────┤
│ Status: Ready                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### Left Panel - Control Center (400px)

#### 1. Title Section
- Large, bold "🤖 FlowBot Control" heading
- Centered alignment
- Accent color (#0e639c)

#### 2. Recording Group
**Mode Selector**
- Dropdown: Single Session | Continuous
- Single: Record once, stop manually
- Continuous: Keep recording multiple sessions

**Transcription Options**
- ☑ Use Vosk (Offline) - Fast, private, local
- ☐ Use Whisper - Higher quality, needs internet

**Auto-Processing Options**
- ☑ Auto-analyze - Process recordings immediately
- ☑ Auto Ollama Analysis - Run AI analysis automatically

**Record Button**
- Large button (50px height)
- Red background (#c42b1c) when idle
- Text changes: "⏺️ Start" → "⏹️ Stop"
- Darkens (#d13438) when recording

**Status Indicator**
- ⚪ Idle - Ready to record
- 🔴 Recording - Currently capturing
- 🟡 Processing - Analyzing workflow

#### 3. Session List Group
**Session Browser**
- Scrollable list of all sessions
- Sorted by date (newest first)
- Session format: `20251028_075237 📝📊🧹🤖`

**Status Icons**
- 📝 = Events recorded (events.json exists)
- 📊 = Workflow analyzed (workflow_*.json exists)
- 🧹 = Workflow cleaned (cleaned_*.json exists)
- 🤖 = AI analysis complete (analysis_*.txt exists)

**Control Buttons**
- 🔄 Refresh - Reload session list
- 🗑️ Delete - Remove selected session

### Right Panel - Tabbed Views (1000px)

#### Tab 1: 📋 Workflow

**Toolbar Buttons**
- 🔍 Analyze Workflow - Process raw recording
- 🧹 Clean Workflow - Format for LLM
- 🤖 Run Ollama - Generate AI insights

**Content Area**
- Scrollable text view
- Shows workflow JSON in formatted text
- Displays both raw and cleaned workflows
- Monospace font for JSON data

#### Tab 2: 🤖 AI Analysis

**Info Banner**
- "💡 AI-generated insights about your workflow"
- Blue accent color

**Analysis Display**
- Read-only text area
- Shows Ollama LLM output:
  - Summary section
  - Transcript Insight section
  - Automation suggestions
  - Detailed steps

**Format Example:**
```
Summary:
User opened Opera browser by typing 'opera' in Windows search,
navigated to youtube.com, and confirmed navigation...

Transcript Insight:
User explicitly stated intention to "open a browser and search
for YouTube videos" which aligns with observed actions...

Automation:
Workflow can be automated using browser automation tools...

Steps:
1. Launch Opera browser
2. Navigate to youtube.com
3. Search for desired content
```

#### Tab 3: 🎤 Transcripts

**Transcript List**
- List of all transcript files
- Clickable items
- Shows filename timestamps

**Transcript Viewer**
- Read-only text area
- Shows audio transcription content
- Groups by file with headers

#### Tab 4: ⚡ Automation (Preview)

**Info Banner**
- "⚡ Execute automated workflows based on AI analysis"

**Automation Steps Display**
- Extracted from AI analysis
- Formatted as bullet points
- Editable for customization

**Control Buttons**
- 📝 Extract Steps - Parse from AI analysis
- ▶️ Execute Automation - Run the workflow
- Disabled until implementation complete

**Progress Bar**
- Hidden by default
- Shows during execution
- Indeterminate progress style

### Bottom Status Bar

- Shows current operation status
- Updates in real-time:
  - "Ready" - Idle state
  - "Recording in progress..." - Active recording
  - "Analyzing session..." - Processing
  - "Ollama analysis complete!" - Success
  - Error messages in red

## Color Scheme

### Dark Theme
- **Background**: `#1e1e1e` (Main)
- **Panels**: `#252525` (Cards)
- **Borders**: `#3a3a3a` (Dividers)
- **Text**: `#ffffff` (Primary)
- **Accent**: `#0e639c` (Blue)
- **Hover**: `#1177bb` (Light Blue)

### Action Colors
- **Primary Button**: `#0e639c` (Blue)
- **Record Button**: `#c42b1c` (Red)
- **Stop Button**: `#d13438` (Dark Red)
- **Delete Button**: `#8b0000` (Dark Red)
- **Success**: `#107c10` (Green)
- **Warning**: `#ffa500` (Orange)

## Interaction Patterns

### Recording Workflow
1. User clicks "⏺️ Start Recording"
2. Button changes to "⏹️ Stop Recording" (red)
3. Status shows "🔴 Recording..."
4. User performs actions
5. User clicks "⏹️ Stop Recording"
6. Status shows "⚪ Processing..."
7. Auto-analysis runs (if enabled)
8. Session appears in list with status icons
9. Status returns to "⚪ Idle"

### Session Selection
1. User clicks session in list
2. Session highlights (blue background)
3. All tabs populate with data
4. Action buttons enable/disable based on available data
5. Delete button enables

### AI Analysis Flow
1. User selects session with 🧹 icon
2. Clicks "🤖 Run Ollama"
3. Progress bar appears (indeterminate)
4. Status bar shows "Running Ollama analysis..."
5. Analysis streams to terminal (visible in background)
6. On completion:
   - Session gains 🤖 icon
   - AI Analysis tab populates
   - Extract Steps button enables
7. Status returns to "Ready"

## Responsive Behavior

### Window Sizing
- Minimum: 1200x700
- Recommended: 1400x900
- Splitter allows resizing panels
- Layout adapts to window size

### Panel Resizing
- Left panel: 300-600px
- Right panel: Remaining space
- Splitter draggable for user preference

## Keyboard Shortcuts (Planned)

- `Ctrl+R` - Start/Stop Recording
- `Ctrl+D` - Delete Session
- `Ctrl+A` - Analyze Workflow
- `Ctrl+O` - Run Ollama Analysis
- `F5` - Refresh Sessions
- `Ctrl+Q` - Quit Application

## Accessibility

- High contrast dark theme
- Clear icon indicators
- Status messages in status bar
- Confirmation dialogs for destructive actions
- Read-only text areas prevent accidental edits
- Tooltips on buttons (planned)

---

## Technical Details

### Framework
- **PyQt6**: Modern Python GUI framework
- **Qt Widgets**: Traditional widget-based UI
- **Qt Signals/Slots**: Event handling
- **QThread**: Background task execution

### Threading Model
- Main thread: UI updates
- Worker threads: Long-running tasks
  - Recording
  - Analysis
  - Ollama queries
- Signals: Thread-safe communication

### Data Flow
```
Recording → events.json
         → screenshots/
         → audio files
         ↓
Analyzer → workflow_*.json
         ↓
Cleaner  → cleaned_*.json
         → cleaned_*.txt
         ↓
Ollama   → analysis_*.txt
```

---

**GUI Design Philosophy**: Clean, minimal, focused on workflow - let the AI do the heavy lifting! 🚀
