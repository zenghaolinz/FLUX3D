import json
import urllib.request
import requests
import websocket
import uuid
import time
import os
import random
import glob
from pathlib import Path

# Config
SERVER = "127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
TEMP_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\temp"
MODEL_DIR = os.path.join(OUTPUT_DIR, "3D")

# Model configs
FLUX_FAST = "flux-2-klein-4b-Q4_K_M.gguf"
FLUX_QUALITY = "Flux-2-Klein-9B-KV-Q4_K_M.gguf"

# Workflow files
WORKFLOWS = {
    "Text to 3D": r"E:\bisai\backend\文生图片生模型.json",
    "Image to 3D": r"E:\bisai\backend\图片生模型.json",
    "Dual Image Fusion": r"E:\bisai\backend\双图生图生模型.json",
}

FLUX2_IMPROVE_WORKFLOW = r"E:\bisai\backend\改图.json"


def upload_image(path):
    with open(path, "rb") as f:
        r = requests.post(f"http://{SERVER}/upload/image", files={"image": f})
    if r.status_code != 200:
        raise Exception(f"Upload failed: {r.text}")
    return r.json()["name"]


def queue_prompt(workflow):
    payload = {
        "prompt": workflow,
        "client_id": CLIENT_ID,
        "extra_data": {"extra_pnginfo": {"ts": str(time.time())}},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"http://{SERVER}/prompt", data=data)
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        if "prompt_id" not in result:
            raise Exception(f"Bad response: {result}")
        return result
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.read().decode()}")
        raise


def get_history(pid):
    with urllib.request.urlopen(f"http://{SERVER}/history/{pid}") as resp:
        return json.loads(resp.read())


def find_file(prefix, subfolder=""):
    search_dir = os.path.join(OUTPUT_DIR, subfolder) if subfolder else OUTPUT_DIR
    if not os.path.exists(search_dir):
        return None
    pattern = os.path.join(search_dir, f"{prefix}*")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None


def extract_file(history, node_id):
    if node_id not in history.get("outputs", {}):
        return None

    out = history["outputs"][node_id]
    for field in ["images", "files", "result"]:
        if field not in out:
            continue
        data = out[field]

        if isinstance(data, list) and len(data) > 0:
            if field == "result" and isinstance(data[0], str):
                path = os.path.join(OUTPUT_DIR, data[0].replace("\\", "/"))
                return path if os.path.exists(path) else None

            for item in data:
                if isinstance(item, dict) and "filename" in item:
                    sub = item.get("subfolder", "")
                    path = os.path.join(OUTPUT_DIR, sub, item["filename"])
                    if os.path.exists(path):
                        return path
                    path = os.path.join(TEMP_DIR, item["filename"])
                    if os.path.exists(path):
                        return path
    return None


