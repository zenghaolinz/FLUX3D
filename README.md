# 3D Asset Generator

FLUX.2 + Hunyuan3D text/image to 3D model pipeline.

## Features

- Text to 3D: Generate 3D models from text prompts
- Image to 3D: Convert images to 3D models  
- Dual Image Fusion: Merge two images with prompt

## Requirements

- Python 3.10+
- ComfyUI with FLUX.2 and Hunyuan3D nodes
- NVIDIA GPU (CUDA)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

1. Start ComfyUI first (port 8188)
2. Run launcher:

```bash
python launcher.py
```

Or run GUI directly:

```bash
.venv\Scripts\python frontend\gui.py
```

## Workflow Files

Place workflow JSON files in `backend/`:
- `文生图片生模型.json` - Text to 3D
- `图片生模型.json` - Image to 3D
- `双图生图生模型.json` - Dual Image Fusion

## Config

Edit `frontend/api_client.py` to change:

```python
SERVER = "127.0.0.1:8188"
OUTPUT_DIR = r"E:\ComfyUI_windows_portable\ComfyUI\output"
```

## License

MIT