@echo off
chcp 65001 >nul 2>&1
title 3D Asset Generator

echo ============================================================
echo    3D Asset Generator - Smart Edition v3.0
echo ============================================================
echo.

set PROJECT_DIR=E:\bisai
set VENV_PATH=%PROJECT_DIR%\.venv

echo [Config]
echo   Project: %PROJECT_DIR%
echo   Venv: %VENV_PATH%
echo.

REM Check virtual environment
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo [!] Virtual environment not found: %VENV_PATH%
    echo.
    echo [*] Creating virtual environment...
    cd /d "%PROJECT_DIR%"
    python -m venv .venv
    
    if errorlevel 1 (
        echo [X] ERROR: Failed to create venv
        pause
        exit /b 1
    )
    
    echo [OK] Venv created
    echo.
    echo [*] Installing dependencies...
    call "%VENV_PATH%\Scripts\activate.bat"
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    
    if errorlevel 1 (
        echo [X] ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    
    echo [OK] Dependencies installed
    echo.
)

echo [*] Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"

if errorlevel 1 (
    echo [X] ERROR: Failed to activate venv
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check PyQt6 by trying to import it
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [*] PyQt6 not found, installing...
    pip install PyQt6 pyvista pyvistaqt trimesh -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [X] ERROR: Failed to install PyQt6
        pause
        exit /b 1
    )
    echo [OK] PyQt6 installed
    echo.
)

echo [*] Starting 3D Asset Generator...
echo ============================================================
echo.

cd /d "%PROJECT_DIR%"
python launcher.py

pause