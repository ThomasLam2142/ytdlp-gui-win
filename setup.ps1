# Set Python version and download URL
$pythonVersion = "3.12.2"
$installerUrl = "https://www.python.org/ftp/python/$pythonVersion/python-$pythonVersion-amd64.exe"
$installerPath = "$PSScriptRoot\python-$pythonVersion-amd64.exe"

function Check-Python312 {
    try {
        $output = & python --version 2>$null
        return $output -match "Python 3\.12"
    } catch {
        return $false
    }
}

function Check-Venv {
    try {
        & python -m venv --help > $null 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Install-Python {
    Write-Output "Downloading Python $pythonVersion installer..."
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

    Write-Output "Installing Python $pythonVersion silently..."
    Start-Process -FilePath $installerPath -ArgumentList `
        "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1", "Include_venv=1" `
        -Wait -NoNewWindow

    Remove-Item $installerPath -Force
    Write-Output "Python $pythonVersion installation complete."
}

# --- MAIN ---
if (Check-Python312) {
    Write-Output "Python 3.12 is in PATH."

    if (Check-Venv) {
        Write-Output "venv module is available."
    } else {
        Write-Output "venv module is missing. Reinstalling Python..."
        Install-Python
    }
} else {
    Write-Output "Python 3.12 not found. Installing now..."
    Install-Python
}