def run_pipeline(
    mode, quality, prompt, img1, img2=None, progress=None, intermediate_callback=None
):
    ts = int(time.time())
    prefix = f"UI_{ts}"

    flux_model = FLUX_QUALITY if quality == "quality" else FLUX_FAST

    if mode not in WORKFLOWS:
        raise ValueError(f"Unknown mode: {mode}")

    with open(WORKFLOWS[mode], "r", encoding="utf-8") as f:
        wf = json.load(f)

    if progress:
        progress(0.05, "Loading workflow...")

    if mode == "Text to 3D":
        if not prompt:
            raise ValueError("Prompt required")
        wf["64"]["inputs"]["text"] = prompt
        wf["63"]["inputs"]["noise_seed"] = random.randint(1, 10000000)
        wf["66"]["inputs"]["unet_name"] = flux_model
        wf["62"]["inputs"]["filename_prefix"] = f"{prefix}_Flux"
        wf["18"]["inputs"]["filename_prefix"] = f"3D/{prefix}_White"
        wf["34"]["inputs"]["filename_prefix"] = f"3D/{prefix}_Textured"

        wf["998"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]},
        }
        wf["997"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]},
        }
        wf["996"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]},
        }

        node_map = {
            "62": "2d",
            "998": "2d",
            "997": "normal",
            "996": "uv",
            "47": "model",
        }

    elif mode == "Image to 3D":
        if not img1:
            raise ValueError("Image required")

        from PIL import Image

        with Image.open(img1) as im:
            img_w, img_h = im.size

        uploaded = upload_image(img1)
        wf["71"]["inputs"]["image"] = uploaded

        wf["24"]["inputs"]["width"] = img_w
        wf["24"]["inputs"]["height"] = img_h
        wf["25"]["inputs"]["width"] = img_w
        wf["25"]["inputs"]["height"] = img_h

        wf["18"]["inputs"]["filename_prefix"] = f"3D/{prefix}_White"
        wf["34"]["inputs"]["filename_prefix"] = f"3D/{prefix}_Textured"

        wf["998"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]},
        }
        wf["997"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]},
        }
        wf["996"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]},
        }

        node_map = {"998": "2d", "997": "normal", "996": "uv", "47": "model"}

    elif mode == "Dual Image Fusion":
        if not prompt:
            raise ValueError("Prompt required")
        if not img1 or not img2:
            raise ValueError("Both images required")

        up1 = upload_image(img1)
        up2 = upload_image(img2)
        wf["74"]["inputs"]["image"] = up1
        wf["75"]["inputs"]["image"] = up2
        wf["73"]["inputs"]["text"] = prompt
        wf["72"]["inputs"]["noise_seed"] = random.randint(1, 10000000)
        wf["76"]["inputs"]["unet_name"] = flux_model
        wf["63"]["inputs"]["filename_prefix"] = f"{prefix}_Flux"
        wf["18"]["inputs"]["filename_prefix"] = f"3D/{prefix}_White"
        wf["34"]["inputs"]["filename_prefix"] = f"3D/{prefix}_Textured"

        wf["998"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]},
        }
        wf["997"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]},
        }
        wf["996"] = {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]},
        }

        node_map = {
            "63": "2d",
            "998": "2d",
            "997": "normal",
            "996": "uv",
            "47": "model",
        }

    # Connect websocket
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER}/ws?clientId={CLIENT_ID}")

    pid = queue_prompt(wf)["prompt_id"]

    # Listen for progress
    while True:
        msg = ws.recv()
        if isinstance(msg, str):
            data = json.loads(msg)

            if data.get("type") == "progress":
                d = data["data"]
                pct = 0.1 + (d["value"] / d["max"]) * 0.85
                desc = (
                    "Processing..." if d["value"] < d["max"] / 3 else "Building 3D..."
                )
                if progress:
                    progress(pct, desc)

            elif data.get("type") == "executing":
                d = data["data"]
                nid = str(d.get("node", ""))

                if nid and nid in node_map and intermediate_callback:
                    time.sleep(1.0)

                    fpath = None
                    if nid == "998":
                        fpath = find_file(f"{prefix}_RemBG")
                    elif nid == "997":
                        fpath = find_file(f"{prefix}_Normal")
                    elif nid == "996":
                        fpath = find_file(f"{prefix}_Texture")
                    elif nid in ("62", "63"):
                        fpath = find_file(f"{prefix}_Flux")
                    elif nid == "47":
                        try:
                            hist = get_history(pid)[pid]
                            fpath = extract_file(hist, nid)
                        except:
                            fpath = find_file(f"{prefix}_Textured", "3D")

                    if fpath and os.path.exists(fpath):
                        intermediate_callback(node_map[nid], fpath)

                if d.get("node") is None and d.get("prompt_id") == pid:
                    break

    if progress:
        progress(0.98, "Finalizing...")
    time.sleep(1.0)

    # Extract final results
    result_2d = find_file(f"{prefix}_Flux") or find_file(f"{prefix}_RemBG")
    result_normal = find_file(f"{prefix}_Normal")
    result_uv = find_file(f"{prefix}_Texture")
    result_model = find_file(f"{prefix}_Textured", "3D")

    # Fallback for Image to 3D mode
    if mode == "Image to 3D":
        result_2d = img1

    return result_2d, result_normal, result_uv, result_model


# Keep old function name for compatibility
run_comfyui_pipeline = run_pipeline


# ============================================================
# Flux2 Klein 改图工具
# ============================================================


