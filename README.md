# 3D Asset Generator

基于 FLUX.2 和 Hunyuan3D 的文本/图片生成 3D 模型工具。

## 功能

- 文生 3D：根据文字描述生成 3D 模型
- 图生 3D：上传图片直接生成 3D 模型（保留原图尺寸）
- 双图融合：两张图片 + 提示词融合生成

## 环境要求

- Python 3.10+
- ComfyUI（需安装 FLUX.2 和 Hunyuan3D 节点）
- NVIDIA GPU

## 安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 使用

先启动 后端（端口 8188），然后运行：

```bash
python launcher.py
```

或直接运行 GUI：

```bash
.venv\Scripts\python frontend\gui.py
```

## 配置

修改 `frontend/api_client.py`：

```python
SERVER = "127.0.0.1:8188"
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
```

## 模型文件

FLUX.2 GGUF 模型放在  `models/unet/` 目录：

- `flux-2-klein-4b-Q4_K_M.gguf` - 快速模式
- `Flux-2-Klein-9B-KV-Q4_K_M.gguf` - 质量模式

## License

MIT