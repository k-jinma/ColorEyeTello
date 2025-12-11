@echo off
echo ====================================
echo  Shape Detection (形状検出専用)
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
echo Starting Shape Detection...
echo (Press 'q' in the camera window to quit)
echo.
python shape_detector.py

echo.
echo Program finished.
pause