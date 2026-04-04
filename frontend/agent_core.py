"""
Agent核心模块 - 智能对话体协调器
支持自然语言理解、多模态AI分析、智能改图决策
"""

import json
import os
import sys
import configparser
import base64
from openai import OpenAI

# 读取配置
config = configparser.ConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini"),
    encoding="utf-8",
)

DASHSCOPE_API_KEY = config.get("Agent", "dashscope_api_key", fallback="")
QWEN_MODEL = config.get("Agent", "qwen_model", fallback="qwen3.5-plus")
MAX_ITERATIONS = config.getint("Agent", "max_tool_iterations", fallback=10)

# 导入工具函数
from api_client import (
    tool_generate_3d,
    tool_analyze_geometry,
    tool_improve_image_flux2klein,
    tool_generate_3d_text,
    tool_generate_3d_image,
    tool_generate_3d_dual,
    improve_image_with_flux2klein,
)

# 工具注册表
TOOLS = {
    "generate_3d": {
        "function": tool_generate_3d,
        "description": "从图片生成3D模型。输入图片路径，输出模型路径。",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "图片文件的绝对路径"}
            },
            "required": ["image_path"],
        },
    },
    "analyze_geometry": {
        "function": tool_analyze_geometry,
        "description": "分析3D模型的几何参数，包括体积、表面积、包围盒等。",
        "parameters": {
            "type": "object",
            "properties": {
                "glb_path": {"type": "string", "description": "GLB模型文件的路径"}
            },
            "required": ["glb_path"],
        },
    },
    "improve_image": {
        "function": tool_improve_image_flux2klein,
        "description": "使用FLUX2改进图片质量，使其更适合3D建模。",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "原图路径"},
                "improvement_prompt": {
                    "type": "string",
                    "description": "改进提示词（英文）",
                },
            },
            "required": ["image_path", "improvement_prompt"],
        },
    },
    "generate_3d_text": {
        "function": tool_generate_3d_text,
        "description": "从文字描述生成3D模型。",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "文字描述"},
                "quality": {
                    "type": "string",
                    "enum": ["fast", "quality"],
                    "description": "生成质量",
                },
            },
            "required": ["prompt"],
        },
    },
    "generate_3d_image": {
        "function": tool_generate_3d_image,
        "description": "从单张图片生成3D模型。",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "图片路径"},
                "quality": {
                    "type": "string",
                    "enum": ["fast", "quality"],
                    "description": "生成质量",
                },
            },
            "required": ["image_path"],
        },
    },
    "generate_3d_dual": {
        "function": tool_generate_3d_dual,
        "description": "从两张图片融合生成3D模型。",
        "parameters": {
            "type": "object",
            "properties": {
                "image1_path": {"type": "string", "description": "图片1路径"},
                "image2_path": {"type": "string", "description": "图片2路径"},
                "prompt": {"type": "string", "description": "融合提示词"},
                "quality": {
                    "type": "string",
                    "enum": ["fast", "quality"],
                    "description": "生成质量",
                },
            },
            "required": ["image1_path", "image2_path", "prompt"],
        },
    },
}


