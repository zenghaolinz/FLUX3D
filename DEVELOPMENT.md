# 3D Asset Generator 开发文档

## 项目概述

3D Asset Generator 是一个基于 AI 的 3D 模型生成工具，支持文生3D、图生3D、双图融合三种工作流模式。集成了 ComfyUI 后端和 Qwen 多模态 AI 进行智能图片分析与改图决策。

## 技术栈

- **前端框架**: PyQt6 + PyVistaQt (3D渲染)
- **后端引擎**: ComfyUI (本地部署)
- **AI模型**: FLUX2 (图片生成) + Hunyuan3D (3D建模)
- **智能分析**: Qwen3.5-plus 多模态模型
- **依赖管理**: Python 3.12 + venv

## 目录结构

```
E:\bisai\
├── frontend/                    # 前端应用
│   ├── gui.py                   # 主界面 (PyQt6)
│   ├── api_client.py            # ComfyUI API 客户端
│   ├── agent_core.py            # AI Agent 核心逻辑
│   └── assets/icons/            # 图标资源
│       ├── settings.png         # 设置图标
│       ├── console.png          # 控制台图标
│       ├── play.png             # 播放图标
│       ├── upload.png           # 上传图标
│       ├── view_2d.png          # 2D视图图标
│       ├── view_3d.png          # 3D视图图标
│       ├── view_normal.png      # 法线视图图标
│       └── view_uv.png          # UV视图图标
│
├── backend/                     # ComfyUI 后端
│   ├── 文生图片生模型.json       # 文生3D工作流
│   ├── 图片生模型.json          # 图生3D工作流
│   ├── 双图生图生模型.json       # 双图融合工作流
│   └── 改图.json                # FLUX2改图工作流
│
├── config.ini                   # 配置文件
├── launcher.py                  # 应用启动器
├── start_app.bat                # 启动脚本 (GUI)
├── start_all.bat               # 完整启动 (ComfyUI + GUI)
├── start_comfyui.bat           # 仅启动ComfyUI
└── requirements.txt            # Python依赖
```

## 核心模块

### 1. gui.py - 主界面模块

**主要类:**
- `MainWindow` - 主窗口类
- `WorkerThread` - 后台工作线程
- `SettingsDialog` - 设置对话框

**界面布局:**
```
┌──────────────────────────────────────────────────────────┐
│  [Logo]  3D资产生成器                    [设置] [控制台]  │
├──────────┬───────────────────────────┬──────────────────┤
│          │                           │                  │
│  控制面板 │        3D预览区           │    AI对话面板    │
│          │                           │                  │
│  ○ 文生3D│   [2D] [3D] [UV] [法线]  │   [对话历史]     │
│  ○ 图生3D│                           │   [输入框]       │
│  ○ 双图  │                           │   [发送]         │
│          │                           │                  │
│  [质量]  │                           │                  │
│  [提示词]│                           │                  │
│  [图片]  │                           │                  │
│          │                           │                  │
│  [生成]  │                           │                  │
│          │                           │                  │
├──────────┴───────────────────────────┴──────────────────┤
│  状态栏: 就绪 | 进度: 0%                                │
└──────────────────────────────────────────────────────────┘
```

**关键方法:**
```python
def generate(self)           # 启动生成流程
def load_image(self)         # 加载输入图片
def update_preview(path)     # 更新预览图像
def update_3d_view(glb_path) # 更新3D模型显示
```

### 2. api_client.py - API 客户端模块

**配置常量:**
```python
SERVER = "127.0.0.1:8188"     # ComfyUI服务地址
FLUX_FAST = "flux-2-klein-4b-Q4_K_M.gguf"      # 快速模型
FLUX_QUALITY = "Flux-2-Klein-9B-KV-Q4_K_M.gguf" # 质量模型
```

**工作流映射:**
```python
WORKFLOWS = {
    "Text to 3D": "backend/文生图片生模型.json",
    "Image to 3D": "backend/图片生模型.json",
    "Dual Image Fusion": "backend/双图生图生模型.json",
}
```

**核心函数:**
| 函数 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `upload_image(path)` | 上传图片到ComfyUI | 本地路径 | 服务器文件名 |
| `queue_prompt(workflow)` | 提交工作流任务 | JSON工作流 | prompt_id |
| `run_pipeline(...)` | 执行完整流程 | mode, prompt, images | 结果路径 |
| `tool_generate_3d_text(prompt)` | 文生3D工具 | 文字描述 | (glb, 2d, uv, normal) |
| `tool_generate_3d_image(path)` | 图生3D工具 | 图片路径 | (glb, 2d, uv, normal) |
| `tool_generate_3d_dual(p, i1, i2)` | 双图融合工具 | 提示词+双图 | (glb, 2d, uv, normal) |
| `tool_improve_image_flux2klein(path, prompt)` | 图片改进 | 图片+提示词 | 改进后图片 |