def improve_image_with_flux2klein(
    original_image_path: str, improvement_prompt: str, progress=None
) -> str:
    """
    使用flux2klein改进图片质量

    Args:
        original_image_path: 原图片路径
        improvement_prompt: 改进提示词（英文）
        progress: 进度回调函数

    Returns:
        改进后的图片路径
    """
    if not original_image_path or not os.path.exists(original_image_path):
        raise ValueError("原图片路径不存在")

    ts = int(time.time())
    prefix = f"IMPROVED_{ts}"

    if not os.path.exists(FLUX2_IMPROVE_WORKFLOW):
        raise ValueError("flux2改图工作流文件不存在")

    with open(FLUX2_IMPROVE_WORKFLOW, "r", encoding="utf-8") as f:
        wf = json.load(f)

    if progress:
        progress(0.05, "加载flux2改图工作流...")

    # 上传原图
    uploaded = upload_image(original_image_path)
    wf["18"]["inputs"]["image"] = uploaded

    # 设置改进提示词
    wf["16"]["inputs"]["text"] = improvement_prompt

    # 设置随机seed
    wf["13"]["inputs"]["noise_seed"] = random.randint(1, 10000000)

    # 设置输出文件名
    wf["19"]["inputs"]["filename_prefix"] = prefix

    if progress:
        progress(0.1, "启动flux2图片改进...")

    # 连接websocket
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER}/ws?clientId={CLIENT_ID}")

    pid = queue_prompt(wf)["prompt_id"]

    # 监听进度
    while True:
        msg = ws.recv()
        if isinstance(msg, str):
            data = json.loads(msg)

            if data.get("type") == "progress":
                d = data["data"]
                pct = 0.15 + (d["value"] / d["max"]) * 0.75
                if progress:
                    progress(pct, "FLUX2改进图片...")

            elif data.get("type") == "executing":
                d = data["data"]
                if d.get("node") is None and d.get("prompt_id") == pid:
                    break

    if progress:
        progress(0.95, "获取改进后的图片...")

    time.sleep(1.0)

    # 查找改进后的图片
    improved_image = find_file(prefix)

    if not improved_image:
        raise Exception("flux2改图失败，未找到输出文件")

    return improved_image


# ============================================================
# Agent工具函数 (供AI智能体调用)
# ============================================================

import trimesh


def tool_generate_3d(image_path: str) -> str:
    """
    [工具1] 供 Agent 调用的 3D 生成工具。
    输入：前端传入的图片绝对路径。
    输出：JSON 字符串，包含状态和生成的模型路径。
    """
    if not image_path or not os.path.exists(image_path):
        return json.dumps(
            {"status": "error", "message": "无法找到指定的图片文件，请检查上传路径。"}
        )

    try:
        res_2d, res_normal, res_uv, model_path = run_pipeline(
            mode="Image to 3D", quality="fast", prompt="", img1=image_path
        )

        if model_path and os.path.exists(model_path):
            return json.dumps(
                {
                    "status": "success",
                    "model_path": model_path,
                    "image_2d": res_2d,
                    "image_normal": res_normal,
                    "image_uv": res_uv,
                    "message": "3D模型生成成功！请继续调用分析工具提取物理参数。",
                }
            )
        else:
            return json.dumps(
                {
                    "status": "error",
                    "message": "后台处理完成，但未在目录中找到模型文件。",
                }
            )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"调用 3D 引擎失败: {str(e)}"})


def tool_analyze_geometry(glb_path: str) -> str:
    """
    [工具2] 供 Agent 调用的工业参数分析工具。
    输入：生成的 GLB 模型路径。
    输出：JSON 字符串，包含体积、表面积等硬核工业数据。
    """
    if not glb_path or not os.path.exists(glb_path):
        return json.dumps(
            {"status": "error", "message": "未找到3D模型文件，请确认模型是否已生成。"}
        )

    try:
        scene = trimesh.load(glb_path, force="scene")

        if isinstance(scene, trimesh.Scene):
            geometries = list(scene.geometry.values())
            mesh = trimesh.util.concatenate(geometries) if geometries else None
        else:
            mesh = scene

        if not mesh or mesh.is_empty:
            return json.dumps(
                {"status": "error", "message": "模型解析为空或无有效几何体。"}
            )

        return json.dumps(
            {
                "status": "success",
                "volume_mm3": round(float(mesh.volume), 2),
                "surface_area_mm2": round(float(mesh.area), 2),
                "bounding_box_xyz": [
                    round(float(x), 2) for x in mesh.bounding_box.extents
                ],
                "message": "几何分析完成。请根据这些数据输出最终的工业评估与耗材报告。",
            }
        )
    except Exception as e:
        return json.dumps(
            {"status": "error", "message": f"解析三维几何数据时出错: {str(e)}"}
        )


