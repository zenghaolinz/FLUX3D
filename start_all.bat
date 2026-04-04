@echo off
chcp 65001 >nul 2>&1
title 3D Asset Generator

echo ============================================================
echo    3D Asset Generator - Smart Edition v3.0
echo ============================================================
echo.

set PROJECT_DIR=E:\bisai
set COMFYUI_PATH=E:\ComfyUI_windows_portable
set VENV_PATH=%PROJECT_DIR%\.venv

echo [Config]
echo   Project: %PROJECT_DIR%
echo   ComfyUI: %COMFYUI_PATH%
echo   Venv: %VENV_PATH%
echo.

REM === Step 1: Start ComfyUI ===
echo ============================================================
echo [Step 1/2] Starting ComfyUI Backend
echo ============================================================
echo.

if exist "%COMFYUI_PATH%\run_nvidia_gpu.bat" (
    echo [*] Starting ComfyUI in background...
    cd /d "%COMFYUI_PATH%"
    start "ComfyUI Backend" /min cmd /c "run_nvidia_gpu.bat"
    echo [OK] ComfyUI started
    echo [*] Waiting 15 seconds for initialization...
    timeout /t 15 /nobreak >nul
    echo [OK] ComfyUI should be ready at http://127.0.0.1:8188
) else (
    echo [!] WARNING: ComfyUI not found at %COMFYUI_PATH%
    echo [!] Please check if ComfyUI is installed correctly
    echo.
    set /p CONT="Continue anyway? (y/n): "
    if /i not "%CONT%"=="y" exit /b 1
)

echo.

REM === Step 2: Start Application ===
echo ============================================================
echo [Step 2/2] Starting Application
echo ============================================================
echo.

if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo [!] Virtual environment not found
    echo [*] Creating virtual environment...
    cd /d "%PROJECT_DIR%"
    python -m venv .venv
    if errorlevel 1 (
        echo [X] ERROR: Failed to create venv
        pause
        exit /b 1
    )
    
    echo [*] Installing dependencies...
    call "%VENV_PATH%\Scripts\activate.bat"
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [X] ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
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

echo ============================================================
echo [*] Starting 3D Asset Generator...
echo ============================================================
echo.
echo Tips:
echo   - Backend: http://127.0.0.1:8188
echo   - Configure API Key in the GUI
echo   - Press Ctrl+C to stop
echo.
echo ============================================================
echo.

cd /d "%PROJECT_DIR%"
python launcher.py

if errorlevel 1 (
    echo.
    echo [X] ERROR: Application failed to start
    echo Error code: %errorlevel%
)

echo.
echo ============================================================
echo [END] Application closed
echo ============================================================
pause