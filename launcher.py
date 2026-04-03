#!/usr/bin/env python3

import os
import sys
import socket
import subprocess
import time

import configparser
import winreg


def get_config_paths():
    config = configparser.ConfigParser()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.ini")

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\AI3DModeling")
        comfyui_path = winreg.QueryValueEx(key, "ComfyUIPath")[0]
        install_dir = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)
        return comfyui_path, install_dir
    except:
        pass

    if os.path.exists(config_file):
        config.read(config_file, encoding="utf-8")
        comfyui_path = config.get(
            "Paths",
            "ComfyUIPath",
            fallback=os.path.join(script_dir, "backend", "ComfyUI"),
        )
        install_dir = config.get("Paths", "InstallDir", fallback=script_dir)
        return comfyui_path, install_dir

    comfyui_path = os.path.join(script_dir, "backend", "ComfyUI")
    return comfyui_path, script_dir


COMFYUI_PATH, INSTALL_DIR = get_config_paths()
COMFYUI_PORT = 8188
COMFYUI_START_CMD = os.path.join(COMFYUI_PATH, "..", "run_nvidia_gpu.bat")
GUI_SCRIPT = os.path.join(INSTALL_DIR, "backend", "python_embeded", "python.exe")
GUI_ARGS = [os.path.join(INSTALL_DIR, "frontend", "gui.py")]


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_comfyui():
    print("Starting ComfyUI...")

    if not os.path.exists(COMFYUI_START_CMD):
        print(f"ComfyUI not found: {COMFYUI_START_CMD}")
        return False

    comfyui_dir = os.path.dirname(COMFYUI_START_CMD)

    try:
        import tempfile

        vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "{comfyui_dir.replace(os.sep, "\\\\")}"
objShell.Run "cmd.exe /c run_nvidia_gpu.bat", 6, False
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vbs", delete=False, encoding="utf-8"
        ) as f:
            f.write(vbs_content)
            vbs_path = f.name

        subprocess.Popen(["wscript.exe", vbs_path])
        time.sleep(0.5)
        try:
            os.unlink(vbs_path)
        except:
            pass
        return True
    except:
        return False

    try:
        import tempfile

        vbs_content = f"""Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "E:\\ComfyUI_windows_portable"
objShell.Run "cmd.exe /c run_nvidia_gpu.bat", 6, False
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".vbs", delete=False, encoding="utf-8"
        ) as f:
            f.write(vbs_content)
            vbs_path = f.name

        subprocess.Popen(["wscript.exe", vbs_path])
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
