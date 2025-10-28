"""
FlowBot - Modern GUI for AGI Assistant Workflow Recorder
A PyQt6 interface for recording, analyzing, and automating workflows.
"""

import sys
import os
import json
import threading
from datetime import datetime
from pathlib import Path
from io import StringIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QListWidget, QTabWidget,
    QGroupBox, QMessageBox, QFileDialog, QSplitter, QStatusBar,
    QComboBox, QCheckBox, QProgressBar, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QObject
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QTextCursor

from recorder import start_recording, stop_recording
import analyzer
from clean_workflow import clean_workflow
from ollama_workflow_analyzer import analyze_workflow_with_ollama


class ConsoleStream(QObject):
    """Custom stream to capture stdout/stderr and emit signals"""
    text_written = pyqtSignal(str)
    
    def __init__(self, original_stream=None):
        super().__init__()
        self.original_stream = original_stream
        
    def write(self, text):
        if text and text.strip():  # Only emit non-empty text
            self.text_written.emit(text)
        if self.original_stream:
            self.original_stream.write(text)
            
    def flush(self):
        if self.original_stream:
            self.original_stream.flush()


class WorkerThread(QThread):
    """Worker thread for background tasks"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    log_message = pyqtSignal(str)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.log_message.emit(f"[Worker] Starting task: {self.task_func.__name__}")
            result = self.task_func(*self.args, **self.kwargs)
            self.log_message.emit(f"[Worker] Task completed: {self.task_func.__name__}")
            self.finished.emit(True, str(result) if result else "Success")
        except Exception as e:
            self.log_message.emit(f"[Worker] Task failed: {str(e)}")
            self.finished.emit(False, str(e))


class FlowBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.current_session_dir = None
        self.worker_thread = None
        
        # Setup console output redirection
        self.setup_console_redirect()
        
        self.init_ui()
        self.load_sessions()
        
        # Log startup
        self.log("FlowBot GUI initialized successfully")
        
    def setup_console_redirect(self):
        """Redirect stdout and stderr to capture console output"""
        self.console_stream = ConsoleStream(sys.stdout)
        self.error_stream = ConsoleStream(sys.stderr)
        
        # Don't actually redirect yet - will connect to console widget later
        # This allows us to capture output when needed
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("FlowBot - AI Workflow Assistant")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply modern dark theme
        self.apply_dark_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Controls and Sessions
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Tabs for different views
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial sizes
        splitter.setSizes([400, 1000])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def apply_dark_theme(self):
        """Apply modern dark theme"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #1e1e1e;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', Arial;
            font-size: 10pt;
        }
        QPushButton {
            background-color: #0e639c;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1177bb;
        }
        QPushButton:pressed {
            background-color: #0d5a8f;
        }
        QPushButton:disabled {
            background-color: #3a3a3a;
            color: #888888;
        }
        QPushButton#recordButton {
            background-color: #c42b1c;
            font-size: 12pt;
        }
        QPushButton#recordButton:hover {
            background-color: #e03e2d;
        }
        QPushButton#stopButton {
            background-color: #d13438;
        }
        QPushButton#deleteButton {
            background-color: #8b0000;
        }
        QListWidget {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            padding: 5px;
        }
        QListWidget::item {
            padding: 8px;
            border-radius: 3px;
        }
        QListWidget::item:selected {
            background-color: #0e639c;
        }
        QListWidget::item:hover {
            background-color: #2a2a2a;
        }
        QTextEdit {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            padding: 10px;
            color: #ffffff;
        }
        QGroupBox {
            border: 2px solid #3a3a3a;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            color: #0e639c;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QTabWidget::pane {
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            background-color: #252525;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            border: 1px solid #3a3a3a;
            padding: 10px 20px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #0e639c;
            border-bottom: 2px solid #1177bb;
        }
        QTabBar::tab:hover {
            background-color: #3a3a3a;
        }
        QComboBox {
            background-color: #252525;
            border: 1px solid #3a3a3a;
            border-radius: 3px;
            padding: 5px;
        }
        QComboBox:hover {
            border: 1px solid #0e639c;
        }
        QCheckBox {
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #3a3a3a;
            border-radius: 3px;
            background-color: #252525;
        }
        QCheckBox::indicator:checked {
            background-color: #0e639c;
            border-color: #0e639c;
        }
        QProgressBar {
            border: 1px solid #3a3a3a;
            border-radius: 5px;
            text-align: center;
            background-color: #252525;
        }
        QProgressBar::chunk {
            background-color: #0e639c;
            border-radius: 3px;
        }
        QStatusBar {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        """
        self.setStyleSheet(dark_stylesheet)
        
    def create_left_panel(self):
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("🤖 FlowBot Control")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Recording controls
        recording_group = QGroupBox("Recording")
        recording_layout = QVBoxLayout()
        
        # Mode selection
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Single Session", "Continuous"])
        mode_layout.addWidget(self.mode_combo)
        recording_layout.addLayout(mode_layout)
        
        # Ollama model selection
        ollama_layout = QHBoxLayout()
        ollama_layout.addWidget(QLabel("AI Model:"))
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.addItems(["mistral:latest", "llama3:8b", "llama2:latest", "codellama:latest"])
        self.ollama_model_combo.setToolTip("Select Ollama model for AI analysis")
        ollama_layout.addWidget(self.ollama_model_combo)
        recording_layout.addLayout(ollama_layout)
        
        # Transcription options
        self.vosk_checkbox = QCheckBox("Use Vosk (Offline)")
        self.vosk_checkbox.setChecked(True)
        recording_layout.addWidget(self.vosk_checkbox)
        
        self.auto_analyze_checkbox = QCheckBox("Auto-analyze")
        self.auto_analyze_checkbox.setChecked(True)
        recording_layout.addWidget(self.auto_analyze_checkbox)
        
        self.ollama_checkbox = QCheckBox("Auto Ollama Analysis")
        self.ollama_checkbox.setChecked(True)
        recording_layout.addWidget(self.ollama_checkbox)
        
        # Countdown option
        self.countdown_checkbox = QCheckBox("3-2-1 Countdown")
        self.countdown_checkbox.setChecked(True)
        self.countdown_checkbox.setToolTip("Show countdown before recording starts")
        recording_layout.addWidget(self.countdown_checkbox)
        
        # Record button
        self.record_button = QPushButton("⏺️ Start Recording")
        self.record_button.setObjectName("recordButton")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setMinimumHeight(50)
        recording_layout.addWidget(self.record_button)
        
        # Countdown label (hidden by default)
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 48pt; font-weight: bold; color: #ff4444; padding: 20px;")
        self.countdown_label.setVisible(False)
        recording_layout.addWidget(self.countdown_label)
        
        # Status indicator
        self.recording_status = QLabel("⚪ Idle")
        self.recording_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_status.setStyleSheet("font-size: 12pt; padding: 10px;")
        recording_layout.addWidget(self.recording_status)
        
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        # Session list
        session_group = QGroupBox("Recorded Sessions")
        session_layout = QVBoxLayout()
        
        self.session_list = QListWidget()
        self.session_list.itemClicked.connect(self.on_session_selected)
        session_layout.addWidget(self.session_list)
        
        # Session controls
        session_btn_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.load_sessions)
        session_btn_layout.addWidget(self.refresh_button)
        
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.delete_session)
        self.delete_button.setEnabled(False)
        session_btn_layout.addWidget(self.delete_button)
        
        session_layout.addLayout(session_btn_layout)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        layout.addStretch()
        return panel
        
    def create_right_panel(self):
        """Create right panel with tabs"""
        self.tabs = QTabWidget()
        
        # Tab 1: Workflow Viewer
        self.workflow_tab = self.create_workflow_tab()
        self.tabs.addTab(self.workflow_tab, "📋 Workflow")
        
        # Tab 2: Analysis Results
        self.analysis_tab = self.create_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "🤖 AI Analysis")
        
        # Tab 3: Transcripts
        self.transcript_tab = self.create_transcript_tab()
        self.tabs.addTab(self.transcript_tab, "🎤 Transcripts")
        
        # Tab 4: Screenshots
        self.screenshots_tab = self.create_screenshots_tab()
        self.tabs.addTab(self.screenshots_tab, "📸 Screenshots")
        
        # Tab 5: Audio
        self.audio_tab = self.create_audio_tab()
        self.tabs.addTab(self.audio_tab, "🔊 Audio")
        
        # Tab 6: Automation
        self.automation_tab = self.create_automation_tab()
        self.tabs.addTab(self.automation_tab, "⚡ Automation")
        
        # Tab 7: Console/Logs
        self.console_tab = self.create_console_tab()
        self.tabs.addTab(self.console_tab, "📟 Console")
        
        return self.tabs
        self.automation_tab = self.create_automation_tab()
        self.tabs.addTab(self.automation_tab, "⚡ Automation")
        
        # Tab 5: Console/Logs
        self.console_tab = self.create_console_tab()
        self.tabs.addTab(self.console_tab, "📟 Console")
        
        return self.tabs
        
    def create_workflow_tab(self):
        """Create workflow display tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.analyze_button = QPushButton("🔍 Analyze Workflow")
        self.analyze_button.clicked.connect(self.analyze_selected_session)
        self.analyze_button.setEnabled(False)
        toolbar.addWidget(self.analyze_button)
        
        self.clean_button = QPushButton("🧹 Clean Workflow")
        self.clean_button.clicked.connect(self.clean_selected_workflow)
        self.clean_button.setEnabled(False)
        toolbar.addWidget(self.clean_button)
        
        self.ollama_button = QPushButton("🤖 Run Ollama")
        self.ollama_button.clicked.connect(self.run_ollama_analysis)
        self.ollama_button.setEnabled(False)
        toolbar.addWidget(self.ollama_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Workflow content
        self.workflow_text = QTextEdit()
        self.workflow_text.setReadOnly(True)
        self.workflow_text.setPlaceholderText("Select a session to view workflow details...")
        layout.addWidget(self.workflow_text)
        
        return tab
        
    def create_analysis_tab(self):
        """Create AI analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel("💡 AI-generated insights about your workflow")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        # Analysis content
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("No AI analysis available. Run Ollama analysis on a cleaned workflow...")
        layout.addWidget(self.analysis_text)
        
        return tab
        
    def create_transcript_tab(self):
        """Create transcript viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Transcript list
        info = QLabel("🎤 Audio transcriptions from recording session")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        self.transcript_list = QListWidget()
        layout.addWidget(self.transcript_list)
        
        # Transcript content
        self.transcript_text = QTextEdit()
        self.transcript_text.setReadOnly(True)
        self.transcript_text.setPlaceholderText("Select a session to view transcripts...")
        layout.addWidget(self.transcript_text)
        
        return tab
        
    def create_screenshots_tab(self):
        """Create screenshot viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel("📸 View captured screenshots from recording session")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        # Create splitter for list and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Screenshot list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Screenshots:")
        list_layout.addWidget(list_label)
        
        self.screenshot_list = QListWidget()
        self.screenshot_list.itemClicked.connect(self.on_screenshot_selected)
        list_layout.addWidget(self.screenshot_list)
        
        splitter.addWidget(list_widget)
        
        # Screenshot preview
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Preview:")
        preview_layout.addWidget(preview_label)
        
        self.screenshot_preview = QLabel()
        self.screenshot_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_preview.setStyleSheet("border: 1px solid #3a3a3a; background-color: #252525; padding: 10px;")
        self.screenshot_preview.setText("Select a screenshot to preview")
        self.screenshot_preview.setScaledContents(False)
        preview_layout.addWidget(self.screenshot_preview)
        
        # Screenshot info
        self.screenshot_info = QLabel("")
        self.screenshot_info.setStyleSheet("padding: 5px; color: #888888;")
        preview_layout.addWidget(self.screenshot_info)
        
        splitter.addWidget(preview_widget)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
        return tab
        
    def create_audio_tab(self):
        """Create audio playback tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel("🔊 Listen to recorded audio from session")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        # Audio file list
        audio_list_label = QLabel("Audio Files:")
        layout.addWidget(audio_list_label)
        
        self.audio_file_list = QListWidget()
        self.audio_file_list.itemClicked.connect(self.on_audio_selected)
        layout.addWidget(self.audio_file_list)
        
        # Audio controls
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QVBoxLayout()
        
        # File info
        self.audio_info_label = QLabel("No audio file selected")
        self.audio_info_label.setStyleSheet("padding: 10px; color: #888888;")
        controls_layout.addWidget(self.audio_info_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.play_audio_button = QPushButton("▶️ Play")
        self.play_audio_button.clicked.connect(self.play_audio)
        self.play_audio_button.setEnabled(False)
        button_layout.addWidget(self.play_audio_button)
        
        self.stop_audio_button = QPushButton("⏹️ Stop")
        self.stop_audio_button.clicked.connect(self.stop_audio)
        self.stop_audio_button.setEnabled(False)
        button_layout.addWidget(self.stop_audio_button)
        
        self.open_audio_button = QPushButton("📂 Open in Player")
        self.open_audio_button.clicked.connect(self.open_audio_external)
        self.open_audio_button.setEnabled(False)
        button_layout.addWidget(self.open_audio_button)
        
        button_layout.addStretch()
        controls_layout.addLayout(button_layout)
        
        # Status
        self.audio_status_label = QLabel("Ready")
        self.audio_status_label.setStyleSheet("padding: 10px;")
        controls_layout.addWidget(self.audio_status_label)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        layout.addStretch()
        
        # Store current audio file
        self.current_audio_file = None
        
        return tab
        
    def create_automation_tab(self):
        """Create automation execution tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info = QLabel("⚡ Execute automated workflows based on AI analysis")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        # Automation steps
        steps_group = QGroupBox("Automation Steps")
        steps_layout = QVBoxLayout()
        
        self.automation_steps = QTextEdit()
        self.automation_steps.setReadOnly(True)
        self.automation_steps.setPlaceholderText("Automation steps will appear here after AI analysis...")
        steps_layout.addWidget(self.automation_steps)
        
        steps_group.setLayout(steps_layout)
        layout.addWidget(steps_group)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.extract_steps_button = QPushButton("📝 Extract Steps from Analysis")
        self.extract_steps_button.clicked.connect(self.extract_automation_steps)
        self.extract_steps_button.setEnabled(False)
        btn_layout.addWidget(self.extract_steps_button)
        
        self.execute_button = QPushButton("▶️ Execute Automation")
        self.execute_button.clicked.connect(self.execute_automation)
        self.execute_button.setEnabled(False)
        btn_layout.addWidget(self.execute_button)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return tab
        
    def create_console_tab(self):
        """Create console/log viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info = QLabel("📟 Real-time process logs and console output")
        info.setStyleSheet("color: #0e639c; padding: 10px; font-size: 11pt;")
        layout.addWidget(info)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        toolbar.addWidget(self.auto_scroll_checkbox)
        
        self.clear_console_button = QPushButton("🗑️ Clear Console")
        self.clear_console_button.clicked.connect(self.clear_console)
        toolbar.addWidget(self.clear_console_button)
        
        self.save_log_button = QPushButton("💾 Save Log")
        self.save_log_button.clicked.connect(self.save_console_log)
        toolbar.addWidget(self.save_log_button)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 9))
        self.console_output.setPlaceholderText("Console output will appear here...\n\nAll background processes and operations will be logged in real-time.")
        
        # Set console-specific styling
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        
        layout.addWidget(self.console_output)
        
        # Connect console streams
        self.console_stream.text_written.connect(self.append_console_output)
        self.error_stream.text_written.connect(self.append_console_error)
        
        # Redirect stdout/stderr
        sys.stdout = self.console_stream
        sys.stderr = self.error_stream
        
        return tab
        
    def log(self, message, level="INFO"):
        """Log a message to the console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}"
        self.append_console_output(formatted + "\n")
        
    def append_console_output(self, text):
        """Append text to console output"""
        self.console_output.insertPlainText(text)
        if self.auto_scroll_checkbox.isChecked():
            self.console_output.moveCursor(QTextCursor.MoveOperation.End)
            
    def append_console_error(self, text):
        """Append error text to console output in red"""
        # Insert with red color
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Store original format
        original_format = cursor.charFormat()
        
        # Set red color for errors
        error_format = cursor.charFormat()
        error_format.setForeground(QColor("#ff4444"))
        
        cursor.setCharFormat(error_format)
        cursor.insertText(text)
        cursor.setCharFormat(original_format)
        
        if self.auto_scroll_checkbox.isChecked():
            self.console_output.moveCursor(QTextCursor.MoveOperation.End)
            
    def clear_console(self):
        """Clear the console output"""
        self.console_output.clear()
        self.log("Console cleared", "INFO")
        
    def save_console_log(self):
        """Save console log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"console_log_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.console_output.toPlainText())
            self.log(f"Console log saved to: {filename}", "SUCCESS")
            QMessageBox.information(self, "Save Log", f"Console log saved to:\n{filename}")
        except Exception as e:
            self.log(f"Failed to save log: {e}", "ERROR")
            QMessageBox.critical(self, "Save Error", f"Failed to save log:\n{str(e)}")
        
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording_session()
            
    def start_recording(self):
        """Start recording session with optional countdown"""
        if self.countdown_checkbox.isChecked():
            self.start_countdown()
        else:
            self.actually_start_recording()
            
    def start_countdown(self):
        """Show 3-2-1 countdown before recording"""
        self.log("Starting 3-2-1 countdown...", "INFO")
        self.countdown_value = 3
        self.record_button.setEnabled(False)
        self.countdown_label.setVisible(True)
        
        # Create timer for countdown
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 1 second intervals
        
        # Show initial countdown
        self.update_countdown()
        
    def update_countdown(self):
        """Update countdown display"""
        if self.countdown_value > 0:
            self.countdown_label.setText(str(self.countdown_value))
            self.recording_status.setText(f"⏱️ Starting in {self.countdown_value}...")
            self.log(f"Countdown: {self.countdown_value}", "INFO")
            self.countdown_value -= 1
        else:
            # Countdown finished, start recording
            self.countdown_timer.stop()
            self.countdown_label.setVisible(False)
            self.countdown_label.setText("")
            self.record_button.setEnabled(True)
            self.log("Countdown complete - Recording NOW!", "SUCCESS")
            self.actually_start_recording()
            
    def actually_start_recording(self):
        """Actually start the recording (after countdown or immediately)"""
        try:
            self.log("Starting recording session...", "INFO")
            self.recording = True
            self.record_button.setText("⏹️ Stop Recording")
            self.record_button.setObjectName("stopButton")
            self.record_button.setStyle(self.record_button.style())  # Refresh style
            self.recording_status.setText("🔴 Recording...")
            self.status_bar.showMessage("Recording in progress...")
            
            # Start recording with 2.5s buffer to avoid capturing stop button
            self.log("Initializing recorder...", "INFO")
            start_recording(stop_screenshot_buffer=2.5)
            self.log("Recording started successfully", "SUCCESS")
            
            # Update UI
            self.mode_combo.setEnabled(False)
            self.vosk_checkbox.setEnabled(False)
            self.countdown_checkbox.setEnabled(False)
            
        except Exception as e:
            self.log(f"Recording failed: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Recording Error", f"Failed to start recording:\n{str(e)}")
            self.recording = False
            
    def stop_recording_session(self):
        """Stop recording session"""
        try:
            self.log("Stopping recording session...", "INFO")
            self.recording = False
            self.record_button.setText("⏺️ Start Recording")
            self.record_button.setObjectName("recordButton")
            self.record_button.setStyle(self.record_button.style())  # Refresh style
            self.recording_status.setText("⚪ Processing...")
            self.status_bar.showMessage("Stopping recording...")
            
            # Stop recording
            self.log("Saving recorded data...", "INFO")
            session_dir = stop_recording()
            self.current_session_dir = session_dir
            
            # Re-enable controls
            self.mode_combo.setEnabled(True)
            self.vosk_checkbox.setEnabled(True)
            self.countdown_checkbox.setEnabled(True)
            
            if session_dir:
                self.log(f"Recording saved to: {session_dir}", "SUCCESS")
                self.status_bar.showMessage(f"Recording saved: {session_dir}")
                self.recording_status.setText("⚪ Idle")
                
                # Auto-analyze if enabled
                if self.auto_analyze_checkbox.isChecked():
                    self.log("Auto-analysis enabled, starting analysis...", "INFO")
                    self.analyze_session_dir(session_dir)
                else:
                    self.load_sessions()
            else:
                self.log("Recording failed: No session was saved", "ERROR")
                self.recording_status.setText("⚠️ Failed")
                QMessageBox.warning(self, "Recording", "No session was saved.")
                
        except Exception as e:
            self.log(f"Stop recording error: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Recording Error", f"Failed to stop recording:\n{str(e)}")
            self.recording_status.setText("⚪ Idle")
            
    def load_sessions(self):
        """Load and display recorded sessions"""
        self.session_list.clear()
        
        recordings_dir = Path("recordings")
        if not recordings_dir.exists():
            return
            
        sessions = sorted(
            [d for d in recordings_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for session in sessions:
            session_id = session.name
            
            # Check what files exist
            has_events = (session / "events.json").exists()
            has_workflow = (Path("workflows") / f"workflow_{session_id}.json").exists()
            has_cleaned = (Path("clean_workflows") / f"cleaned_{session_id}.json").exists()
            has_analysis = (Path("clean_workflows/analysis") / f"analysis_cleaned_{session_id}.txt").exists()
            
            # Status icons
            status = []
            if has_events:
                status.append("📝")
            if has_workflow:
                status.append("📊")
            if has_cleaned:
                status.append("🧹")
            if has_analysis:
                status.append("🤖")
                
            item_text = f"{session_id} {' '.join(status)}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, session_id)
            self.session_list.addItem(item)
            
    def on_session_selected(self, item):
        """Handle session selection"""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        self.load_session_details(session_id)
        
        # Enable buttons
        self.delete_button.setEnabled(True)
        
        # Check what exists to enable appropriate buttons
        workflow_path = Path("workflows") / f"workflow_{session_id}.json"
        cleaned_path = Path("clean_workflows") / f"cleaned_{session_id}.json"
        
        self.analyze_button.setEnabled(True)
        self.clean_button.setEnabled(workflow_path.exists())
        self.ollama_button.setEnabled(cleaned_path.exists())
        
    def load_session_details(self, session_id):
        """Load and display session details"""
        # Load workflow
        workflow_path = Path("workflows") / f"workflow_{session_id}.json"
        if workflow_path.exists():
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
                self.display_workflow(workflow)
        else:
            self.workflow_text.setText("Workflow not yet analyzed. Click 'Analyze Workflow' to process.")
            
        # Load cleaned workflow
        cleaned_path = Path("clean_workflows") / f"cleaned_{session_id}.json"
        if cleaned_path.exists():
            with open(cleaned_path, 'r', encoding='utf-8') as f:
                cleaned = json.load(f)
                # Display in workflow tab with better formatting
                self.display_cleaned_workflow(cleaned)
                
        # Load AI analysis
        analysis_path = Path("clean_workflows/analysis") / f"analysis_cleaned_{session_id}.txt"
        if analysis_path.exists():
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis = f.read()
                self.analysis_text.setText(analysis)
                self.extract_steps_button.setEnabled(True)
        else:
            self.analysis_text.setText("No AI analysis available. Run Ollama analysis on this workflow.")
            self.extract_steps_button.setEnabled(False)
            
        # Load transcripts
        self.load_transcripts(session_id)
        
        # Load screenshots
        self.load_screenshots(session_id)
        
        # Load audio files
        self.load_audio_files(session_id)
        
    def display_workflow(self, workflow):
        """Display workflow in formatted text"""
        text = f"Session: {workflow.get('session', 'Unknown')}\n"
        text += f"Generated: {workflow.get('generated_at', 'Unknown')}\n"
        text += f"Summary: {workflow.get('summary', 'No summary')}\n"
        text += "=" * 80 + "\n\n"
        
        steps = workflow.get('steps', [])
        text += f"Total Steps: {len(steps)}\n\n"
        
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'unknown')
            details = step.get('details', {})
            text += f"Step {i}: {action}\n"
            text += f"  Details: {json.dumps(details, indent=4)}\n\n"
            
        self.workflow_text.setText(text)
        
    def display_cleaned_workflow(self, cleaned):
        """Display cleaned workflow in formatted text"""
        metadata = cleaned.get('metadata', {})
        summary = cleaned.get('workflow_summary', '')
        actions = cleaned.get('actions', [])
        
        text = f"📊 CLEANED WORKFLOW\n"
        text += "=" * 80 + "\n\n"
        text += f"Session: {metadata.get('session_id', 'Unknown')}\n"
        text += f"Recorded: {metadata.get('recorded_at', 'Unknown')}\n"
        text += f"Total Actions: {metadata.get('total_steps', 0)}\n\n"
        text += f"Summary:\n{summary}\n\n"
        text += "=" * 80 + "\n"
        text += "DETAILED ACTIONS:\n"
        text += "=" * 80 + "\n\n"
        
        for action in actions:
            step = action.get('step', '')
            desc = action.get('description', '')
            action_type = action.get('action_type', '')
            transcripts = action.get('transcripts', [])
            
            text += f"Step {step}: {desc}\n"
            text += f"  Type: {action_type}\n"
            if transcripts:
                text += f"  🎤 Transcript: {' | '.join(transcripts)}\n"
            text += "\n"
            
        self.workflow_text.setText(text)
        
    def load_transcripts(self, session_id):
        """Load and display transcripts"""
        self.transcript_list.clear()
        self.transcript_text.clear()
        
        transcript_dir = Path("recordings") / session_id / "transcripts"
        if not transcript_dir.exists():
            self.transcript_text.setText("No transcripts available for this session.")
            return
            
        transcripts = sorted(transcript_dir.glob("*.txt"))
        all_text = []
        
        for transcript_file in transcripts:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.transcript_list.addItem(transcript_file.name)
                all_text.append(f"=== {transcript_file.name} ===\n{content}\n")
                
        self.transcript_text.setText("\n".join(all_text))
        
    def load_screenshots(self, session_id):
        """Load and display screenshots"""
        self.screenshot_list.clear()
        self.screenshot_preview.clear()
        self.screenshot_preview.setText("Select a screenshot to preview")
        self.screenshot_info.setText("")
        
        screenshot_dir = Path("recordings") / session_id
        if not screenshot_dir.exists():
            return
            
        screenshots = sorted(screenshot_dir.glob("screenshot_*.png"))
        
        if not screenshots:
            self.screenshot_info.setText("No screenshots available for this session.")
            return
            
        for screenshot_file in screenshots:
            item = QListWidgetItem(screenshot_file.name)
            item.setData(Qt.ItemDataRole.UserRole, str(screenshot_file))
            self.screenshot_list.addItem(item)
            
        self.log(f"Loaded {len(screenshots)} screenshots", "INFO")
        
    def on_screenshot_selected(self, item):
        """Handle screenshot selection and display preview"""
        from PyQt6.QtGui import QPixmap
        
        screenshot_path = item.data(Qt.ItemDataRole.UserRole)
        
        try:
            pixmap = QPixmap(screenshot_path)
            
            if not pixmap.isNull():
                # Scale to fit preview area while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.screenshot_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.screenshot_preview.setPixmap(scaled_pixmap)
                
                # Show file info
                file_size = Path(screenshot_path).stat().st_size / 1024  # KB
                file_info = f"File: {Path(screenshot_path).name} | Size: {file_size:.1f} KB | Resolution: {pixmap.width()}x{pixmap.height()}"
                self.screenshot_info.setText(file_info)
                
                self.log(f"Displaying screenshot: {Path(screenshot_path).name}", "INFO")
            else:
                self.screenshot_preview.setText("Failed to load image")
                self.log(f"Failed to load screenshot: {screenshot_path}", "ERROR")
                
        except Exception as e:
            self.screenshot_preview.setText(f"Error loading image: {str(e)}")
            self.log(f"Error loading screenshot: {str(e)}", "ERROR")
            
    def load_audio_files(self, session_id):
        """Load audio files for the session"""
        self.audio_file_list.clear()
        self.audio_info_label.setText("No audio file selected")
        self.play_audio_button.setEnabled(False)
        self.stop_audio_button.setEnabled(False)
        self.open_audio_button.setEnabled(False)
        self.current_audio_file = None
        
        session_dir = Path("recordings") / session_id
        if not session_dir.exists():
            return
            
        # Look for audio files (wav, mp3, etc.)
        audio_files = list(session_dir.glob("*.wav")) + list(session_dir.glob("*.mp3"))
        
        if not audio_files:
            self.audio_info_label.setText("No audio files available for this session.")
            return
            
        for audio_file in sorted(audio_files):
            item = QListWidgetItem(f"🎵 {audio_file.name}")
            item.setData(Qt.ItemDataRole.UserRole, str(audio_file))
            self.audio_file_list.addItem(item)
            
        self.log(f"Loaded {len(audio_files)} audio files", "INFO")
        
    def on_audio_selected(self, item):
        """Handle audio file selection"""
        audio_path = item.data(Qt.ItemDataRole.UserRole)
        self.current_audio_file = audio_path
        
        try:
            file_size = Path(audio_path).stat().st_size / 1024  # KB
            self.audio_info_label.setText(f"Selected: {Path(audio_path).name} ({file_size:.1f} KB)")
            
            self.play_audio_button.setEnabled(True)
            self.open_audio_button.setEnabled(True)
            
            self.log(f"Selected audio file: {Path(audio_path).name}", "INFO")
            
        except Exception as e:
            self.audio_info_label.setText(f"Error: {str(e)}")
            self.log(f"Error selecting audio: {str(e)}", "ERROR")
            
    def play_audio(self):
        """Play the selected audio file"""
        if not self.current_audio_file:
            return
            
        try:
            import subprocess
            import platform
            
            self.log(f"Playing audio: {Path(self.current_audio_file).name}", "INFO")
            self.audio_status_label.setText("▶️ Playing...")
            self.stop_audio_button.setEnabled(True)
            
            # Use system default audio player
            system = platform.system()
            if system == "Windows":
                os.startfile(self.current_audio_file)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", self.current_audio_file])
            else:  # Linux
                subprocess.Popen(["xdg-open", self.current_audio_file])
                
            self.audio_status_label.setText("▶️ Playing (in system player)")
            
        except Exception as e:
            self.log(f"Error playing audio: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Playback Error", f"Failed to play audio:\n{str(e)}")
            self.audio_status_label.setText("Error")
            
    def stop_audio(self):
        """Stop audio playback"""
        # Note: This won't actually stop system players, just updates UI
        self.audio_status_label.setText("⏹️ Stopped")
        self.stop_audio_button.setEnabled(False)
        self.log("Audio playback stopped (if using system player, close it manually)", "INFO")
        
    def open_audio_external(self):
        """Open audio file in external player"""
        if not self.current_audio_file:
            return
            
        try:
            import subprocess
            import platform
            
            self.log(f"Opening audio externally: {Path(self.current_audio_file).name}", "INFO")
            
            system = platform.system()
            if system == "Windows":
                os.startfile(self.current_audio_file)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", self.current_audio_file])
            else:  # Linux
                subprocess.Popen(["xdg-open", self.current_audio_file])
                
        except Exception as e:
            self.log(f"Error opening audio: {str(e)}", "ERROR")
            QMessageBox.critical(self, "Open Error", f"Failed to open audio:\n{str(e)}")
        
    def delete_session(self):
        """Delete selected session and all related files"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
            
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Session",
            f"Delete session {session_id} and all related files?\n\nThis will remove:\n"
            "- Recording files\n- Workflow JSON\n- Cleaned workflow\n- AI analysis\n- Transcripts",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete recording directory
                import shutil
                recording_dir = Path("recordings") / session_id
                if recording_dir.exists():
                    shutil.rmtree(recording_dir)
                    
                # Delete workflow
                workflow_file = Path("workflows") / f"workflow_{session_id}.json"
                if workflow_file.exists():
                    workflow_file.unlink()
                    
                # Delete cleaned workflow
                cleaned_file = Path("clean_workflows") / f"cleaned_{session_id}.json"
                if cleaned_file.exists():
                    cleaned_file.unlink()
                    
                cleaned_txt = Path("clean_workflows") / f"cleaned_{session_id}.txt"
                if cleaned_txt.exists():
                    cleaned_txt.unlink()
                    
                # Delete analysis
                analysis_file = Path("clean_workflows/analysis") / f"analysis_cleaned_{session_id}.txt"
                if analysis_file.exists():
                    analysis_file.unlink()
                    
                self.status_bar.showMessage(f"Deleted session: {session_id}")
                self.load_sessions()
                self.workflow_text.clear()
                self.analysis_text.clear()
                self.transcript_text.clear()
                
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete session:\n{str(e)}")
                
    def analyze_selected_session(self):
        """Analyze the selected session"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
            
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        session_dir = Path("recordings") / session_id
        
        self.analyze_session_dir(str(session_dir))
        
    def analyze_session_dir(self, session_dir):
        """Analyze a session directory"""
        self.log(f"Starting analysis of session: {session_dir}", "INFO")
        self.status_bar.showMessage("Analyzing session...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        use_vosk = self.vosk_checkbox.isChecked()
        transcription_method = "Vosk (offline)" if use_vosk else "Whisper (online)"
        self.log(f"Using transcription: {transcription_method}", "INFO")
        
        def analyze_task():
            self.log("Running analyzer.analyze_session()...", "INFO")
            workflow = analyzer.analyze_session(session_dir, use_vosk=use_vosk)
            if workflow and "session" in workflow:
                session_id = workflow["session"]
                self.log(f"Analysis complete for session: {session_id}", "SUCCESS")
                workflow_file = Path("workflows") / f"workflow_{session_id}.json"
                
                # Clean if auto-clean is enabled
                if self.auto_analyze_checkbox.isChecked() and workflow_file.exists():
                    self.log("Auto-cleaning workflow...", "INFO")
                    cleaned = clean_workflow(str(workflow_file))
                    self.log("Workflow cleaned successfully", "SUCCESS")
                    
                    # Run Ollama if enabled
                    if self.ollama_checkbox.isChecked() and cleaned:
                        cleaned_path = Path("clean_workflows") / f"cleaned_{session_id}.json"
                        if cleaned_path.exists():
                            selected_model = self.ollama_model_combo.currentText()
                            self.log(f"Starting Ollama AI analysis with model: {selected_model}", "INFO")
                            analyze_workflow_with_ollama(str(cleaned_path), model_name=selected_model)
                            self.log("Ollama analysis complete", "SUCCESS")
            else:
                self.log("Analysis returned no workflow", "WARNING")
                            
            return workflow
            
        self.worker_thread = WorkerThread(analyze_task)
        self.worker_thread.log_message.connect(lambda msg: self.log(msg, "WORKER"))
        self.worker_thread.finished.connect(self.on_analysis_complete)
        self.worker_thread.start()
        
    def on_analysis_complete(self, success, message):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.log("Analysis workflow completed successfully", "SUCCESS")
            self.status_bar.showMessage("Analysis complete!")
            self.load_sessions()
            # Reload current session if one is selected
            current_item = self.session_list.currentItem()
            if current_item:
                session_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.load_session_details(session_id)
        else:
            self.log(f"Analysis failed: {message}", "ERROR")
            self.status_bar.showMessage("Analysis failed")
            QMessageBox.warning(self, "Analysis Error", f"Analysis failed:\n{message}")
            
    def clean_selected_workflow(self):
        """Clean the selected workflow"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
            
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        workflow_file = Path("workflows") / f"workflow_{session_id}.json"
        
        if not workflow_file.exists():
            QMessageBox.warning(self, "Clean Workflow", "Workflow file not found. Analyze the session first.")
            return
            
        try:
            clean_workflow(str(workflow_file))
            self.status_bar.showMessage(f"Cleaned workflow: {session_id}")
            self.load_sessions()
            self.load_session_details(session_id)
        except Exception as e:
            QMessageBox.critical(self, "Clean Error", f"Failed to clean workflow:\n{str(e)}")
            
    def run_ollama_analysis(self):
        """Run Ollama analysis on cleaned workflow"""
        current_item = self.session_list.currentItem()
        if not current_item:
            return
            
        session_id = current_item.data(Qt.ItemDataRole.UserRole)
        cleaned_file = Path("clean_workflows") / f"cleaned_{session_id}.json"
        
        if not cleaned_file.exists():
            self.log(f"Cleaned workflow not found for session: {session_id}", "WARNING")
            QMessageBox.warning(self, "Ollama Analysis", "Cleaned workflow not found. Clean the workflow first.")
            return
        
        selected_model = self.ollama_model_combo.currentText()
        self.log(f"Starting Ollama analysis for session: {session_id}", "INFO")
        self.log(f"Using model: {selected_model}", "INFO")
        self.status_bar.showMessage("Running Ollama analysis...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        def ollama_task():
            self.log("Connecting to Ollama server...", "INFO")
            return analyze_workflow_with_ollama(str(cleaned_file), model_name=selected_model)
            
        self.worker_thread = WorkerThread(ollama_task)
        self.worker_thread.log_message.connect(lambda msg: self.log(msg, "WORKER"))
        self.worker_thread.finished.connect(self.on_ollama_complete)
        self.worker_thread.start()
        
    def on_ollama_complete(self, success, message):
        """Handle Ollama analysis completion"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.log("Ollama analysis completed successfully!", "SUCCESS")
            self.status_bar.showMessage("Ollama analysis complete!")
            self.load_sessions()
            current_item = self.session_list.currentItem()
            if current_item:
                session_id = current_item.data(Qt.ItemDataRole.UserRole)
                self.load_session_details(session_id)
        else:
            self.log(f"Ollama analysis failed: {message}", "ERROR")
            self.status_bar.showMessage("Ollama analysis failed")
            QMessageBox.warning(self, "Ollama Error", f"Analysis failed:\n{message}")
            
    def extract_automation_steps(self):
        """Extract automation steps from AI analysis"""
        analysis_text = self.analysis_text.toPlainText()
        
        if not analysis_text:
            return
            
        # Try to extract steps section from analysis
        lines = analysis_text.split('\n')
        in_steps = False
        steps = []
        
        for line in lines:
            if 'steps:' in line.lower() or 'automation:' in line.lower():
                in_steps = True
                continue
            if in_steps:
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    steps.append(line.strip())
                elif line.strip() and not line.strip().startswith(' '):
                    # New section started
                    if steps:
                        break
                        
        if steps:
            self.automation_steps.setText('\n'.join(steps))
            self.execute_button.setEnabled(True)
        else:
            self.automation_steps.setText("No automation steps found in analysis.")
            
    def execute_automation(self):
        """Execute the automation (placeholder for future implementation)"""
        QMessageBox.information(
            self,
            "Automation Execution",
            "Automation execution is not yet implemented.\n\n"
            "Future versions will allow you to execute the suggested automation steps."
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FlowBot")
    
    # Set application icon if available
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = FlowBotGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
