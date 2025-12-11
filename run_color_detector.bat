@echo off
echo ====================================
echo  Color Detection (色検出専用)
echo ====================================

REM 仮想環境の名前
set VENV_NAME=tello_env

REM 現在のディレクトリをプロジェクトルートに設定
cd /d "%~dp0"

REM 仮想環境が存在するかチェック
if not exist %VENV_NAME% (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to create the environment.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call %VENV_NAME%\Scripts\activate.bat

echo.
echo Starting Color Detection...
echo (Press 'q' in the camera window to quit)
echo.
python color_detector.py

echo.
echo Program finished.
pause