#!/usr/bin/env python3
"""
AI 3D Modeling Workstation - One-Click Launcher
一键启动 ComfyUI 和 GUI
"""

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
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def start_comfyui():
    """启动 ComfyUI（最小化窗口）"""
    print("[1/2] 正在启动 ComfyUI...")
    
    if not os.path.exists(COMFYUI_START_CMD):
        print(f"[ERROR] 找不到 ComfyUI 启动脚本：{COMFYUI_START_CMD}")
        return False
    
    try:
        # 使用 VBScript 创建最小化启动
        import tempfile
        
        # 创建临时 VBScript 文件
        vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "E:\\ComfyUI_windows_portable"
objShell.Run "cmd.exe /c run_nvidia_gpu.bat", 6, False
'''
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False, encoding='utf-8') as f:
            f.write(vbs_content)
            vbs_path = f.name
        
        # 执行 VBScript
        subprocess.Popen(['wscript.exe', vbs_path])
        
        # 清理临时文件（延迟删除）
        import time
        time.sleep(0.5)
        try:
            os.unlink(vbs_path)
        except:
            pass
        
        print("[OK] ComfyUI 已启动（窗口最小化）")
        return True
    except Exception as e:
        print(f"[ERROR] 启动失败：{e}")
        return False


def wait_for_comfyui(timeout=15):
    """等待 ComfyUI 启动完成"""
    print(f"[2/2] 等待 ComfyUI 初始化（最多{timeout}秒）...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(COMFYUI_PORT):
            print(f"[OK] ComfyUI 已就绪（端口 {COMFYUI_PORT}）")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\n[WARNING] ComfyUI 可能启动失败，但将继续启动 GUI...")
    return False


def start_gui():
    """启动 GUI"""
    print("\n" + "=" * 50)
    print("  正在启动 GUI...")
    print("=" * 50 + "\n")
    
    if not os.path.exists(GUI_SCRIPT):
        print(f"[ERROR] 找不到 Python：{GUI_SCRIPT}")
        print("请检查虚拟环境是否正确创建")
        input("按任意键退出...")
        return
    
    try:
        subprocess.run([GUI_SCRIPT] + GUI_ARGS, cwd=os.path.dirname(__file__))
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    except Exception as e:
        print(f"[ERROR] GUI 启动失败：{e}")
        input("按任意键退出...")


def main():
    """主函数"""
    print("=" * 50)
    print("  AI 全链路 3D 建模工作站 - 启动器")
    print("=" * 50)
    print()
    
    # 检查 ComfyUI 是否已在运行
    if is_port_in_use(COMFYUI_PORT):
        print(f"[OK] ComfyUI 已经在运行（端口 {COMFYUI_PORT}）")
    else:
        # 启动 ComfyUI
        if start_comfyui():
            wait_for_comfyui()
    
    # 启动 GUI
    start_gui()
    
    print("\n" + "=" * 50)
    print("  程序已退出")
    print("=" * 50)
    input("按任意键关闭窗口...")


if __name__ == "__main__":
    main()
