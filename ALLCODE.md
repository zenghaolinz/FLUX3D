# ALLCODE - 3D Asset Generator 完整代码文档

## 项目目的

**3D Asset Generator** 是一个基于 AI 的智能 3D 模型生成工具，旨在降低 3D 内容创作门槛，让普通用户无需专业建模技能即可快速生成高质量 3D 模型。

### 核心目标

1. **降低创作门槛** - 用户无需掌握 Blender/Maya 等专业软件
2. **多模态输入** - 支持文本描述、单张图片、双图融合三种输入方式
3. **智能辅助决策** - 集成 Qwen 多模态 AI 自动分析图片质量并优化
4. **专业级体验** - 类 Blender/VS Code 的深色主题界面

### 目标用户

- 游戏开发者（快速原型建模）
- 产品设计师（概念验证）
- 3D 打印爱好者（模型生成）
- 元宇宙内容创作者（资产生成）

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (PyQt6)                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ 左控制面板│  │ 中预览区│  │ 右AI面板│  │    设置/日志    │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └─────────────────┘ │
└───────┼────────────┼────────────┼───────────────────────────┘
        │            │            │
        ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                     应用逻辑层 (Python)                      │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │   launcher.py    │  │         agent_core.py            │ │
│  │   启动器/进程管理 │  │   Qwen API调用/意图分析/改图决策  │ │
│  └────────┬─────────┘  └───────────────┬──────────────────┘ │
└───────────┼────────────────────────────┼────────────────────┘
            │                            │
            ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API 客户端层 (api_client.py)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ HTTP/WebSocket│  │  工作流管理  │  │   工具函数封装   │   │
