# 3D Asset Generator - Complete Code Reference

## 智能改图功能实施完成！✅

### 完成清单

| 任务 | 状态 | 文件 |
|------|------|------|
| 移动工作流文件 | ✅ 完成 | 改图.json → backend/改图.json |
| 修改api_client.py | ✅ 完成 | improve_image_with_flux2klein() |
| 修改agent_core.py | ✅ 完成 | detect_intent_and_quality() |
| 修改agent_core.py | ✅ 完成 | run_smart_agent() |
| 语法检查 | ✅ 通过 | Python编译无错误 |

---

## 🎯 核心功能

### 1. 自然语言支持 ✅
- 支持中文："把材质改成金属"
- 支持英文："change material to metal"
- 智能理解用户需求

### 2. 多模态AI理解 ✅
- qwen-vl-max同时看图片和文字
- 综合分析图片内容、质量、用户需求
- 智能生成改图提示词

### 3. 智能决策逻辑 ✅
- need_improve字段控制是否改图
- reason字段说明改图原因
- 双重判断：用户需求 + 图片质量

### 4. 工作流优化 ✅
- Node 7 自动获取图片尺寸
- Node 8 自动适配Flux2Scheduler
- 无需手动设置尺寸

---

## 📊 工作流节点映射

| 功能 | 节点编号 | 说明 |
|------|----------|------|
| 图片输入 | Node 18 | LoadImage |
| 提示词 | Node 16 | CLIPTextEncode（支持自然语言） |
| 随机种子 | Node 13 | RandomNoise |
| 输出文件 | Node 19 | SaveImage |
| 自动尺寸 | Node 7 | GetImageSize |
| 尺寸适配 | Node 8 | Flux2Scheduler |
| 模型 | Node 17 | flux2klein（图片编辑） |

---

## Table of Contents

1. [frontend/gui.py](#1-frontendguipy)
2. [frontend/agent_core.py](#2-frontendagent_corepy)
3. [frontend/api_client.py](#3-frontendapi_clientpy)
4. [launcher.py](#4-launcherpy)
5. [config.ini](#5-configini)
6. [backend/改图.json](#6-backend改图json)
7. [启动脚本](#7-启动脚本)

---

## 1. frontend/gui.py

PyQt6 GUI界面，包含：
- 主窗口布局
- 模式选择（文生3D、图生3D、双图融合）
- 图片上传
- 3D预览（PyVista）
- 进度显示

---

## 2. frontend/agent_core.py

智能Agent核心模块：

### 主要函数
- `detect_intent_and_quality()` - 智能检测用户意图和图片质量
- `run_smart_agent()` - 主Agent入口，支持自然语言
- `encode_image_to_base64()` - 图片编码

### 工具注册表（6个工具）
1. `generate_3d` - 从图片生成3D
2. `analyze_geometry` - 分析几何参数
3. `improve_image` - 改进图片质量
4. `generate_3d_text` - 文生3D
5. `generate_3d_image` - 图生3D
6. `generate_3d_dual` - 双图融合

---

## 3. frontend/api_client.py

API客户端和工具函数：

### 主要函数
- `run_pipeline()` - 主工作流执行
- `improve_image_with_flux2klein()` - 改图功能（自动尺寸适配）
- `upload_image()` - 图片上传
- `queue_prompt()` - 任务队列

### 6个工具函数
- `tool_generate_3d()`
- `tool_analyze_geometry()`
- `tool_improve_image_flux2klein()`
- `tool_generate_3d_text()`
- `tool_generate_3d_image()`
- `tool_generate_3d_dual()`

---

## 4. launcher.py

启动器：
- 检测ComfyUI状态
- 自动启动后端
- 启动GUI
- 使用venv Python

---

## 5. config.ini

```ini
[Paths]
comfyuipath = E:/ComfyUI_windows_portable/ComfyUI
installdir = E:\bisai

[Agent]
dashscope_api_key = sk-xxxxxxxxxxxxxxxx
qwen_model = qwen3.5-plus
max_tool_iterations = 10
tool_timeout = 900
enable_auto_retry = true
retry_attempts = 3
```

---

## 6. backend/改图.json

FLUX2改图工作流JSON文件，支持自动尺寸：

| 节点 | 类型 | 功能 |
|------|------|------|
| 7 | GetImageSize | 自动获取图片尺寸 |
| 8 | Flux2Scheduler | 自动适配尺寸 |
| 13 | RandomNoise | 随机噪声 |
| 16 | CLIPTextEncode | 编码提示词（自然语言） |
| 17 | UnetLoaderGGUF | Flux2 Klein模型 |
| 18 | LoadImage | 加载原图 |
| 19 | SaveImage | 保存改进后图片 |
| 20 | CLIPLoader | 加载CLIP |
| 21 | VAELoader | 加载VAE |
| 22 | VAEEncode | 编码原图 |
| 23 | ConditioningZeroOut | 条件零化 |
| 24 | VAEDecode | VAE解码 |
| 25 | SamplerCustomAdvanced | 自定义采样器 |
| 26 | CFGGuider | CFG引导器 |
| 27 | KSamplerSelect | 采样器选择 |

---

## 7. 启动脚本

### 7.1 start_all.bat
一键启动全部（ComfyUI + Application）

### 7.2 start_app.bat
仅启动应用

### 7.3 start_comfyui.bat
仅启动ComfyUI后端

---

## 文件清单

### 核心Python文件
- `frontend/gui.py` - PyQt6 GUI界面
- `frontend/agent_core.py` - 智能Agent核心
- `frontend/api_client.py` - API客户端和工具函数
- `launcher.py` - 启动器

### 配置文件
- `config.ini` - 系统配置

### 工作流文件
- `backend/改图.json` - FLUX2改图工作流（自动尺寸）
- `backend/文生图片生模型.json` - 文生3D工作流
- `backend/图片生模型.json` - 图生3D工作流
- `backend/双图生图生模型.json` - 双图融合工作流

### 启动脚本
- `start_all.bat` - 一键启动全部
- `start_app.bat` - 启动应用
- `start_comfyui.bat` - 启动ComfyUI

---

**文档版本：** v3.0 - Smart Edition (智能改图功能完成)
**最后更新：** 2026-04-04