import json
import urllib.request
import urllib.parse
import requests
import websocket
import uuid
import time
import os
import random
import shutil
from pathlib import Path

# ================= 配置区 =================
SERVER_ADDRESS = "127.0.0.1:8188"
CLIENT_ID = str(uuid.uuid4())
COMFYUI_OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"

# Gradio 临时目录
GRADIO_TEMP_DIR = os.path.join(os.path.dirname(__file__), "gradio_temp")
os.makedirs(GRADIO_TEMP_DIR, exist_ok=True)


# ==========================================

def copy_to_gradio_temp(source_path):
    """复制文件到 Gradio 临时目录，绕过路径验证"""
    if not source_path or not os.path.exists(source_path):
        return None
    
    # 生成唯一文件名（避免覆盖）
    filename = f"{uuid.uuid4()}_{os.path.basename(source_path)}"
    dest_path = os.path.join(GRADIO_TEMP_DIR, filename)
    
    # 复制文件
    try:
        shutil.copy2(source_path, dest_path)
        # 返回正斜杠路径
        return str(Path(dest_path).as_posix())
    except Exception as e:
        print(f"⚠️ 文件复制失败：{e}")
        return None

def upload_image_to_comfyui(image_path):
    with open(image_path, "rb") as f:
        files = {"image": f}
        response = requests.post(f"http://{SERVER_ADDRESS}/upload/image", files=files)
        if response.status_code == 200:
            return response.json()["name"]
        else:
            raise Exception("图片上传到 ComfyUI 失败！")


def queue_prompt(prompt_workflow):
    # 添加时间戳强制禁用 ComfyUI 缓存，确保每次都重新执行
    p = {
        "prompt": prompt_workflow,
        "client_id": CLIENT_ID,
        "extra_data": {
            "extra_pnginfo": {
                "timestamp": str(time.time())
            }
        }
    }
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        if "prompt_id" not in result:
            raise KeyError(f"ComfyUI 返回异常：{result}")
        return result
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"\n❌ [HTTP 错误] ComfyUI 拒绝请求:\n{error_msg}\n")
        raise Exception("任务发送失败，请看控制台。")


def get_history(prompt_id):
    with urllib.request.urlopen(f"http://{SERVER_ADDRESS}/history/{prompt_id}") as response:
        return json.loads(response.read())


# ComfyUI 临时目录（用于 Preview3D 等节点）
COMFYUI_TEMP_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\temp"
COMFYUI_3D_DIR = os.path.join(COMFYUI_OUTPUT_DIR, "3D")

def create_cross_layout_from_multi_view(multi_view_path, output_size=400):
    """
    将多视角法线贴图（6 合 1 横向排列）转换为十字展开布局
    
    假设输入图像是 6 个视角横向排列：[前，后，左，右，顶，底]
    输出十字展开（标准正方形 400x400）：
           [顶]
    [左][前][右][后]
           [底]
    """
    try:
        from PIL import Image
        
        # 打开输入图像
        img = Image.open(multi_view_path)
        width, height = img.size
        
        # 计算每个视角的尺寸（假设 6 个视角等宽横向排列）
        cell_width = width // 6
        cell_height = height
        
        # 裁剪出 6 个视角
        views = []
        view_names = ['front', 'back', 'left', 'right', 'top', 'bottom']
        for i in range(6):
            left = i * cell_width
            view = img.crop((left, 0, left + cell_width, cell_height))
            views.append((view_names[i], view))
        
        # 创建十字展开画布（标准正方形）
        # 布局：4 列 3 行
        # 每个视角的目标尺寸
        target_cell_size = output_size // 4  # 100x100
        
        result = Image.new('RGB', (output_size, output_size), color=(20, 20, 30))
        
        # 第 1 行：顶视图 (占据中间 2 列，即列 1-2)
        top_view = views[4][1].resize((target_cell_size * 2, target_cell_size), Image.Resampling.LANCZOS)
        result.paste(top_view, (target_cell_size, 0))
        
        # 第 2 行：左、前、右、后（4 个视角占满整行）
        left_view = views[2][1].resize((target_cell_size, target_cell_size), Image.Resampling.LANCZOS)
        front_view = views[0][1].resize((target_cell_size, target_cell_size), Image.Resampling.LANCZOS)
        right_view = views[3][1].resize((target_cell_size, target_cell_size), Image.Resampling.LANCZOS)
        back_view = views[1][1].resize((target_cell_size, target_cell_size), Image.Resampling.LANCZOS)
        
        result.paste(left_view, (0, target_cell_size))
        result.paste(front_view, (target_cell_size, target_cell_size))
        result.paste(right_view, (target_cell_size * 2, target_cell_size))
        result.paste(back_view, (target_cell_size * 3, target_cell_size))
        
        # 第 3 行：底视图 (占据中间 2 列，即列 1-2)
        bottom_view = views[5][1].resize((target_cell_size * 2, target_cell_size), Image.Resampling.LANCZOS)
        result.paste(bottom_view, (target_cell_size, target_cell_size * 2))
        
        # 保存十字展开图（标准 400x400 正方形）
        output_path = os.path.join(COMFYUI_TEMP_DIR, f"UI_cross_normal_{os.path.basename(multi_view_path)}")
        result.save(output_path)
        return output_path
        
    except Exception as e:
        print(f"创建十字展开法线贴图失败：{e}")
        import traceback
        traceback.print_exc()
        return None

