@echo off
REM RF Spectrum Analyzer - Install Dependencies
REM This batch file installs all Python dependencies required for the RF spectrum analyzer

echo Installing RF Spectrum Analyzer dependencies...
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    python3 --version > nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python not found. Please install Python 3.6 or higher.
        echo Download from https://www.python.org/downloads/
        exit /b 1
    ) else (
        set pythonCmd=python3
    )
) else (
    set pythonCmd=python
)

echo Found %pythonCmd%: 
%pythonCmd% --version
echo.

REM Check if pip is installed
%pythonCmd% -m pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not installed or not in path.
    echo Try installing pip with: %pythonCmd% -m ensurepip --upgrade
    exit /b 1
)

echo Installing required Python packages...
%pythonCmd% -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo All dependencies have been successfully installed!
    echo.
    
    echo You can now use the RF Spectrum Analyzer tools:
    echo 1. To visualize data from a CSV file:
    echo    %pythonCmd% spectrum_visualizer.py --file your_data.csv
    echo.
    echo 2. To capture and visualize data directly from serial port:
    echo    %pythonCmd% spectrum_visualizer.py --serial COM3 --samples 100 --save-csv output.csv
    echo    (Replace COM3 with your actual serial port)
    echo.
    echo 3. To generate test data for visualization testing:
    echo    %pythonCmd% generate_test_data.py
    echo.
    echo For more information, refer to the README.md file.
) else (
    echo.
    echo Error: Failed to install some dependencies.
    echo.
    echo Try installing them manually with:
    echo %pythonCmd% -m pip install numpy pandas matplotlib pyserial
)

pause
