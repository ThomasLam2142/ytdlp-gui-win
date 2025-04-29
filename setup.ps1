# Function to check Python version
function Check-PythonVersion {
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match 'Python 3\.12\.\d+') {
            Write-Host "Python 3.12 is installed"
            return $true
        }
        else {
            Write-Host "Python 3.12 is not installed. Current version: $pythonVersion"
            return $false
        }
    }
    catch {
        Write-Host "Python is not installed or not in PATH"
        return $false
    }
}

# Function to download Python installer
function Download-Python {
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $installerPath = Join-Path $env:TEMP "python-3.12.0-amd64.exe"
    
    Write-Host "Downloading Python 3.12 installer..."
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
    
    return $installerPath
}

# Function to install Python
function Install-Python {
    $installerPath = Download-Python
    
    Write-Host "Installing Python 3.12..."
    Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    
    # Refresh the PATH environment variable
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Verify installation
    if (Check-PythonVersion) {
        Write-Host "Python 3.12 installation completed successfully!"
    }
    else {
        Write-Host "Error: Python installation failed"
        return $false
    }
    
    return $true
}

# Function to check virtual environment
function Check-VirtualEnvironment {
    try {
        if (Test-Path -Path "venv") {
            Write-Host "Virtual environment directory exists"
            return $true
        }
        else {
            Write-Host "Virtual environment directory not found"
            return $false
        }
    }
    catch {
        Write-Host "Error checking virtual environment: $_"
        return $false
    }
}

# Main script execution
Write-Host "Checking Python 3.12 installation..."
$pythonCheck = Check-PythonVersion

if (-not $pythonCheck) {
    $installPython = Read-Host "Python 3.12 is not installed. Would you like to install it? (Y/N)"
    if ($installPython -eq 'Y' -or $installPython -eq 'y') {
        Install-Python
        $pythonCheck = Check-PythonVersion
    }
}

Write-Host "`nChecking virtual environment..."
$venvCheck = Check-VirtualEnvironment

# Summary
Write-Host "`nSummary:"
if ($pythonCheck -and $venvCheck) {
    Write-Host "All checks passed! Python 3.12 and virtual environment are ready."
}
elseif ($pythonCheck -and !$venvCheck) {
    Write-Host "Python 3.12 is installed, but virtual environment is missing."
}
elseif (!$pythonCheck -and $venvCheck) {
    Write-Host "Python 3.12 is missing, but virtual environment exists."
}
else {
    Write-Host "Both Python 3.12 and virtual environment are missing."
}

# Optional: Create virtual environment if missing
if ($pythonCheck -and !$venvCheck) {
    $createVenv = Read-Host "Would you like to create a new virtual environment? (Y/N)"
    if ($createVenv -eq 'Y' -or $createVenv -eq 'y') {
        python -m venv venv
        Write-Host "Virtual environment created successfully!"
    }
}