│  │  ComfyUI通信  │  │  JSON加载    │  │ tool_generate_3d │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    ComfyUI 后端引擎                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   FLUX.2     │  │  Hunyuan3D   │  │    RemBG等       │   │
│  │  图片生成模型 │  │  3D建模模型  │  │   预处理节点     │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入 → Agent分析意图 → 决策是否改图 → 调用工具函数 → 
ComfyUI执行工作流 → 返回中间结果 → 生成GLB模型 → UI展示
```

---

## 项目结构

```
E:\bisai\
│
├── frontend/                          # 前端应用层
│   ├── gui.py                         # 主界面模块 (962行)
│   │   ├── class MainWindow           # 主窗口
│   │   ├── class Worker               # 本地管线工作线程
│   │   ├── class SmartWorker          # 云端API工作线程
│   │   ├── class SettingsDialog       # 设置对话框
│   │   └── class LogWindow            # 日志窗口
│   │
│   ├── api_client.py                  # API客户端模块 (623行)
│   │   ├── run_pipeline()             # 核心工作流执行函数
│   │   ├── improve_image_with_flux2klein()  # FLUX2改图
│   │   └── tool_*()                   # 6个Agent工具函数
│   │
│   ├── agent_core.py                  # Agent核心模块 (489行)
│   │   ├── run_smart_agent()          # 智能Agent入口
│   │   ├── detect_intent_and_quality()  # 意图检测
│   │   └── TOOLS                      # 工具注册表
│   │
│   └── assets/icons/                  # UI图标资源 (8个PNG)
│       ├── settings.png               # 设置图标
│       ├── console.png                # 控制台图标
│       ├── play.png                   # 执行图标
│       ├── upload.png                 # 上传图标
│       ├── view_2d.png                # 2D视图图标
│       ├── view_3d.png                # 3D视图图标
│       ├── view_normal.png            # 法线视图图标
│             └── view_uv.png           # UV视图图标
│
├── backend/                           # ComfyUI后端层
│   ├── 文生图片生模型.json             # 文生3D工作流
│   ├── 图片生模型.json                # 图生3D工作流
│   ├── 双图生图生模型.json             # 双图融合工作流
│   ├── 改图.json                      # FLUX2改图工作流
│   │
│   ├── ComfyUI/                       # ComfyUI核心引擎
│   │   ├── comfy/                     # ComfyUI核心模块
│   │   ├── custom_nodes/              # 自定义节点
│   │   │   ├── ComfyUI-Hunyuan3DWrapper/  # Hunyuan3D节点
│   │   │   ├── ComfyUI-Manager/       # 节点管理器
│   │   │   └── comfyui-inpaint-nodes/ # 修复节点
│   │   └── blueprints/                # 工作流蓝图
│   │
│   ├── python_embeded/                # 内嵌Python环境
│   │   ├── python.exe                 # Python 3.12
│   │   ├── Lib/site-packages/         # 依赖包
│   │   └── *.dll                      # CUDA/运行时库
│   │
│   ├── update/                        # 更新脚本
│   └── advanced/                      # 高级配置
│
├── config.ini                         # 全局配置文件
│   ├── [Paths]                        # 路径配置
│   │   ├── comfyuipath                # ComfyUI路径
│   │   └── installdir                 # 安装目录
│   └── [Agent]                        # Agent配置
│       ├── dashscope_api_key          # API密钥 (sk-xxxxxx)
│       ├── qwen_model                 # 模型名称
│       └── max_tool_iterations        # 最大迭代次数
│
├── launcher.py                        # 应用启动器 (140行)
│   ├── get_config_paths()             # 读取配置路径
│   ├── start_comfyui()                # 启动ComfyUI
│   ├── wait_for_comfyui()             # 等待就绪
│   └── start_gui()                    # 启动GUI
│
├── start_app.bat                      # GUI启动脚本
├── start_all.bat                      # 完整启动脚本
├── start_comfyui.bat                  # ComfyUI启动脚本
│
├── requirements.txt                   # Python依赖列表
├── README.md                          # 用户说明文档
├── DEVELOPMENT.md                     # 开发文档
│
├── dist/                              # 打包输出目录
│   ├── AI3DGenerator_Source_v2.zip    # 源码包
│   └── AI3DGenerator_Compiled_v2.zip  # 编译包
│
├── .venv/                             # Python虚拟环境
├── .git/                              # Git版本控制
└── installer/                         # 安装包目录
```

---

## 核心模块详解

### 1. gui.py - 主界面模块 (962行)

**职责**: 提供用户交互界面，管理UI状态和用户操作

**主要类**:

| 类名 | 行数 | 功能 |
|------|------|------|
| `MainWindow` | 239-853 | 主窗口，三栏布局 |
| `Worker` | 205-236 | 本地管线后台线程 |
| `SmartWorker` | 173-202 | 云端API后台线程 |
| `SettingsDialog` | 855-913 | 设置对话框 |
| `LogWindow` | 916-943 | 系统日志窗口 |

**界面布局**:
```
┌──────────────────────────────────────────────────────────┐
│  [Logo]  3D资产生成器 v3.0          [设置] [控制台]      │
├──────────┬───────────────────────────┬──────────────────┤
│          │                           │                  │
│ 控制面板  │       3D预览区            │   AI对话面板     │
│          │  ┌─────────┐ ┌─────────┐  │                  │
│ ○智能计算 │  │2D预览   │ │法线贴图 │  │  [控制台输出]   │
│ ○文生3D  │  │         │ │         │  │                  │
│ ○图生3D  │  └─────────┘ └─────────┘  │  [API源资产]    │
│ ○双图融合 │  ┌─────────┐ ┌─────────┐  │                  │
│          │  │UV贴图   │ │3D视窗   │  │  [任务状态]     │
│ [质量]   │  │         │ │(PyVista)│  │                  │
│ ○草稿4B  │  └─────────┘ └─────────┘  │  [云端计算]     │
│ ○成品9B  │                           │                  │
│          │                           │                  │
│ [输入]   │                           │                  │
│ [状态]   │                           │                  │
│ [执行]   │                           │                  │
└──────────┴───────────────────────────┴──────────────────┘
```

**关键方法**:
```python
def _generate(self):           # 启动生成流程
def _update_visibility(self):  # 根据模式切换UI
def _load_model(self, widget, path):  # 加载GLB模型
def _on_qwen_message(self, msg):      # 处理AI消息
```

**主题配置**:
```python
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; color: #cccccc; }
QPushButton#primaryAction { background-color: #0e639c; }
QProgressBar::chunk { background-color: #0e639c; }
"""
```

---

### 2. api_client.py - API客户端模块 (623行)

**职责**: 与ComfyUI后端通信，管理工作流执行

**配置常量**:
```python
SERVER = "127.0.0.1:8188"
FLUX_FAST = "flux-2-klein-4b-Q4_K_M.gguf"
FLUX_QUALITY = "Flux-2-Klein-9B-KV-Q4_K_M.gguf"
```

**工作流映射**:
```python
WORKFLOWS = {
    "Text to 3D": "backend/文生图片生模型.json",
    "Image to 3D": "backend/图片生模型.json",
    "Dual Image Fusion": "backend/双图生图生模型.json",
}
```

**核心函数**:

| 函数名 | 行数 | 功能 |
|--------|------|------|
| `upload_image(path)` | 33-38 | 上传图片到ComfyUI |
| `queue_prompt(workflow)` | 41-57 | 提交工作流任务 |
| `run_pipeline(...)` | 101-286 | 执行完整工作流 |
| `improve_image_with_flux2klein(...)` | 298-377 | FLUX2改图 |

**Agent工具函数** (供智能体调用):

| 工具名 | 行数 | 功能 | 参数 |
|--------|------|------|------|
| `tool_generate_3d` | 387-423 | 图生3D | image_path |
| `tool_analyze_geometry` | 426-465 | 几何分析 | glb_path |
| `tool_improve_image_flux2klein` | 468-498 | 图片改进 | image_path, prompt |
| `tool_generate_3d_text` | 501-534 | 文生3D | prompt, quality |
| `tool_generate_3d_image` | 537-573 | 图生3D | image_path, quality |
| `tool_generate_3d_dual` | 576-623 | 双图融合 | image1, image2, prompt |

**工作流节点映射**:

```
文生图片生模型.json:
  Node 64: 文本输入
  Node 63: 随机种子
  Node 66: FLUX模型选择
  Node 62: 保存FLUX生成图
  Node 1:  RemBG去背景
  Node 42: 生成法线图
  Node 35: 生成UV贴图
  Node 47: 输出GLB模型
  Node 998/997/996: 临时保存节点

改图.json:
  Node 18: LoadImage (加载原图)
  Node 16: CLIPTextEncode (提示词编码)
  Node 13: RandomNoise (随机噪声)
  Node 19: SaveImage (保存结果)
```

---

### 3. agent_core.py - Agent核心模块 (489行)

**职责**: AI智能体协调，意图分析，改图决策

**配置读取**:
```python
DASHSCOPE_API_KEY = config.get("Agent", "dashscope_api_key")  # sk-xxxxxx
QWEN_MODEL = "qwen3.5-plus"
MAX_ITERATIONS = 10
```

**工具注册表**:
```python
TOOLS = {
    "generate_3d": {...},
    "analyze_geometry": {...},
    "improve_image": {...},
    "generate_3d_text": {...},
    "generate_3d_image": {...},
    "generate_3d_dual": {...},
}
```

**核心函数**:

| 函数名 | 行数 | 功能 |
|--------|------|------|
| `encode_image_to_base64(path)` | 127-130 | 图片Base64编码 |
| `detect_intent_and_quality(...)` | 133-322 | 意图检测+质量分析 |
| `run_smart_agent(...)` | 357-489 | 智能Agent入口 |

**智能Agent流程**:
```
1. Qwen分析图片 → detect_intent_and_quality()
   ↓
2. 决策是否改图
   ↓
   ├─ 需要 → improve_image_with_flux2klein()
   └─ 不需要 → 直接生成
   ↓
3. 调用 tool_generate_3d_image()
   ↓
4. 返回模型路径和预览图
```

**Qwen API调用**:
```python
client = OpenAI(
    api_key="sk-xxxxxx",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
response = client.chat.completions.create(
    model="qwen3.5-plus",
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": [
            {"type": "text", "text": "..."},
            {"type": "image_url", "image_url": {...}}
        ]}
    ]
)
```

---

### 4. launcher.py - 启动器模块 (140行)

**职责**: 应用启动，进程管理，依赖检查

**核心函数**:

| 函数名 | 行数 | 功能 |
|--------|------|------|
| `get_config_paths()` | 13-38 | 读取配置/注册表 |
| `is_port_in_use(port)` | 48-50 | 检测端口占用 |
| `start_comfyui()` | 53-106 | 启动ComfyUI后台 |
| `wait_for_comfyui(timeout)` | 109-117 | 等待ComfyUI就绪 |
| `start_gui()` | 120-132 | 启动GUI进程 |

**启动流程**:
```
1. 检测ComfyUI端口(8188)是否占用
   ↓
2. 未启动 → start_comfyui() 启动后台进程
   ↓
3. wait_for_comfyui() 等待就绪
   ↓
4. start_gui() 启动PyQt6界面
```

---

## 工作流节点映射

### 文生3D工作流 (文生图片生模型.json)

```
输入: text (用户描述)
      ↓
[Node 64] CLIPTextEncode - 文本编码
      ↓
[Node 63] RandomNoise - 随机种子
      ↓
[Node 66] UNET Loader - FLUX模型加载
      ↓
[Node 62] SaveImage - 保存FLUX生成图 (2D预览)
      ↓
[Node 1] RemBG - 去背景
      ↓
[Node 998] SaveImage - 保存去背景图
      ↓
[Node 42] NormalGenerator - 生成法线图
      ↓
[Node 997] SaveImage - 保存法线图
      ↓
[Node 35] UVGenerator - 生成UV贴图
      ↓
[Node 996] SaveImage - 保存UV贴图
      ↓
[Node 47] Hunyuan3D - 生成GLB模型
      ↓
输出: model.glb, preview_2d.png, normal.png, uv.png
```

### 图生3D工作流 (图片生模型.json)

```
输入: image (用户上传图片)
      ↓
[Node 71] LoadImage - 加载图片
      ↓
[Node 24/25] ImageResize - 调整尺寸
      ↓
[Node 1] RemBG - 去背景
      ↓
... 后续同文生3D ...
```

### 改图工作流 (改图.json)

```
输入: image, improvement_prompt
      ↓
[Node 18] LoadImage - 加载原图
      ↓
[Node 16] CLIPTextEncode - 编码提示词
      ↓
[Node 13] RandomNoise - 随机噪声
      ↓
[Node FLUX2] FLUX2Klein - 图片重绘
      ↓
[Node 19] SaveImage - 保存结果
      ↓
输出: improved_image.png
```

---

## 配置文件说明

### config.ini

```ini
[Paths]
comfyuipath = E:/ComfyUI_windows_portable/ComfyUI
installdir = E:\bisai

[Agent]
dashscope_api_key = sk-xxxxxx              # API密钥
qwen_model = qwen3.5-plus                  # 模型名称
max_tool_iterations = 10                   # 最大迭代次数
tool_timeout = 900                         # 工具超时(秒)
enable_auto_retry = true                   # 自动重试
retry_attempts = 3                         # 重试次数
```

---

## API端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `http://127.0.0.1:8188/prompt` | POST | 提交工作流 |
| `http://127.0.0.1:8188/history/{id}` | GET | 获取执行历史 |
| `http://127.0.0.1:8188/upload/image` | POST | 上传图片 |
| `ws://127.0.0.1:8188/ws?clientId={id}` | WebSocket | 实时进度 |

---

## 依赖项

**核心依赖**:
```
PyQt6>=6.10              # GUI框架
pyvista>=0.47            # 3D渲染
pyvistaqt>=0.11          # Qt集成
trimesh==4.11.4          # 网格处理
websocket-client>=1.8    # WebSocket通信
openai                   # Qwen API客户端
Pillow>=9.0.0            # 图片处理
requests>=2.28           # HTTP请求
```

**ComfyUI依赖**:
```
torch==2.6.0+cu126       # PyTorch CUDA
transformers==5.3.0      # Transformer模型
diffusers==0.37.0        # 扩散模型
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v3.0 | 2026-04 | 重构UI为三栏布局，专业深色主题，完整汉化 |
| v2.0 | 2026-03 | 集成Qwen API，智能改图决策 |
| v1.0 | 2026-02 | 基础功能实现 |

---

## 许可证

MIT License