def get_file_from_output_dir(filename_prefix, subfolder=""):
    """从 ComfyUI 输出目录直接查找文件（用于中间结果）"""
    import glob
    
    if subfolder:
        search_dir = os.path.join(COMFYUI_OUTPUT_DIR, subfolder)
    else:
        search_dir = COMFYUI_OUTPUT_DIR
    
    if not os.path.exists(search_dir):
        return None
    
    pattern = os.path.join(search_dir, f"{filename_prefix}*")
    files = glob.glob(pattern)
    
    if files:
        return max(files, key=os.path.getmtime)
    return None

def get_latest_glb_from_disk(pattern_prefix="Hy3D", exclude_textured=False):
    """从磁盘查找最新的 GLB 文件"""
    if not os.path.exists(COMFYUI_3D_DIR):
        return None
    
    import glob
    glb_files = glob.glob(os.path.join(COMFYUI_3D_DIR, f"{pattern_prefix}*.glb"))
    
    # 如果需要排除 textured 文件
    if exclude_textured:
        glb_files = [f for f in glb_files if 'textured' not in f]
    
    if glb_files:
        # 按修改时间排序，返回最新的
        return max(glb_files, key=os.path.getmtime)
    return None

def get_specific_glb_from_disk(pattern):
    """从磁盘查找匹配特定模式的 GLB 文件"""
    if not os.path.exists(COMFYUI_3D_DIR):
        return None
    
    import glob
    full_pattern = os.path.join(COMFYUI_OUTPUT_DIR, pattern)
    glb_files = glob.glob(full_pattern)
    
    if glb_files:
        # 返回最新的（通常只有一个）
        return max(glb_files, key=os.path.getmtime)
    return None

def get_file_from_history(history, node_id, output_dirs=None):
    """从 ComfyUI 的历史记录中提取文件（支持多种字段和目录）"""
    if node_id not in history['outputs']:
        return None
    
    node_output = history['outputs'][node_id]
    
    # 支持多种输出字段名（包括自定义节点和 Preview3D）
    for field_name in ['images', 'files', 'meshes', 'gltf_files', 'obj_files', 'file', 'result']:
        if field_name in node_output:
            data = node_output[field_name]
            
            # 情况 1：列表格式（包括 result 字段：['3D\\Hy3D_xxx.glb', None, None]）
            if isinstance(data, list) and len(data) > 0:
                # 特殊处理 result 字段：第一个元素是文件路径字符串
                if field_name == 'result' and isinstance(data[0], str):
                    filename = data[0]
                    # 处理反斜杠，统一为正斜杠
                    filename = filename.replace('\\', '/')
                    filepath = os.path.join(COMFYUI_OUTPUT_DIR, filename)
                    if os.path.exists(filepath):
                        return filepath
                
                # 标准格式：列表中包含字典
                for f in data:
                    if isinstance(f, dict) and 'filename' in f:
                        subfolder = f.get('subfolder', '')
                        filename = f['filename']
                        # 优先从 output 目录查找
                        filepath = os.path.join(COMFYUI_OUTPUT_DIR, subfolder, filename)
                        if os.path.exists(filepath):
                            return filepath
                        # 如果 output 没有，尝试 temp 目录
                        filepath = os.path.join(COMFYUI_TEMP_DIR, filename)
                        if os.path.exists(filepath):
                            return filepath
            
            # 情况 2：字典格式（Preview3D 可能使用）
            elif isinstance(data, dict):
                if 'filename' in data:
                    subfolder = data.get('subfolder', '')
                    filename = data['filename']
                    filepath = os.path.join(COMFYUI_OUTPUT_DIR, subfolder, filename)
                    if os.path.exists(filepath):
                        return filepath
                    # 尝试 temp 目录
                    filepath = os.path.join(COMFYUI_TEMP_DIR, filename)
                    if os.path.exists(filepath):
                        return filepath
                elif 'path' in data:
                    return data['path']
            
            # 情况 3：直接字符串路径
            elif isinstance(data, str):
                # 如果是绝对路径直接返回
                if os.path.isabs(data):
                    return data
                # 否则尝试从 temp 目录构建路径
                filepath = os.path.join(COMFYUI_TEMP_DIR, data)
                if os.path.exists(filepath):
                    return filepath
    
    return None


