import sys
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QProgressBar,
    QRadioButton, QButtonGroup, QFrame, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

import pyvista as pv
from pyvistaqt import QtInteractor

from api_client import run_comfyui_pipeline


class WorkerThread(QThread):
    """后台工作线程，执行 ComfyUI 调用"""
    progress_signal = pyqtSignal(float, str)
    intermediate_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(object, object, object, object)
    error_signal = pyqtSignal(str)
    
    def __init__(self, mode, quality, prompt_text, image1_path, image2_path=None):
        super().__init__()
        self.mode = mode
        self.quality = quality
        self.prompt_text = prompt_text
        self.image1_path = image1_path
        self.image2_path = image2_path
    
    def run(self):
        try:
            def progress_callback(value, desc):
                self.progress_signal.emit(value, desc)
            
            def intermediate_callback(file_type, file_path):
                self.intermediate_signal.emit(file_type, file_path)
            
            result = run_comfyui_pipeline(
                self.mode,
                self.quality,
                self.prompt_text, 
                self.image1_path,
                self.image2_path,
                progress=progress_callback,
                intermediate_callback=intermediate_callback
            )
            self.finished_signal.emit(*result)
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D 建模")
        self.setMinimumSize(1400, 900)
        
        self.current_image1_path = None
        self.current_image2_path = None
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === 标题区 ===
        title_label = QLabel(" 3D 建模")
        title_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #2b6cb0;
            padding: 10px;
        """)
        subtitle_label = QLabel("FLUX.2 视觉生成引擎 ️  多视角拓扑重建")
        subtitle_label.setStyleSheet("font-size: 14px; color: #4a5568; padding-left: 10px;")
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        
        mode_label = QLabel("生成模式:")
        mode_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(mode_label)
        
        self.mode_group = QButtonGroup()
        self.radio_text2img = QRadioButton("文生图再生模型 (提示词→图片→模型)")
        self.radio_img2model = QRadioButton("图生模型 (上传图片→模型)")
        self.radio_dual = QRadioButton("双图融合生模型 (两张图片+提示词→模型)")
        self.radio_text2img.setChecked(True)
        self.mode_group.addButton(self.radio_text2img)
        self.mode_group.addButton(self.radio_img2model)
        self.mode_group.addButton(self.radio_dual)
        
        left_layout.addWidget(self.radio_text2img)
        left_layout.addWidget(self.radio_img2model)
        left_layout.addWidget(self.radio_dual)
        
        self.radio_text2img.toggled.connect(self.update_ui_visibility)
        self.radio_img2model.toggled.connect(self.update_ui_visibility)
        self.radio_dual.toggled.connect(self.update_ui_visibility)
        
        quality_label = QLabel("FLUX 模型质量:")
        quality_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        left_layout.addWidget(quality_label)
        
        self.quality_group = QButtonGroup()
        self.radio_speed = QRadioButton("速度优先 (4B 模型，快速生成)")
        self.radio_quality = QRadioButton("质量优先 (9B 模型，更精细)")
        self.radio_speed.setChecked(True)
        self.quality_group.addButton(self.radio_speed)
        self.quality_group.addButton(self.radio_quality)
        
        left_layout.addWidget(self.radio_speed)
        left_layout.addWidget(self.radio_quality)
        
        self.prompt_label = QLabel("提示词:")
        self.prompt_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(self.prompt_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "输入详细描述，AI 将先生成高清 2D 图像，再进行 3D 建模...\n"
            "例如：一个极具未来感的赛博朋克风格工业机械零件"
        )
        self.prompt_input.setMinimumHeight(100)
        left_layout.addWidget(self.prompt_input)
        
        self.image1_label = QLabel("参考图片 1:")
        self.image1_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(self.image1_label)
        
        self.image1_preview = QLabel("未选择图片")
        self.image1_preview.setMinimumHeight(120)
        self.image1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image1_preview.setStyleSheet("""
            border: 2px dashed #a0aec0;
            border-radius: 10px;
            background-color: #f7fafc;
        """)
        left_layout.addWidget(self.image1_preview)
        
        self.upload1_btn = QPushButton("选择图片 1...")
        self.upload1_btn.clicked.connect(self.select_image1)
        left_layout.addWidget(self.upload1_btn)
        
        self.image2_label = QLabel("参考图片 2:")
        self.image2_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(self.image2_label)
        
        self.image2_preview = QLabel("未选择图片")
        self.image2_preview.setMinimumHeight(120)
        self.image2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image2_preview.setStyleSheet("""
            border: 2px dashed #a0aec0;
            border-radius: 10px;
            background-color: #f7fafc;
        """)
        left_layout.addWidget(self.image2_preview)
        
        self.upload2_btn = QPushButton("选择图片 2...")
        self.upload2_btn.clicked.connect(self.select_image2)
        left_layout.addWidget(self.upload2_btn)
        
        # 生成按钮
        self.generate_btn = QPushButton("开始生成")
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3182ce;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2c5282;
            }
            QPushButton:pressed {
                background-color: #2a4365;
            }
        """)
        self.generate_btn.clicked.connect(self.start_generation)
        left_layout.addWidget(self.generate_btn)
        
        # 日志按钮
        self.log_btn = QPushButton("查看日志")
        self.log_btn.setMinimumHeight(40)
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: white;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
        """)
        self.log_btn.clicked.connect(self.show_log)
        left_layout.addWidget(self.log_btn)
        
        # 进度条
        progress_label = QLabel("生成进度:")
        progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cbd5e0;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #48bb78;
            }
        """)
        left_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #718096; font-size: 12px;")
        left_layout.addWidget(self.status_label)
        
        left_layout.addStretch()
        splitter.addWidget(left_panel)
        
        # --- 右侧资产展示区 ---
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        # 2x2 网格布局（4 个等尺寸正方形框）
        assets_grid = QHBoxLayout()
        
        # 左列
        left_col = QVBoxLayout()
        
        # 2D 预览（正方形 400x400）
        left_col.addWidget(QLabel("<b>1️⃣ 2D 预览</b>"))
        self.preview_2d = QLabel("等待生成...")
        self.preview_2d.setMinimumSize(400, 400)
        self.preview_2d.setMaximumSize(400, 400)
        self.preview_2d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_2d.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            background-color: #ffffff;
        """)
        left_col.addWidget(self.preview_2d)
        
        # UV 贴图（正方形 400x400）
        left_col.addWidget(QLabel("<b>3️⃣ UV 贴图</b>"))
        self.preview_uv = QLabel("等待生成...")
        self.preview_uv.setMinimumSize(400, 400)
        self.preview_uv.setMaximumSize(400, 400)
        self.preview_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_uv.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            background-color: #ffffff;
        """)
        left_col.addWidget(self.preview_uv)
        
        # 右列
        right_col = QVBoxLayout()
        
        # 法线贴图（十字展开 6 视角）（正方形 400x400）
        right_col.addWidget(QLabel("<b>2️⃣ 法线贴图（6 视角十字展开）</b>"))
        self.preview_normal = QLabel("等待生成...")
        self.preview_normal.setMinimumSize(400, 400)
        self.preview_normal.setMaximumSize(400, 400)
        self.preview_normal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_normal.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 5px;
            background-color: #1a1a2e;
        """)
        right_col.addWidget(self.preview_normal)
        
        # 成品 3D（正方形 400x400）
        right_col.addWidget(QLabel("<b>4️⃣ 成品 3D</b>"))
        self.vtk_widget_final = QtInteractor(self)
        self.vtk_widget_final.add_axes()
        # 设置 3D 查看器尺寸为 400x400
        self.vtk_widget_final.interactor.setMinimumSize(400, 400)
        self.vtk_widget_final.interactor.setMaximumSize(400, 400)
        right_col.addWidget(self.vtk_widget_final.interactor)
        
        assets_grid.addLayout(left_col)
        assets_grid.addLayout(right_col)
        right_layout.addLayout(assets_grid)
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 初始化 UI 可见性
        self.update_ui_visibility()
    
    def select_image1(self):
        """选择参考图片 1"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择参考图片 1",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        
        if file_path:
            self.current_image1_path = file_path
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image1_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image1_preview.setPixmap(scaled_pixmap)
            self.image1_preview.setText("")
    
    def select_image2(self):
        """选择参考图片 2"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择参考图片 2",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        
        if file_path:
            self.current_image2_path = file_path
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.image2_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image2_preview.setPixmap(scaled_pixmap)
            self.image2_preview.setText("")
    
    def update_ui_visibility(self):
        """根据模式切换 UI 元素可见性"""
        mode, quality = self.get_current_mode()
        
        prompt_visible = "图生模型" not in mode
        image1_visible = "图生模型" in mode or "双图融合" in mode
        image2_visible = "双图融合" in mode
        
        self.prompt_label.setVisible(prompt_visible)
        self.prompt_input.setVisible(prompt_visible)
        
        self.image1_label.setVisible(image1_visible)
        self.image1_preview.setVisible(image1_visible)
        self.upload1_btn.setVisible(image1_visible)
        
        self.image2_label.setVisible(image2_visible)
        self.image2_preview.setVisible(image2_visible)
        self.upload2_btn.setVisible(image2_visible)
    
    def get_current_mode(self):
        """获取当前选中的模式"""
        if self.radio_text2img.isChecked():
            mode = "文生图再生模型"
        elif self.radio_img2model.isChecked():
            mode = "图生模型"
        elif self.radio_dual.isChecked():
            mode = "双图融合生模型"
        else:
            mode = "文生图再生模型"
        
        quality = "quality" if self.radio_quality.isChecked() else "speed"
        return mode, quality
    
    def start_generation(self):
        """开始生成"""
        mode, quality = self.get_current_mode()
        prompt = self.prompt_input.toPlainText().strip()
        image1_path = self.current_image1_path
        image2_path = self.current_image2_path
        
        if "文生图再生" in mode:
            if not prompt:
                QMessageBox.warning(self, "警告", "文生图再生模式必须输入提示词！")
                return
        elif "图生模型" in mode:
            if not image1_path:
                QMessageBox.warning(self, "警告", "图生模型模式必须上传参考图片！")
                return
        elif "双图融合" in mode:
            if not prompt:
                QMessageBox.warning(self, "警告", "双图融合模式必须输入提示词！")
                return
            if not image1_path:
                QMessageBox.warning(self, "警告", "双图融合模式必须上传参考图片 1！")
                return
            if not image2_path:
                QMessageBox.warning(self, "警告", "双图融合模式必须上传参考图片 2！")
                return
        
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("生成中...")
        self.progress_bar.setValue(0)
        self.status_label.setText("正在初始化...")
        
        self.worker = WorkerThread(mode, quality, prompt, image1_path, image2_path)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.intermediate_signal.connect(self.update_preview)
        self.worker.finished_signal.connect(self.generation_finished)
        self.worker.error_signal.connect(self.generation_error)
        self.worker.start()
    
    def update_progress(self, value, desc):
        """更新进度"""
        self.progress_bar.setValue(int(value * 100))
        self.status_label.setText(desc)
    
    def update_preview(self, file_type, file_path):
        """实时更新预览（中间结果）"""
        if not file_path or not os.path.exists(file_path):
            return
        
        if file_type == '2d':
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                self.preview_2d.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_2d.setPixmap(scaled)
            self.preview_2d.setText("")
        elif file_type == 'normal':
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                self.preview_normal.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_normal.setPixmap(scaled)
            self.preview_normal.setText("")
        elif file_type == 'uv':
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                self.preview_uv.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_uv.setPixmap(scaled)
            self.preview_uv.setText("")
        elif file_type == 'model':
            self.load_3d_model(self.vtk_widget_final, file_path)
    
    def generation_finished(self, img_2d, normal_maps, uv_map, final_model):
        """生成完成"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("开始生成")
        self.status_label.setText("生成完成！")
        
        # 显示 2D 预览
        if img_2d and os.path.exists(img_2d):
            pixmap = QPixmap(img_2d)
            # 保持原始比例，适应正方形框（可能有留白）
            scaled = pixmap.scaled(
                self.preview_2d.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_2d.setPixmap(scaled)
            self.preview_2d.setText("")
        else:
            self.preview_2d.setText("无 2D 图像输出")
        
        # 显示法线贴图（十字展开 6 视角）
        if normal_maps and os.path.exists(normal_maps):
            pixmap = QPixmap(normal_maps)
            # 保持原始比例，适应正方形框（可能有留白）
            scaled = pixmap.scaled(
                self.preview_normal.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_normal.setPixmap(scaled)
            self.preview_normal.setText("")
        else:
            self.preview_normal.setText("无法线贴图输出")
        
        # 显示 UV 贴图
        if uv_map and os.path.exists(uv_map):
            pixmap = QPixmap(uv_map)
            # 保持原始比例，适应正方形框（可能有留白）
            scaled = pixmap.scaled(
                self.preview_uv.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_uv.setPixmap(scaled)
            self.preview_uv.setText("")
        else:
            self.preview_uv.setText("无 UV 贴图输出")
        
        # 加载 3D 成品
        if final_model and os.path.exists(final_model):
            self.load_3d_model(self.vtk_widget_final, final_model)
        else:
            self.status_label.setText("无成品模型输出")
    
    def load_3d_model(self, vtk_widget, model_path):
        """加载 3D 模型到查看器（支持纹理）"""
        try:
            print(f"\n=== 加载 3D 模型 ===")
            print(f"模型路径：{model_path}")
            
            # 检查文件是否存在
            if not os.path.exists(model_path):
                print(f"文件不存在：{model_path}")
                return
            
            # 清除旧模型
            vtk_widget.clear()
            vtk_widget.add_axes()
            
            # 加载模型 (trimesh 支持 GLB/OBJ 等格式)
            import trimesh
            import numpy as np
            
            print(f"正在使用 trimesh 加载...")
            # 使用 force='scene' 加载完整场景（包括纹理）
            scene_or_mesh = trimesh.load(model_path, force='scene')
            
            # 处理 Scene 对象（多网格）
            if isinstance(scene_or_mesh, trimesh.Scene):
                print(f"检测到 Scene 对象，包含 {len(scene_or_mesh.geometry)} 个几何体")
                
                # 收集所有几何体用于合并
                geometries = []
                has_texture = False
                
                for geom_name, geom in scene_or_mesh.geometry.items():
                    geometries.append(geom)
                    # 检查是否有纹理
                    if hasattr(geom, 'visual') and hasattr(geom.visual, 'material'):
                        material = geom.visual.material
                        # 检查材质是否有纹理
                        if hasattr(material, 'baseColorTexture') and material.baseColorTexture is not None:
                            has_texture = True
                            print(f"  几何体 {geom_name}: 有纹理")
                        else:
                            print(f"  几何体 {geom_name}: 无纹理")
                
                # 合并所有几何体
                if geometries:
                    mesh = trimesh.util.concatenate(geometries)
                    print(f"合并后顶点数：{len(mesh.vertices) if hasattr(mesh, 'vertices') else 'N/A'}")
                else:
                    print("无可渲染的几何体")
                    return
            else:
                mesh = scene_or_mesh
                has_texture = hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material') and \
                              hasattr(mesh.visual.material, 'baseColorTexture')
            
            print(f"加载成功！")
            
            # 转换为 PyVista 网格
            if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                print(f"转换为 PyVista 网格...")
                pv_mesh = pv.wrap(mesh)
                
                # 尝试提取并应用纹理
                if has_texture:
                    print(f"检测到纹理，尝试加载...")
                    # 从第一个有纹理的几何体获取材质
                    if isinstance(scene_or_mesh, trimesh.Scene):
                        for geom in scene_or_mesh.geometry.values():
                            if hasattr(geom, 'visual') and hasattr(geom.visual, 'material'):
                                material = geom.visual.material
                                if hasattr(material, 'baseColorTexture') and material.baseColorTexture is not None:
                                    texture_img = material.baseColorTexture
                                    # 转换为 numpy 数组
                                    if hasattr(texture_img, 'convert'):
                                        texture_img = texture_img.convert('RGB')
                                        texture_array = np.array(texture_img)
                                        # 创建 PyVista 纹理
                                        pv_texture = pv.numpy_to_texture(texture_array)
                                        print(f"应用纹理：{texture_array.shape}")
                                        vtk_widget.add_mesh(pv_mesh, texture=pv_texture)
                                        print(f"带纹理渲染完成！")
                                        return
                                    
                    # 如果上面失败了，尝试从 mesh.visual 获取
                    if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
                        material = mesh.visual.material
                        if hasattr(material, 'baseColorTexture') and material.baseColorTexture is not None:
                            texture_img = material.baseColorTexture
                            if hasattr(texture_img, 'convert'):
                                texture_img = texture_img.convert('RGB')
                                texture_array = np.array(texture_img)
                                pv_texture = pv.numpy_to_texture(texture_array)
                                vtk_widget.add_mesh(pv_mesh, texture=pv_texture)
                                print(f"带纹理渲染完成！")
                                return
                
                # 无纹理或纹理加载失败，使用默认颜色
                print(f"无纹理或纹理加载失败，使用默认颜色")
                # 判断是白模还是成品（通过文件名）
                if 'Textured' in model_path or 'textured' in model_path:
                    # 成品模型应该有纹理，如果没有可能是加载问题
                    print(f"成品模型缺少纹理，可能是 GLB 文件问题")
                
                vtk_widget.add_mesh(pv_mesh, color="lightgray", show_edges=False)
                vtk_widget.reset_camera()
                vtk_widget.render()
                print(f"渲染完成！（白模）")
            else:
                print(f"网格对象缺少 vertices 或 faces 属性")
                
        except Exception as e:
            import traceback
            print(f"加载 3D 模型失败：{e}")
            print(traceback.format_exc())
    
    def generation_error(self, error_msg):
        """生成出错"""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("开始生成")
        self.progress_bar.setValue(0)
        self.status_label.setText("生成失败")
        
        QMessageBox.critical(self, "错误", f"生成失败:\n{error_msg}")
    
    def show_log(self):
        """显示日志窗口"""
        log_window = LogWindow(self)
        log_window.show()


class LogWindow(QMainWindow):
    """日志窗口类 - 显示 ComfyUI 运行日志"""
    
    # ComfyUI 日志文件路径
    COMFYUI_LOG_PATH = r"E:\ComfyUI_windows_portable\ComfyUI\user\comfyui.log"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志 - ComfyUI 运行日志")
        self.setMinimumSize(800, 600)
        
        # 自动刷新定时器（每 5 秒）
        self.refresh_timer = None
        
        # 创建文本区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontPointSize(9)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setCentralWidget(self.log_text)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 工具栏
        from PyQt6.QtWidgets import QToolBar, QWidget
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_log)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addSeparator()
        
        # 自动刷新开关
        self.auto_refresh_btn = QPushButton("自动刷新：开")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.setChecked(True)
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        toolbar.addWidget(self.auto_refresh_btn)
        
        toolbar.addSeparator()
        
        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.log_text.clear)
        toolbar.addWidget(clear_btn)
        
        toolbar.addSeparator()
        
        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(self.copy_log)
        toolbar.addWidget(copy_btn)
        
        # 保存按钮
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_log)
        toolbar.addWidget(save_btn)
        
        # 初始加载日志
        self.refresh_log()
        
        # 启动自动刷新定时器（每 5 秒）
        self.start_auto_refresh()
    
    def start_auto_refresh(self):
        """启动自动刷新定时器"""
        from PyQt6.QtCore import QTimer
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_log)
        self.refresh_timer.start(5000)  # 5 秒
        self.statusBar().showMessage("自动刷新已启动（每 5 秒）")
    
    def stop_auto_refresh(self):
        """停止自动刷新"""
        if self.refresh_timer:
            self.refresh_timer.stop()
            self.statusBar().showMessage("自动刷新已停止")
    
    def toggle_auto_refresh(self):
        """切换自动刷新状态"""
        if self.auto_refresh_btn.isChecked():
            self.auto_refresh_btn.setText("自动刷新：开")
            self.start_auto_refresh()
        else:
            self.auto_refresh_btn.setText("自动刷新：关")
            self.stop_auto_refresh()
    
    def refresh_log(self):
        """刷新日志内容"""
        try:
            if not os.path.exists(self.COMFYUI_LOG_PATH):
                self.log_text.clear()
                self.log_text.append("=" * 80)
                self.log_text.append("未找到 ComfyUI 日志文件")
                self.log_text.append("=" * 80)
                self.log_text.append("")
                self.log_text.append(f"预期路径：{self.COMFYUI_LOG_PATH}")
                self.log_text.append("")
                self.log_text.append("可能原因：")
                self.log_text.append("  1. ComfyUI 尚未启动")
                self.log_text.append("  2. ComfyUI 启动失败")
                self.log_text.append("  3. 日志文件路径已更改")
                self.log_text.append("")
                self.log_text.append("建议：")
                self.log_text.append("  - 使用 run_gui.bat 启动程序（会自动启动 ComfyUI）")
                self.log_text.append("  - 手动检查 ComfyUI 是否正在运行")
                return
            
            # 读取日志文件
            with open(self.COMFYUI_LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
            
            # 如果日志为空
            if not log_content.strip():
                self.log_text.clear()
                self.log_text.append("=" * 80)
                self.log_text.append("ComfyUI 日志（空）")
                self.log_text.append("=" * 80)
                self.log_text.append("")
                self.log_text.append("ComfyUI 正在运行，但日志文件为空。")
                self.log_text.append("这可能是因为 ComfyUI 刚刚启动。")
                return
            
            # 更新日志显示
            # 只保留最后 10000 行，避免内存溢出
            lines = log_content.splitlines()
            if len(lines) > 10000:
                lines = lines[-10000:]
                self.log_text.setText('\n'.join(lines))
            else:
                self.log_text.setText(log_content)
            
            # 滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            # 更新状态栏
            self.statusBar().showMessage(f"已更新：{len(lines)} 行日志 | 最后更新：{self._get_current_time()}")
            
        except Exception as e:
            self.log_text.append(f"\n读取日志失败：{e}")
            self.statusBar().showMessage(f"错误：{e}")
    
    def _get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def closeEvent(self, event):
        """窗口关闭时停止定时器"""
        self.stop_auto_refresh()
        event.accept()
    
    def copy_log(self):
        """复制日志到剪贴板"""
        from PyQt6.QtGui import QClipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_text.toPlainText())
        QMessageBox.information(self, "提示", "日志已复制到剪贴板！")
    
    def save_log(self):
        """保存日志到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存日志",
            "system_log.txt",
            "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                QMessageBox.information(self, "提示", f"日志已保存到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败：\n{e}")


def main():
    app = QApplication(sys.argv)
    
    # 设置全局样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
