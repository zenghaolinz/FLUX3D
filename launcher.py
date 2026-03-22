#!/usr/bin/env python3

import os
import sys
import socket
import subprocess
import time

COMFYUI_PORT = 8188
COMFYUI_START_CMD = r"E:\ComfyUI_windows_portable\run_nvidia_gpu.bat"
GUI_SCRIPT = os.path.join(os.path.dirname(__file__), ".venv", "Scripts", "python.exe")
GUI_ARGS = ["frontend/gui.py"]


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def start_comfyui():
    print("Starting ComfyUI...")
    
    if not os.path.exists(COMFYUI_START_CMD):
        print(f"ComfyUI not found: {COMFYUI_START_CMD}")
        return False
    
    try:
        import tempfile
        vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "E:\\ComfyUI_windows_portable"
objShell.Run "cmd.exe /c run_nvidia_gpu.bat", 6, False
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False, encoding='utf-8') as f:
            f.write(vbs_content)
            vbs_path = f.name
        
        subprocess.Popen(['wscript.exe', vbs_path])
        time.sleep(0.5)
        try:
            os.unlink(vbs_path)
        except:
            pass
        return True
    except:
        return False


def wait_for_comfyui(timeout=15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(COMFYUI_PORT):
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print()
    return False


def start_gui():
    if not os.path.exists(GUI_SCRIPT):
        print(f"Python not found: {GUI_SCRIPT}")
        input("Press Enter to exit...")
        return
    
    try:
        subprocess.run([GUI_SCRIPT] + GUI_ARGS, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"GUI error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    if not is_port_in_use(COMFYUI_PORT):
        if start_comfyui():
            wait_for_comfyui()
    
    start_gui()