import gradio as gr
import os
from pathlib import Path
from api_client import run_comfyui_pipeline

# -------------------------------------------------------------------
# UI 核心布局与逻辑设定
# -------------------------------------------------------------------


# 2. 动态切换输入框的函数 (根据用户选择的模式，显示文本框或图片上传框)
def toggle_inputs(mode):
    if "文生" in mode:
        return gr.update(visible=True), gr.update(visible=False)
    else:
        return gr.update(visible=False), gr.update(visible=True)


# 3. 搭建前端 Blocks 架构
with gr.Blocks(title="湖工大智造：AI 全链路 3D 建模平台") as demo:
    # 【头部标题区】
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #2b6cb0; font-weight: 800; font-size: 2.2em;">💠 AI 全链路 3D 建模工作站 (双模版)</h1>
        <p style="color: #4a5568; font-size: 1.1em;">FLUX.2 视觉生成引擎 ✖️ Hunyuan3D V2.0 多视角拓扑重建</p>
    </div>
    """)

    with gr.Row():
        # ⬅️ 左侧栏：参数输入区
        with gr.Column(scale=1, variant="panel"):
            gr.Markdown("### ⚙️ 创作控制台")

            # 【核心功能】：模式选择器
            input_mode = gr.Radio(
                choices=["文生3D (文本生成模型)", "图生3D (图片生成模型)"],
                value="文生3D (文本生成模型)",
                label="1. 选择生成模式",
                interactive=True
            )

            # 文本输入区 (默认在文生模式下显示)
            with gr.Column(visible=True) as text_col:
                input_prompt = gr.Textbox(
                    label="2. 创意描述 (Prompt)",
                    lines=4,
                    placeholder="输入详细描述，AI 将先生成高清 2D 图像，再进行 3D 建模...\n例如：一个极具未来感的赛博朋克风格工业机械零件"
                )

            # 图片输入区 (默认在图生模式下隐藏)
            with gr.Column(visible=False) as img_col:
                input_image = gr.Image(
                    label="2. 上传参考图 (自动进行 InSPyReNet 高精度去背)",
                    type="filepath",
                    height=250
                )

            # 绑定单选框的切换事件，实现所见即所得的动态 UI
            input_mode.change(
                fn=toggle_inputs,
                inputs=input_mode,
                outputs=[text_col, img_col]
            )

            generate_btn = gr.Button("🚀 启动 3D 生成引擎", variant="primary", size="lg")

        # ➡️ 右侧栏：成果展示区 (四宫格展示)
        with gr.Column(scale=2):
            gr.Markdown("### 📊 资产生成全景视图 (Pipeline)")

            with gr.Row():
                # 阶段 1：2D 原图或去背图
                with gr.Column(variant="panel"):
                    out_2d_preview = gr.Image(label="1️⃣ 2D 预览 (文生原图 / 图生去背图)", interactive=False,
                                              height=280)
                # 阶段 2：3D 白模
                with gr.Column(variant="panel"):
                    out_white_model = gr.Model3D(label="2️⃣ 白模展示 (几何拓扑)", interactive=False, height=280,
                                                 clear_color=[0, 0, 0, 0])

            with gr.Row():
                # 阶段 3：展开的 UV 贴图
                with gr.Column(variant="panel"):
                    out_texture_map = gr.Image(label="3️⃣ 贴图展示 (UV 展开与修复)", interactive=False, height=350)
                # 阶段 4：最终成品
                with gr.Column(variant="panel"):
                    out_final_model = gr.Model3D(label="4️⃣ 成品展示 (高质量带纹理 3D)", interactive=False, height=350,
                                                 clear_color=[0, 0, 0, 0])

    # -------------------------------------------------------------------
    # 事件绑定逻辑：将界面的输入发给后端的 API 脚本
    # -------------------------------------------------------------------
    generate_btn.click(
        fn=run_comfyui_pipeline,
        inputs=[input_mode, input_prompt, input_image],
        outputs=[out_2d_preview, out_white_model, out_texture_map, out_final_model],
        show_progress="full"
    )

# -------------------------------------------------------------------
# 启动服务
# -------------------------------------------------------------------
if __name__ == "__main__":
    # 获取 gradio_temp 目录的绝对路径
    gradio_temp_path = os.path.join(os.path.dirname(__file__), "gradio_temp")
    os.makedirs(gradio_temp_path, exist_ok=True)
    
    print("System starting...")
    print(f"  Gradio temp dir: {os.path.abspath(gradio_temp_path)}")
    print(f"  Allowed paths: {os.getcwd()}, E:/, C:/")

    # 终极启动指令 - 授权当前目录、临时目录和磁盘根目录
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        allowed_paths=[
            os.getcwd(),
            gradio_temp_path,
            "E:/",
            "C:/"
        ] 
    )