def tool_improve_image_flux2klein(image_path: str, improvement_prompt: str) -> str:
    """
    [工具3] 使用flux2klein改进图片质量

    Args:
        image_path: 原图片路径
        improvement_prompt: 改进提示词（英文）
    Returns:
        JSON字符串，包含改进后的图片路径
    """
    if not image_path or not os.path.exists(image_path):
        return json.dumps({"status": "error", "message": "图片路径不存在"})

    try:
        improved_path = improve_image_with_flux2klein(image_path, improvement_prompt)

        if improved_path and os.path.exists(improved_path):
            return json.dumps(
                {
                    "status": "success",
                    "improved_image_path": improved_path,
                    "message": "图片改进成功！已生成更适合3D建模的图片。",
                }
            )
        else:
            return json.dumps(
                {"status": "error", "message": "flux2改图完成但未找到输出文件"}
            )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"flux2改图失败: {str(e)}"})


def tool_generate_3d_text(prompt: str, quality: str = "fast") -> str:
    """
    [工具4] 文生3D模型

    Args:
        prompt: 文字描述
        quality: fast/quality

    Returns:
        JSON字符串，包含生成的模型路径
    """
    if not prompt:
        return json.dumps({"status": "error", "message": "Prompt不能为空"})

    try:
        _, _, _, model_path = run_pipeline(
            mode="Text to 3D", quality=quality, prompt=prompt, img1=None
        )

        if model_path and os.path.exists(model_path):
            return json.dumps(
                {
                    "status": "success",
                    "model_path": model_path,
                    "message": "文生3D模型成功！",
                }
            )
        else:
            return json.dumps(
                {"status": "error", "message": "生成完成但未找到模型文件"}
            )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"文生3D失败: {str(e)}"})


def tool_generate_3d_image(image_path: str, quality: str = "fast") -> str:
    """
    [工具5] 图生3D模型

    Args:
        image_path: 图片路径
        quality: fast/quality

    Returns:
        JSON字符串，包含生成的模型路径
    """
    if not image_path or not os.path.exists(image_path):
        return json.dumps({"status": "error", "message": "图片路径不存在"})

    try:
        res_2d, res_normal, res_uv, model_path = run_pipeline(
            mode="Image to 3D", quality=quality, prompt="", img1=image_path
        )

        if model_path and os.path.exists(model_path):
            return json.dumps(
                {
                    "status": "success",
                    "model_path": model_path,
                    "image_2d": res_2d,
                    "image_normal": res_normal,
                    "image_uv": res_uv,
                    "message": "图生3D模型成功！",
                }
            )
        else:
            return json.dumps(
                {"status": "error", "message": "生成完成但未找到模型文件"}
            )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"图生3D失败: {str(e)}"})


def tool_generate_3d_dual(
    image1_path: str, image2_path: str, prompt: str, quality: str = "fast"
) -> str:
    """
    [工具6] 双图融合生3D模型

    Args:
        image1_path: 图片1路径
        image2_path: 图片2路径
        prompt: 文字描述
        quality: fast/quality

    Returns:
        JSON字符串，包含生成的模型路径
    """
    if not image1_path or not os.path.exists(image1_path):
        return json.dumps({"status": "error", "message": "图片1路径不存在"})

    if not image2_path or not os.path.exists(image2_path):
        return json.dumps({"status": "error", "message": "图片2路径不存在"})

    if not prompt:
        return json.dumps({"status": "error", "message": "Prompt不能为空"})

    try:
        _, _, _, model_path = run_pipeline(
            mode="Dual Image Fusion",
            quality=quality,
            prompt=prompt,
            img1=image1_path,
            img2=image2_path,
        )

        if model_path and os.path.exists(model_path):
            return json.dumps(
                {
                    "status": "success",
                    "model_path": model_path,
                    "message": "双图融合生3D模型成功！",
                }
            )
        else:
            return json.dumps(
                {"status": "error", "message": "生成完成但未找到模型文件"}
            )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"双图融合失败: {str(e)}"})
