@echo off
chcp 65001 >nul 2>&1
title Start ComfyUI Backend

echo ============================================================
echo    Start ComfyUI Backend
echo ============================================================
echo.

REM Set ComfyUI path (modify if needed)
set COMFYUI_PATH=E:\ComfyUI_windows_portable

REM Check if path exists
if not exist "%COMFYUI_PATH%\run_nvidia_gpu.bat" (
    echo [X] ERROR: ComfyUI path not found: %COMFYUI_PATH%
    echo.
    echo Please edit this bat file and modify COMFYUI_PATH
    echo.
    pause
    exit /b 1
)

echo [*] ComfyUI Directory: %COMFYUI_PATH%
echo [*] Mode: NVIDIA GPU Acceleration
echo.
echo [*] Starting ComfyUI...
echo ============================================================
echo.

REM Switch to ComfyUI directory and start
cd /d "%COMFYUI_PATH%"
call run_nvidia_gpu.bat

pause