def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def detect_intent_and_quality(
    user_input: str = "", image_paths: list = None, callback=None
) -> dict:
    """
    智能检测用户意图和图片质量

    Args:
        user_input: 用户输入（支持中英文，可为空）
        image_paths: 图片路径列表
        callback: 回调函数

    Returns:
        {
            "need_improve": bool,     # 是否需要改图
            "suitable_for_3d": bool,  # 图片是否适合3D生成
            "reason": str,            # 改图原因
            "improve_prompt": str,    # 改图提示词（英文）
            "quality": str,           # fast/quality
            "intent": str             # 用户意图
        }
    """
    if not DASHSCOPE_API_KEY:
        return {
            "need_improve": False,
            "suitable_for_3d": True,
            "reason": "未配置API Key",
            "improve_prompt": "",
            "quality": "fast",
            "intent": "unknown",
        }

    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 根据是否有用户输入，选择不同的系统提示词
    if user_input and user_input.strip():
        system_content = """你是一个专业的图片分析和改图决策助手。

## 任务
分析图片和用户需求，生成改图提示词。

## 输出格式（JSON）
{
    "need_improve": true,
    "suitable_for_3d": true/false,
    "reason": "改图原因说明",
    "improve_prompt": "英文改图提示词",
    "quality": "fast",
    "intent": "用户意图描述"
}

## 决策规则
用户有明确需求时，必须生成改图提示词：
- 提示词要准确反映用户需求（如"改成金属"→"transform to metallic material, high polish"）
- 保持原图主体不变，只修改用户要求的部分
- improve_prompt 必须是英文

请只输出JSON，不要有其他内容。"""
        user_text = user_input
    else:
        system_content = """你是一个专业的图片质量分析助手。

## 任务
分析图片是否适合直接生成3D模型。

## 输出格式（JSON）
{
    "need_improve": true/false,
    "suitable_for_3d": true/false,
    "reason": "原因说明",
    "improve_prompt": "英文改图提示词（如果需要改图）",
    "quality": "fast",
    "intent": "图生3D"
}

## 决策规则
1. suitable_for_3d = true 的情况：
   - 图片清晰、主体明确
   - 光线均匀、细节丰富
   - 适合直接提取3D几何

2. suitable_for_3d = false 的情况：
   - 图片模糊、分辨率低
   - 光线差、阴影过多
   - 细节不足、边缘不清
   - 需要 improve_prompt 来改进图片

3. need_improve 与 suitable_for_3d 相反

请只输出JSON，不要有其他内容。"""
        user_text = "请分析这张图片是否适合直接生成3D模型，如果不适合请给出改图建议。"

    # 构建消息
    messages = [{"role": "system", "content": system_content}]

    # 添加用户消息
    user_message = {"role": "user", "content": [{"type": "text", "text": user_text}]}

    # 如果有图片，使用多模态模型分析
    if image_paths and len(image_paths) > 0:
        for i, path in enumerate(image_paths[:2]):
            if os.path.exists(path):
                try:
                    base64_image = encode_image_to_base64(path)
                    user_message["content"].append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        }
                    )
                except Exception as e:
                    if callback:
                        callback(
                            json.dumps(
                                {"type": "WARNING", "content": f"图片编码失败: {e}"}
                            )
                        )

    messages.append(user_message)

    try:
        if callback:
            callback(
                json.dumps({"type": "INFO", "content": "正在分析用户意图和图片质量..."})
            )

        # 使用多模态模型
        response = client.chat.completions.create(
            model="qwen3.5-plus",  # 多模态模型
            messages=messages,
            temperature=0.3,
        )

        result_text = response.choices[0].message.content.strip()

        # 解析JSON结果
        # 尝试提取JSON部分
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        if callback:
            callback(
                json.dumps(
                    {
                        "type": "ANALYSIS",
                        "content": f"意图分析: {result.get('intent', 'unknown')}",
                    }
                )
            )
            callback(
                json.dumps(
                    {
                        "type": "DECISION",
                        "content": f"改图决策: {'需要' if result.get('need_improve') else '不需要'} - {result.get('reason', '')}",
                    }
                )
            )

        return result

    except json.JSONDecodeError as e:
        if callback:
            callback(json.dumps({"type": "ERROR", "content": f"JSON解析失败: {e}"}))
        return {
            "need_improve": False,
            "suitable_for_3d": True,
            "reason": "解析失败",
            "improve_prompt": "",
            "quality": "fast",
            "intent": "unknown",
        }
    except Exception as e:
        if callback:
            callback(json.dumps({"type": "ERROR", "content": f"意图检测失败: {e}"}))
        return {
            "need_improve": False,
            "suitable_for_3d": True,
            "reason": f"检测失败: {e}",
            "improve_prompt": "",
            "quality": "fast",
            "intent": "unknown",
        }


def get_system_prompt():
    """生成系统提示词"""
    tools_desc = []
    for name, tool in TOOLS.items():
        tools_desc.append(f"- {name}: {tool['description']}")

    return f"""你是一个专业的3D资产生成助手。你可以使用以下工具来帮助用户：

{chr(10).join(tools_desc)}

## 工作流程
1. 分析用户需求，确定需要使用哪些工具
2. 按顺序调用工具，每次调用后等待结果
3. 根据结果决定下一步操作
4. 最终向用户报告结果

## 重要规则
- 每次只调用一个工具
- 调用工具时使用JSON格式: {{"tool": "工具名", "parameters": {{"参数": "值"}}}}
- 等待工具返回结果后再继续
- 如果工具返回错误，尝试其他方案或向用户说明

## 输出格式
当需要调用工具时，输出：
[TOOL_CALL]
{{"tool": "xxx", "parameters": {{...}}}}
[/TOOL_CALL]

其他时候正常对话即可。
"""