def run_comfyui_pipeline(mode, quality, prompt_text, image1_path, image2_path, progress=None, intermediate_callback=None):
    timestamp = int(time.time())
    file_prefix = f"UI_{timestamp}"
    
    flux_model_speed = "flux-2-klein-4b-Q4_K_M.gguf"
    flux_model_quality = "Flux-2-Klein-9B-KV-Q4_K_M.gguf"
    flux_model = flux_model_quality if quality == "quality" else flux_model_speed
    
    if "文生图再生" in mode:
        if not prompt_text or not prompt_text.strip():
            raise ValueError("❌ 文生图再生模式必须输入提示词！")
        workflow_path = r"E:\bisai\backend\文生图片生模型.json"
    elif "图生模型" in mode:
        if not image1_path:
            raise ValueError("❌ 图生模型模式必须上传参考图片！")
        workflow_path = r"E:\bisai\backend\图片生模型.json"
    elif "双图融合" in mode:
        if not prompt_text or not prompt_text.strip():
            raise ValueError("❌ 双图融合模式必须输入提示词！")
        if not image1_path:
            raise ValueError("❌ 双图融合模式必须上传参考图片 1！")
        if not image2_path:
            raise ValueError("❌ 双图融合模式必须上传参考图片 2！")
        workflow_path = r"E:\bisai\backend\双图生图生模型.json"
    else:
        raise ValueError(f"❌ 未知模式: {mode}")
    
    if progress: progress(0.05, desc="正在解析工作流引擎...")
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        prompt_workflow = json.load(f)
    
    if "文生图再生" in mode:
        if progress: progress(0.1, desc="文生图模式：FLUX.2 视觉引擎正在采样...")
        prompt_workflow["64"]["inputs"]["text"] = prompt_text
        prompt_workflow["63"]["inputs"]["noise_seed"] = random.randint(1, 10000000)
        prompt_workflow["66"]["inputs"]["unet_name"] = flux_model
        prompt_workflow["62"]["inputs"]["filename_prefix"] = f"{file_prefix}_Flux"
        prompt_workflow["18"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_White"
        prompt_workflow["34"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_Textured"
        
        prompt_workflow["998"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_RemBG",
                "images": ["1", 0]
            }
        }
        prompt_workflow["997"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Normal",
                "images": ["42", 0]
            }
        }
        prompt_workflow["996"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Texture",
                "images": ["35", 0]
            }
        }
        
        node_type_map = {
            '62': '2d',
            '998': '2d',
            '997': 'normal',
            '996': 'uv',
            '47': 'model'
        }
        
    elif "图生模型" in mode:
        if progress: progress(0.1, desc="图生模型模式：正在处理图片...")
        uploaded_filename = upload_image_to_comfyui(image1_path)
        prompt_workflow["71"]["inputs"]["image"] = uploaded_filename
        prompt_workflow["18"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_White"
        prompt_workflow["34"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_Textured"
        
        prompt_workflow["998"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_RemBG",
                "images": ["1", 0]
            }
        }
        prompt_workflow["997"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Normal",
                "images": ["42", 0]
            }
        }
        prompt_workflow["996"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Texture",
                "images": ["35", 0]
            }
        }
        
        node_type_map = {
            '998': '2d',
            '997': 'normal',
            '996': 'uv',
            '47': 'model'
        }
        
    elif "双图融合" in mode:
        if progress: progress(0.1, desc="双图融合模式：FLUX.2 正在融合生成...")
        uploaded_filename1 = upload_image_to_comfyui(image1_path)
        uploaded_filename2 = upload_image_to_comfyui(image2_path)
        prompt_workflow["74"]["inputs"]["image"] = uploaded_filename1
        prompt_workflow["75"]["inputs"]["image"] = uploaded_filename2
        prompt_workflow["73"]["inputs"]["text"] = prompt_text
        prompt_workflow["72"]["inputs"]["noise_seed"] = random.randint(1, 10000000)
        prompt_workflow["76"]["inputs"]["unet_name"] = flux_model
        prompt_workflow["63"]["inputs"]["filename_prefix"] = f"{file_prefix}_Flux"
        prompt_workflow["18"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_White"
        prompt_workflow["34"]["inputs"]["filename_prefix"] = f"3D/{file_prefix}_Textured"
        
        prompt_workflow["998"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_RemBG",
                "images": ["1", 0]
            }
        }
        prompt_workflow["997"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Normal",
                "images": ["42", 0]
            }
        }
        prompt_workflow["996"] = {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"{file_prefix}_Texture",
                "images": ["35", 0]
            }
        }
        
        node_type_map = {
            '63': '2d',
            '998': '2d',
            '997': 'normal',
            '996': 'uv',
            '47': 'model'
        }
    
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
    
    prompt_id = queue_prompt(prompt_workflow)['prompt_id']
    
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'progress':
                data = message['data']
                ratio = 0.1 + (data['value'] / data['max']) * 0.85
                desc_text = "AI 思考中..." if data['value'] < (data['max'] / 3) else "Hunyuan3D 重建中..."
                if progress: progress(ratio, desc=desc_text)
            
            if message['type'] == 'executing':
                data = message['data']
                node_id = str(data.get('node', ''))
                
                if node_id and node_id in node_type_map and intermediate_callback:
                    time.sleep(1.0)
                    
                    file_path = None
                    
                    if node_id == '998':
                        file_path = get_file_from_output_dir(f"{file_prefix}_RemBG")
                    elif node_id == '997':
                        file_path = get_file_from_output_dir(f"{file_prefix}_Normal")
                    elif node_id == '996':
                        file_path = get_file_from_output_dir(f"{file_prefix}_Texture")
                    elif node_id == '62':
                        file_path = get_file_from_output_dir(f"{file_prefix}_Flux")
                    elif node_id == '63':
                        file_path = get_file_from_output_dir(f"{file_prefix}_Flux")
                    elif node_id == '47':
                        try:
                            current_history = get_history(prompt_id)[prompt_id]
                            file_path = get_file_from_history(current_history, node_id)
                        except:
                            textured_pattern = f"3D/{file_prefix}_Textured*.glb"
                            file_path = get_specific_glb_from_disk(textured_pattern)
                    
                    if file_path and os.path.exists(file_path):
                        print(f"中间结果提取成功: {node_id} -> {file_path}")
                        intermediate_callback(node_type_map[node_id], file_path)
                
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
    
    if progress: progress(0.98, desc="渲染完毕，正在抓取资产...")
    time.sleep(1.5)
    
    history = get_history(prompt_id)[prompt_id]
    
    print("\n=== ComfyUI 输出历史调试 ===")
    print(f"模式: {mode}")
    print(f"Outputs 节点列表：{list(history['outputs'].keys())}")
    for nid, output in history['outputs'].items():
        print(f"  节点 {nid}: 字段 = {list(output.keys())}")
    print("========================\n")
    
    if "文生图再生" in mode:
        path_2d_preview = get_file_from_output_dir(f"{file_prefix}_Flux") or get_file_from_output_dir(f"{file_prefix}_RemBG")
        path_final_model = get_file_from_output_dir(f"{file_prefix}_Textured", "3D")
    elif "图生模型" in mode:
        path_2d_preview = image1_path
        path_final_model = get_file_from_output_dir(f"{file_prefix}_Textured", "3D")
    elif "双图融合" in mode:
        path_2d_preview = get_file_from_output_dir(f"{file_prefix}_Flux") or get_file_from_output_dir(f"{file_prefix}_RemBG")
        path_final_model = get_file_from_output_dir(f"{file_prefix}_Textured", "3D")
    
    path_normal_maps = get_file_from_output_dir(f"{file_prefix}_Normal")
    path_texture_map = get_file_from_output_dir(f"{file_prefix}_Texture")
    
    if not path_final_model:
        print("⚠️ 成品模型提取失败，尝试从磁盘查找...")
        textured_pattern = f"3D/{file_prefix}_Textured*.glb"
        path_final_model = get_specific_glb_from_disk(textured_pattern)
    
    print("\nExtracted file paths:")
    print(f"  2D preview: {path_2d_preview}")
    print(f"  Normal maps: {path_normal_maps}")
    print(f"  Texture map: {path_texture_map}")
    print(f"  Final model: {path_final_model}")
    print()
    
    return (
        path_2d_preview,
        path_normal_maps,
        path_texture_map,
        path_final_model
    )