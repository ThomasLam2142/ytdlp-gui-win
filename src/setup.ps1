Set-Location -Path $PSScriptRoot

# Move up to the project root (src's parent)
Set-Location -Path (Join-Path $PSScriptRoot "..")

# Check if python3.11 is available in the PATH
$pythonVersion = & python --version 2>&1

if ($pythonVersion -match "Python 3\.11") {
    Write-Output "Python 3.11 is installed and available in PATH."
} else {
    Write-Host "Python 3.11 is not installed. Installing..."

    # Download the official Python 3.11 installer (64-bit Windows)
    $pythonInstallerUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
    $installerPath = "$env:TEMP\python-3.11.0-amd64.exe"
    Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath

    # Install Python silently for all users and add to PATH
    Start-Process -Wait -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1"

    # Remove installer after installation
    Remove-Item $installerPath

    # Refresh the environment variables for the current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

# Confirm Python version
$newPythonVersion = & python --version 2>&1
Write-Host "Python version now: $newPythonVersion"

# Set virtual environment directory
$venvDir = ".\venv"

if (Test-Path $venvDir) {
    Write-Host "Virtual environment already exists at: $venvDir"
} else {
    # Create virtual environment
    Write-Host "Creating virtual environment at: $venvDir"
    python -m venv $venvDir
}

# Activate virtual environment
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..."
    & $activateScript
} else {
    Write-Warning "Virtual environment exists, but activation script not found."
}

# Install dependencies
Write-Host "Installing dependencies..."
pip install -r src\requirements.txt

# Confirm dependencies are installed
Write-Host "Dependencies installed successfully."

Write-Host "Setup complete."

# Start the GUI application
Write-Host "Starting GUI application..."
python src\gui.py


pause
