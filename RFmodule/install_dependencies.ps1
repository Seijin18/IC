# RF Spectrum Analyzer - Install Dependencies
# This script installs all Python dependencies required for the RF spectrum analyzer

# Check if Python is installed
$pythonCmd = "python"
try {
    $pythonVersion = & $pythonCmd --version
    Write-Host "Found $pythonVersion"
} catch {
    # Try python3 if python fails
    $pythonCmd = "python3"
    try {
        $pythonVersion = & $pythonCmd --version
        Write-Host "Found $pythonVersion"
    } catch {
        Write-Host "Error: Python not found. Please install Python 3.6 or higher."
        Write-Host "Download from https://www.python.org/downloads/"
        exit 1
    }
}

# Check if pip is installed
try {
    & $pythonCmd -m pip --version
    Write-Host "Pip is installed."
} catch {
    Write-Host "Error: pip is not installed or not in path."
    Write-Host "Try installing pip with: $pythonCmd -m ensurepip --upgrade"
    exit 1
}

# Install dependencies from requirements.txt
Write-Host "Installing required Python packages..."
& $pythonCmd -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll dependencies have been successfully installed!`n"
    
    Write-Host "You can now use the RF Spectrum Analyzer tools:"
    Write-Host "1. To visualize data from a CSV file:"
    Write-Host "   $pythonCmd spectrum_visualizer.py --file your_data.csv"
    Write-Host ""
    Write-Host "2. To capture and visualize data directly from serial port:"
    Write-Host "   $pythonCmd spectrum_visualizer.py --serial COM3 --samples 100 --save-csv output.csv"
    Write-Host "   (Replace COM3 with your actual serial port)"
    Write-Host ""
    Write-Host "3. To generate test data for visualization testing:"
    Write-Host "   $pythonCmd generate_test_data.py"
    Write-Host ""
    Write-Host "For more information, refer to the README.md file."
} else {
    Write-Host "`nError: Failed to install some dependencies.`n"
    Write-Host "Try installing them manually with:"
    Write-Host "$pythonCmd -m pip install numpy pandas matplotlib pyserial"
}
