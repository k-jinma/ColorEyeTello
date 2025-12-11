@echo off
echo ====================================
echo  Tello Color Detection Setup
echo ====================================

REM 仮想環境の名前
set VENV_NAME=tello_env

REM 現在のディレクトリをプロジェクトルートに設定
cd /d "%~dp0"

echo.
echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo.
echo [2/5] Creating virtual environment...
if exist %VENV_NAME% (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv %VENV_NAME%
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

echo.
echo [3/5] Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

echo.
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [5/5] Installing required packages...
pip install djitellopy opencv-python pillow numpy

if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ====================================
echo  Setup completed successfully!
echo ====================================
echo.
echo To run the programs:
echo   1. Activate virtual environment: %VENV_NAME%\Scripts\activate
echo   2. Run color detection: python color_detector.py
echo   3. Run shape detection: python shape_detector.py
echo   4. Run combined detection: python zukei.py
echo.
echo Press any key to exit...
pause > nul