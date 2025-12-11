@echo off
echo ====================================
echo  Combined Detection (色＋形状統合版)
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
echo Starting Combined Color + Shape Detection...
echo (Press 'q' in the camera window to quit)
echo.
python zukei.py

echo.
echo Program finished.
pause