def run_smart_agent(user_input: str = "", image_paths: list = None, callback=None):
    """
    运行智能Agent - 简化流程

    Args:
        user_input: 用户输入（支持中英文自然语言，可为空）
        image_paths: 图片路径列表
        callback: 消息回调函数

    Returns:
        最终模型路径
    """
    if not DASHSCOPE_API_KEY:
        if callback:
            callback(
                json.dumps(
                    {
                        "type": "ERROR",
                        "content": "未配置API Key，请在config.ini中设置dashscope_api_key",
                    }
                )
            )
        return None

    if not image_paths or len(image_paths) == 0:
        if callback:
            callback(json.dumps({"type": "ERROR", "content": "请上传图片"}))
        return None

    current_image = image_paths[0]

    # Step 1: Qwen分析图片
    if callback:
        callback(json.dumps({"type": "INFO", "content": "🔍 正在智能分析图片..."}))

    analysis = detect_intent_and_quality(user_input, [current_image], callback)

    suitable = analysis.get("suitable_for_3d", True)
    need_improve = analysis.get("need_improve", False)
    reason = analysis.get("reason", "")
    improve_prompt = analysis.get("improve_prompt", "")

    if callback:
        callback(
            json.dumps(
                {
                    "type": "ANALYSIS",
                    "content": f"图片分析: {'适合3D生成' if suitable else '不适合直接生成3D'}",
                }
            )
        )
        callback(json.dumps({"type": "DECISION", "content": f"决策: {reason}"}))

    # Step 2: 如果需要改图，执行改图
    if not suitable or need_improve:
        if improve_prompt:
            if callback:
                callback(
                    json.dumps(
                        {"type": "INFO", "content": f"✨ 正在改进图片: {reason}"}
                    )
                )

            try:
                improved_path = improve_image_with_flux2klein(
                    current_image,
                    improve_prompt,
                    progress=lambda v, d: (
                        callback(
                            json.dumps(
                                {
                                    "type": "PROGRESS",
                                    "content": f"{d} ({int(v * 100)}%)",
                                }
                            )
                        )
                        if callback
                        else None
                    ),
                )

                if improved_path and os.path.exists(improved_path):
                    current_image = improved_path
                    if callback:
                        callback(
                            json.dumps({"type": "PREVIEW_2D", "content": improved_path})
                        )
                        callback(
                            json.dumps(
                                {"type": "SUCCESS", "content": f"✅ 图片改进完成"}
                            )
                        )
            except Exception as e:
                if callback:
                    callback(
                        json.dumps({"type": "WARNING", "content": f"图片改进失败: {e}"})
                    )

    # Step 3: 直接生图（不走对话循环）
    if callback:
        callback(json.dumps({"type": "INFO", "content": "🎲 正在生成3D模型..."}))

    result_json = tool_generate_3d_image(current_image)
    result = json.loads(result_json)

    if result.get("status") == "success":
        model_path = result.get("model_path")
        image_2d = result.get("image_2d")
        image_normal = result.get("image_normal")
        image_uv = result.get("image_uv")

        if callback:
            # 发送预览图路径给GUI
            if image_2d:
                callback(json.dumps({"type": "PREVIEW_2D", "content": image_2d}))
            if image_normal:
                callback(
                    json.dumps({"type": "PREVIEW_NORMAL", "content": image_normal})
                )
            if image_uv:
                callback(json.dumps({"type": "PREVIEW_UV", "content": image_uv}))

            callback(json.dumps({"type": "MODEL_READY", "content": model_path}))
            callback(json.dumps({"type": "DONE", "content": "🎉 3D模型生成完成"}))
        return model_path
    else:
        if callback:
            callback(
                json.dumps(
                    {"type": "ERROR", "content": result.get("message", "生成失败")}
                )
            )
        return None