**节点映射 (改图.json):**
```
Node 18: LoadImage      - 加载原图
Node 16: CLIPTextEncode - 编码提示词
Node 13: RandomNoise    - 随机噪声种子
Node 19: SaveImage      - 保存结果
```

**节点映射 (文生图片生模型.json):**
```
Node 59: EmptyLatentImage - 空白潜空间 (需1024x1024)
Node 60: EmptyLatentImage - 空白潜空间 (需1024x1024)
Node 62: SaveImage        - 保存FLUX生成图
Node 47: 输出GLB模型
Node 1:  RemBG去背景
Node 42: 生成法线图
Node 35: 生成UV贴图
```

### 3. agent_core.py - AI Agent 模块

**配置读取:**
```python
DASHSCOPE_API_KEY = config.get("Agent", "dashscope_api_key")
QWEN_MODEL = "qwen3.5-plus"
MAX_ITERATIONS = 10
```

**工具注册表:**
```python
TOOLS = {
    "generate_3d": tool_generate_3d,
    "analyze_geometry": tool_analyze_geometry,
    "improve_image": tool_improve_image_flux2klein,
    "generate_3d_text": tool_generate_3d_text,
    "generate_3d_image": tool_generate_3d_image,
    "generate_3d_dual": tool_generate_3d_dual,
}
```

**核心函数:**
```python
def run_smart_agent(user_input, image_path=None, max_iter=10)
    # 主入口: 处理用户输入, 调用工具, 返回结果

def call_qwen_vision(image_path, prompt)
    # 调用Qwen多模态API分析图片

def decide_improvement(image_path, user_request)
    # 决策是否需要改图及改进方向
```

**Qwen API 调用示例:**
```python
client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
response = client.chat.completions.create(
    model="qwen3.5-plus",
    messages=[...],
    tools=tool_definitions
)
```

## 工作流说明

### 文生3D (Text to 3D)
1. 用户输入文字描述
2. FLUX2 生成初始图片 (Node 62)
3. RemBG 去背景 (Node 1)
4. Hunyuan3D 生成模型 (Node 47)
5. 返回 GLB + 预览图

### 图生3D (Image to 3D)
1. 用户上传图片
2. 自动调整尺寸适配
3. RemBG 去背景
4. Hunyuan3D 生成模型
5. 返回 GLB + 预览图

### 双图融合 (Dual Image Fusion)
1. 用户上传两张参考图
2. 输入融合描述词
3. FLUX2 混合生成新图
4. Hunyuan3D 生成模型
5. 返回 GLB + 预览图

### AI改图流程
1. Qwen 分析原图质量
2. 生成改进提示词
3. FLUX2 Klein 重绘图片
4. 返回改进后图片路径

## 配置文件

### config.ini
```ini
[Paths]
comfyuipath = E:/ComfyUI_windows_portable/ComfyUI
installdir = E:\bisai

[Agent]
dashscope_api_key = sk-xxxxx
qwen_model = qwen3.5-plus
max_tool_iterations = 10
tool_timeout = 900
enable_auto_retry = true
retry_attempts = 3
```

## 启动方式

```bash
# 仅启动GUI (需ComfyUI已运行)
start_app.bat

# 启动ComfyUI + GUI
start_all.bat

# 仅启动ComfyUI后端
start_comfyui.bat
```

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/prompt` | POST | 提交工作流 |
| `/history/{id}` | GET | 获取执行历史 |
| `/upload/image` | POST | 上传图片 |
| `/ws` | WebSocket | 实时进度推送 |

## 主题设计

采用专业深色主题 (VS Code/Blender 风格):
- 背景色: `#1e1e1e`
- 面板色: `#252526`
- 边框色: `#3c3c3c`
- 强调色: `#007acc`
- 文字色: `#cccccc`
- 次要文字: `#999999`

## 扩展开发

### 添加新工作流
1. 在 ComfyUI 中设计工作流
2. 导出为 JSON 到 `backend/`
3. 在 `api_client.py` 中添加到 `WORKFLOWS` 字典
4. 实现对应的 `tool_xxx` 函数

### 添加新工具
1. 在 `api_client.py` 中实现工具函数
2. 在 `agent_core.py` 的 `TOOLS` 中注册
3. 定义工具描述和参数 schema

### 修改UI
1. 修改 `gui.py` 中的布局和控件
2. 样式定义在 `STYLESHEET` 常量中
3. 图标放在 `frontend/assets/icons/`

## 常见问题

**Q: ComfyUI 连接失败**
A: 检查 `config.ini` 中的路径配置，确保 ComfyUI 服务已启动

**Q: 图片生成尺寸不匹配**
A: 文生图片生模型.json 的 Node 59/60 需要设置为 1024x1024

**Q: 改图节点ID错误**
A: 改图.json 使用 Node 18/16/13/19，参考 `tool_improve_image_flux2klein()`

## 版本历史

- v2.0.0 - 重构UI为三栏布局，专业深色主题，完整汉化
- v1.x - 初始版本，基础功能实现