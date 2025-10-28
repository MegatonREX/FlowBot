# FlowBot GUI Launcher for PowerShell
# Run with: .\launch_gui.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FlowBot - AI Workflow Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.8 or higher" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if PyQt6 is installed
$pyqt6Check = python -c "import PyQt6" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ PyQt6 is not installed" -ForegroundColor Yellow
    Write-Host "  Installing required dependencies..." -ForegroundColor Yellow
    Write-Host ""
    pip install -r requirements_gui.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Starting FlowBot GUI..." -ForegroundColor Green
Write-Host ""

# Launch the GUI
python gui.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ FlowBot GUI encountered an error" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
