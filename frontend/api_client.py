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
        "extra_data": {"extra_pnginfo": {"ts": str(time.time())}}
    }
    data = json.dumps(payload).encode('utf-8')
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
    """Find latest file by prefix in output dir"""
    search_dir = os.path.join(OUTPUT_DIR, subfolder) if subfolder else OUTPUT_DIR
    if not os.path.exists(search_dir):
        return None
    pattern = os.path.join(search_dir, f"{prefix}*")
    files = glob.glob(pattern)
    return max(files, key=os.path.getmtime) if files else None


def extract_file(history, node_id):
    """Extract file from ComfyUI history output"""
    if node_id not in history.get('outputs', {}):
        return None
    
    out = history['outputs'][node_id]
    for field in ['images', 'files', 'result']:
        if field not in out:
            continue
        data = out[field]
        
        if isinstance(data, list) and len(data) > 0:
            if field == 'result' and isinstance(data[0], str):
                path = os.path.join(OUTPUT_DIR, data[0].replace('\\', '/'))
                return path if os.path.exists(path) else None
            
            for item in data:
                if isinstance(item, dict) and 'filename' in item:
                    sub = item.get('subfolder', '')
                    path = os.path.join(OUTPUT_DIR, sub, item['filename'])
                    if os.path.exists(path):
                        return path
                    path = os.path.join(TEMP_DIR, item['filename'])
                    if os.path.exists(path):
                        return path
    return None


def run_pipeline(mode, quality, prompt, img1, img2=None, progress=None, intermediate_callback=None):
    ts = int(time.time())
    prefix = f"UI_{ts}"
    
    flux_model = FLUX_QUALITY if quality == "quality" else FLUX_FAST
    
    # Load workflow
    if mode not in WORKFLOWS:
        raise ValueError(f"Unknown mode: {mode}")
    
    with open(WORKFLOWS[mode], 'r', encoding='utf-8') as f:
        wf = json.load(f)
    
    if progress:
        progress(0.05, "Loading workflow...")
    
    # Inject parameters based on mode
    if mode == "Text to 3D":
        if not prompt:
            raise ValueError("Prompt required")
        wf["64"]["inputs"]["text"] = prompt
        wf["63"]["inputs"]["noise_seed"] = random.randint(1, 10000000)
        wf["66"]["inputs"]["unet_name"] = flux_model
        wf["62"]["inputs"]["filename_prefix"] = f"{prefix}_Flux"
        wf["18"]["inputs"]["filename_prefix"] = f"3D/{prefix}_White"
        wf["34"]["inputs"]["filename_prefix"] = f"3D/{prefix}_Textured"
        
        # Add intermediate save nodes
        wf["998"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]}}
        wf["997"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]}}
        wf["996"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]}}
        
        node_map = {'62': '2d', '998': '2d', '997': 'normal', '996': 'uv', '47': 'model'}
    
    elif mode == "Image to 3D":
        if not img1:
            raise ValueError("Image required")
        uploaded = upload_image(img1)
        wf["71"]["inputs"]["image"] = uploaded
        wf["18"]["inputs"]["filename_prefix"] = f"3D/{prefix}_White"
        wf["34"]["inputs"]["filename_prefix"] = f"3D/{prefix}_Textured"
        
        wf["998"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]}}
        wf["997"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]}}
        wf["996"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]}}
        
        node_map = {'998': '2d', '997': 'normal', '996': 'uv', '47': 'model'}
    
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
        
        wf["998"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_RemBG", "images": ["1", 0]}}
        wf["997"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Normal", "images": ["42", 0]}}
        wf["996"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": f"{prefix}_Texture", "images": ["35", 0]}}
        
        node_map = {'63': '2d', '998': '2d', '997': 'normal', '996': 'uv', '47': 'model'}
    
    # Connect websocket
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER}/ws?clientId={CLIENT_ID}")
    
    pid = queue_prompt(wf)['prompt_id']
    
    # Listen for progress
    while True:
        msg = ws.recv()
        if isinstance(msg, str):
            data = json.loads(msg)
            
            if data.get('type') == 'progress':
                d = data['data']
                pct = 0.1 + (d['value'] / d['max']) * 0.85
                desc = "Processing..." if d['value'] < d['max'] / 3 else "Building 3D..."
                if progress:
                    progress(pct, desc)
            
            elif data.get('type') == 'executing':
                d = data['data']
                nid = str(d.get('node', ''))
                
                if nid and nid in node_map and intermediate_callback:
                    time.sleep(1.0)
                    
                    fpath = None
                    if nid == '998':
                        fpath = find_file(f"{prefix}_RemBG")
                    elif nid == '997':
                        fpath = find_file(f"{prefix}_Normal")
                    elif nid == '996':
                        fpath = find_file(f"{prefix}_Texture")
                    elif nid in ('62', '63'):
                        fpath = find_file(f"{prefix}_Flux")
                    elif nid == '47':
                        try:
                            hist = get_history(pid)[pid]
                            fpath = extract_file(hist, nid)
                        except:
                            fpath = find_file(f"{prefix}_Textured", "3D")
                    
                    if fpath and os.path.exists(fpath):
                        print(f"[intermediate] {nid}: {fpath}")
                        intermediate_callback(node_map[nid], fpath)
                
                if d.get('node') is None and d.get('prompt_id') == pid:
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
    
    print(f"\nResults:")
    print(f"  2D: {result_2d}")
    print(f"  Normal: {result_normal}")
    print(f"  UV: {result_uv}")
    print(f"  Model: {result_model}")
    
    return result_2d, result_normal, result_uv, result_model


# Keep old function name for compatibility
run_comfyui_pipeline = run_pipeline