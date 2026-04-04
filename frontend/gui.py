import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QProgressBar,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QSplitter,
    QMessageBox,
    QDialog,
    QLineEdit,
    QGroupBox,
)
import configparser
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

import pyvista as pv
from pyvistaqt import QtInteractor

from api_client import run_comfyui_pipeline
from agent_core import run_smart_agent


class SmartWorker(QThread):
    progress = pyqtSignal(float, str)
    qwen_message = pyqtSignal(str)
    intermediate = pyqtSignal(str, str)
    done = pyqtSignal(object)
    err = pyqtSignal(str)

    def __init__(self, user_input, image_path, quality):
        super().__init__()
        self.user_input = user_input
        self.image_path = image_path
        self.quality = quality

    def run(self):
        try:

            def on_qwen_message(msg):
                self.qwen_message.emit(msg)

            def on_progress(v, d):
                self.progress.emit(v, d)

            result = run_smart_agent(
                self.user_input,
                [self.image_path] if self.image_path else None,
                callback=on_qwen_message,
            )
            self.done.emit(result)
        except Exception as e:
            self.err.emit(str(e))


class Worker(QThread):
    progress = pyqtSignal(float, str)
    intermediate = pyqtSignal(str, str)
    done = pyqtSignal(object, object, object, object)
    err = pyqtSignal(str)

    def __init__(self, mode, quality, prompt, img1, img2=None):
        super().__init__()
        self.mode, self.quality, self.prompt = mode, quality, prompt
        self.img1, self.img2 = img1, img2

    def run(self):
        try:

            def on_progress(v, d):
                self.progress.emit(v, d)

            def on_intermediate(t, p):
                self.intermediate.emit(t, p)

            result = run_comfyui_pipeline(
                self.mode,
                self.quality,
                self.prompt,
                self.img1,
                self.img2,
                progress=on_progress,
                intermediate_callback=on_intermediate,
            )
            self.done.emit(*result)
        except Exception as e:
            self.err.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Asset Generator")
        self.setMinimumSize(1400, 900)

        self.img1_path = None
        self.img2_path = None
        self.smart_img_path = None

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QLabel("3D Asset Generator")
        header.setStyleSheet("font-size: 20px; font-weight: bold; padding: 4px;")

        header_layout = QHBoxLayout()
        header_layout.addWidget(header)
        header_layout.addStretch()

        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.clicked.connect(self._show_settings)
        header_layout.addWidget(self.btn_settings)

        layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel
        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # Mode selection
        left_layout.addWidget(QLabel("Mode"))
        self.mode_group = QButtonGroup()
        self.rb_smart = QRadioButton("🤖 Smart Mode")
        self.rb_text2img = QRadioButton("Text to 3D")
        self.rb_img2model = QRadioButton("Image to 3D")
        self.rb_dual = QRadioButton("Dual Image Fusion")
        self.rb_smart.setChecked(True)

        for rb in [self.rb_smart, self.rb_text2img, self.rb_img2model, self.rb_dual]:
            self.mode_group.addButton(rb)
            left_layout.addWidget(rb)
            rb.toggled.connect(self._update_visibility)

        # Quality
        left_layout.addWidget(QLabel("Quality"))
        self.quality_group = QButtonGroup()
        self.rb_fast = QRadioButton("Fast (4B)")
        self.rb_quality = QRadioButton("Quality (9B)")
        self.rb_fast.setChecked(True)
        self.quality_group.addButton(self.rb_fast)
        self.quality_group.addButton(self.rb_quality)
        left_layout.addWidget(self.rb_fast)
        left_layout.addWidget(self.rb_quality)

        # Smart Mode - Natural Language Input
        self.lbl_smart_input = QLabel("🧠 Natural Language (Optional)")
        left_layout.addWidget(self.lbl_smart_input)
        self.smart_input = QTextEdit()
        self.smart_input.setPlaceholderText(
            "可不输入，AI将自动分析图片质量\n输入需求如: 把材质改成金属, add more details"
        )
        self.smart_input.setMaximumHeight(60)
        left_layout.addWidget(self.smart_input)

        # Smart Mode - Image
        self.lbl_smart_img = QLabel("📷 Image")
        left_layout.addWidget(self.lbl_smart_img)
        self.smart_img_preview = QLabel("Click to select")
        self.smart_img_preview.setMinimumHeight(120)
        self.smart_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.smart_img_preview.setStyleSheet(
            "border: 1px dashed #ccc; background: #fafafa;"
        )
        left_layout.addWidget(self.smart_img_preview)
        self.btn_smart_img = QPushButton("Select Image...")
        self.btn_smart_img.clicked.connect(self._select_smart_img)
        left_layout.addWidget(self.btn_smart_img)

        # Smart Mode - Qwen Response Panel
        self.lbl_qwen = QLabel("🤖 AI Analysis")
        left_layout.addWidget(self.lbl_qwen)
        self.qwen_response = QTextEdit()
        self.qwen_response.setReadOnly(True)
        self.qwen_response.setMaximumHeight(150)
        self.qwen_response.setStyleSheet(
            "border: 1px solid #ddd; background: #f5f5f5; font-size: 11px;"
        )
        self.qwen_response.setPlaceholderText("AI analysis results will appear here...")
        left_layout.addWidget(self.qwen_response)

        # Prompt
        self.lbl_prompt = QLabel("Prompt")
        left_layout.addWidget(self.lbl_prompt)
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "A mechanical watch gear, brass material, close-up view"
        )
        self.prompt_input.setMaximumHeight(80)
        left_layout.addWidget(self.prompt_input)

        # Image 1
        self.lbl_img1 = QLabel("Image 1")
        left_layout.addWidget(self.lbl_img1)
        self.img1_preview = QLabel("Click to select")
        self.img1_preview.setMinimumHeight(100)
        self.img1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img1_preview.setStyleSheet("border: 1px dashed #ccc; background: #fafafa;")
        left_layout.addWidget(self.img1_preview)
        self.btn_img1 = QPushButton("Select...")
        self.btn_img1.clicked.connect(self._select_img1)
        left_layout.addWidget(self.btn_img1)

        # Image 2
        self.lbl_img2 = QLabel("Image 2")
        left_layout.addWidget(self.lbl_img2)
        self.img2_preview = QLabel("Click to select")
        self.img2_preview.setMinimumHeight(100)
        self.img2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img2_preview.setStyleSheet("border: 1px dashed #ccc; background: #fafafa;")
        left_layout.addWidget(self.img2_preview)
        self.btn_img2 = QPushButton("Select...")
        self.btn_img2.clicked.connect(self._select_img2)
        left_layout.addWidget(self.btn_img2)

        # Generate button
        self.btn_gen = QPushButton("Generate")
        self.btn_gen.setMinimumHeight(40)
        self.btn_gen.setStyleSheet("""
            QPushButton { background: #3182ce; color: white; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background: #2c5282; }
            QPushButton:disabled { background: #a0aec0; }
        """)
        self.btn_gen.clicked.connect(self._generate)
        left_layout.addWidget(self.btn_gen)

        # Progress
        self.progress = QProgressBar()
        self.progress.setMaximumHeight(20)
        left_layout.addWidget(self.progress)

        self.status = QLabel("Ready")
        self.status.setStyleSheet("color: #666; font-size: 11px;")
        left_layout.addWidget(self.status)

        # Log button
        self.btn_log = QPushButton("Log")
        self.btn_log.clicked.connect(self._show_log)
        left_layout.addWidget(self.btn_log)

        left_layout.addStretch()
        splitter.addWidget(left)

        # Right panel - previews
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        # Grid layout for 4 previews
        grid = QHBoxLayout()

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        # 2D Preview
        col1.addWidget(QLabel("2D"))
        self.preview_2d = QLabel("--")
        self.preview_2d.setMinimumSize(350, 350)
        self.preview_2d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_2d.setStyleSheet("border: 1px solid #ddd; background: #fff;")
        col1.addWidget(self.preview_2d)

        # UV
        col1.addWidget(QLabel("UV"))
        self.preview_uv = QLabel("--")
        self.preview_uv.setMinimumSize(350, 350)
        self.preview_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_uv.setStyleSheet("border: 1px solid #ddd; background: #fff;")
        col1.addWidget(self.preview_uv)

        # Normal
        col2.addWidget(QLabel("Normal"))
        self.preview_normal = QLabel("--")
        self.preview_normal.setMinimumSize(350, 350)
        self.preview_normal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_normal.setStyleSheet(
            "border: 1px solid #ddd; background: #1a1a2e;"
        )
        col2.addWidget(self.preview_normal)

        # 3D
        col2.addWidget(QLabel("3D"))
        self.vtk_widget = QtInteractor(self)
        self.vtk_widget.add_axes()
        self.vtk_widget.interactor.setMinimumSize(350, 350)
        col2.addWidget(self.vtk_widget.interactor)

        grid.addLayout(col1)
        grid.addLayout(col2)
        right_layout.addLayout(grid)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self._update_visibility()

    def _update_visibility(self):
        mode, _ = self._get_mode()
        is_smart = self.rb_smart.isChecked()

        # Smart mode controls
        self.lbl_smart_input.setVisible(is_smart)
        self.smart_input.setVisible(is_smart)
        self.lbl_smart_img.setVisible(is_smart)
        self.smart_img_preview.setVisible(is_smart)
        self.btn_smart_img.setVisible(is_smart)
        self.lbl_qwen.setVisible(is_smart)
        self.qwen_response.setVisible(is_smart)

        # Traditional mode controls
        show_prompt = "Image to 3D" not in mode and not is_smart
        show_img1 = "Image to 3D" in mode or "Dual" in mode
        show_img2 = "Dual" in mode

        self.lbl_prompt.setVisible(show_prompt)
        self.prompt_input.setVisible(show_prompt)

        self.lbl_img1.setVisible(show_img1)
        self.img1_preview.setVisible(show_img1)
        self.btn_img1.setVisible(show_img1)

        self.lbl_img2.setVisible(show_img2)
        self.img2_preview.setVisible(show_img2)
        self.btn_img2.setVisible(show_img2)

    def _get_mode(self):
        if self.rb_smart.isChecked():
            mode = "Smart"
        elif self.rb_text2img.isChecked():
            mode = "Text to 3D"
        elif self.rb_img2model.isChecked():
            mode = "Image to 3D"
        else:
            mode = "Dual Image Fusion"

        quality = "quality" if self.rb_quality.isChecked() else "fast"
        return mode, quality

    def _select_img1(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image 1", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.img1_path = path
            px = QPixmap(path).scaled(
                self.img1_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img1_preview.setPixmap(px)
            self.img1_preview.setText("")

    def _select_img2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image 2", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.img2_path = path
            px = QPixmap(path).scaled(
                self.img2_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img2_preview.setPixmap(px)
            self.img2_preview.setText("")

    def _select_smart_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.smart_img_path = path
            px = QPixmap(path).scaled(
                self.smart_img_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.smart_img_preview.setPixmap(px)
            self.smart_img_preview.setText("")

    def _generate(self):
        mode, quality = self._get_mode()

        # Smart Mode
        if mode == "Smart":
            if not self.smart_img_path:
                QMessageBox.warning(self, "Error", "Please select an image")
                return

            user_input = self.smart_input.toPlainText().strip()
            # 提示词可以为空，AI将自动分析

            self.btn_gen.setEnabled(False)
            self.btn_gen.setText("Generating...")
            self.progress.setValue(0)
            self.status.setText("Starting Smart Mode...")
            self.qwen_response.clear()

            self.smart_worker = SmartWorker(user_input, self.smart_img_path, quality)
            self.smart_worker.progress.connect(self._on_progress)
            self.smart_worker.qwen_message.connect(self._on_qwen_message)
            self.smart_worker.intermediate.connect(self._on_intermediate)
            self.smart_worker.done.connect(self._on_smart_done)
            self.smart_worker.err.connect(self._on_error)
            self.smart_worker.start()
            return

        # Traditional modes
        prompt = self.prompt_input.toPlainText().strip()

        # Validation
        if "Text to 3D" in mode and not prompt:
            QMessageBox.warning(self, "Error", "Prompt required")
            return
        if "Image to 3D" in mode and not self.img1_path:
            QMessageBox.warning(self, "Error", "Image 1 required")
            return
        if "Dual" in mode:
            if not prompt:
                QMessageBox.warning(self, "Error", "Prompt required")
                return
            if not self.img1_path:
                QMessageBox.warning(self, "Error", "Image 1 required")
                return
            if not self.img2_path:
                QMessageBox.warning(self, "Error", "Image 2 required")
                return

        self.btn_gen.setEnabled(False)
        self.btn_gen.setText("Generating...")
        self.progress.setValue(0)
        self.status.setText("Starting...")

        self.worker = Worker(mode, quality, prompt, self.img1_path, self.img2_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.intermediate.connect(self._on_intermediate)
        self.worker.done.connect(self._on_done)
        self.worker.err.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, val, desc):
        self.progress.setValue(int(val * 100))
        self.status.setText(desc)

    def _on_qwen_message(self, msg):
        import json

        try:
            data = json.loads(msg)
            type_ = data.get("type", "INFO")
            content = data.get("content", msg)

            prefix = {
                "INFO": "🔍",
                "ANALYSIS": "📊",
                "DECISION": "🎯",
                "SUCCESS": "✅",
                "WARNING": "⚠️",
                "ERROR": "❌",
                "PREVIEW_2D": "🖼️",
                "PREVIEW_NORMAL": "📐",
                "PREVIEW_UV": "🎨",
                "MODEL_READY": "🎲",
                "TOOL_CALL": "🔧",
                "TOOL_RESULT": "📋",
                "THINKING": "💭",
                "DONE": "🎉",
            }.get(type_, "•")

            self.qwen_response.append(f"{prefix} {content}")

            # 处理预览图更新
            if type_ == "PREVIEW_2D" and content and os.path.exists(content):
                px = QPixmap(content).scaled(
                    self.preview_2d.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_2d.setPixmap(px)
                self.preview_2d.setText("")
            elif type_ == "PREVIEW_NORMAL" and content and os.path.exists(content):
                px = QPixmap(content).scaled(
                    self.preview_normal.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_normal.setPixmap(px)
                self.preview_normal.setText("")
            elif type_ == "PREVIEW_UV" and content and os.path.exists(content):
                px = QPixmap(content).scaled(
                    self.preview_uv.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_uv.setPixmap(px)
                self.preview_uv.setText("")
            elif type_ == "MODEL_READY" and content and os.path.exists(content):
                self._load_model(self.vtk_widget, content)
        except:
            self.qwen_response.append(f"• {msg}")

    def _on_intermediate(self, ftype, fpath):
        if not fpath or not os.path.exists(fpath):
            return

        if ftype == "2d":
            px = QPixmap(fpath).scaled(
                self.preview_2d.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_2d.setPixmap(px)
            self.preview_2d.setText("")
        elif ftype == "normal":
            px = QPixmap(fpath).scaled(
                self.preview_normal.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_normal.setPixmap(px)
            self.preview_normal.setText("")
        elif ftype == "uv":
            px = QPixmap(fpath).scaled(
                self.preview_uv.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_uv.setPixmap(px)
            self.preview_uv.setText("")
        elif ftype == "model":
            self._load_model(self.vtk_widget, fpath)

    def _on_done(self, img2d, normal, uv, model):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("Generate")
        self.status.setText("Done")

        if img2d and os.path.exists(img2d):
            px = QPixmap(img2d).scaled(
                self.preview_2d.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_2d.setPixmap(px)

        if normal and os.path.exists(normal):
            px = QPixmap(normal).scaled(
                self.preview_normal.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_normal.setPixmap(px)

        if uv and os.path.exists(uv):
            px = QPixmap(uv).scaled(
                self.preview_uv.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview_uv.setPixmap(px)

        if model and os.path.exists(model):
            self._load_model(self.vtk_widget, model)

    def _on_smart_done(self, model_path):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("Generate")
        self.progress.setValue(100)
        self.status.setText("Done")

        if model_path and os.path.exists(model_path):
            self.qwen_response.append(f"🎉 3D模型生成完成: {model_path}")
            self._load_model(self.vtk_widget, model_path)
        else:
            self.qwen_response.append("⚠️ 未生成模型文件")

    def _on_error(self, msg):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("Generate")
        self.progress.setValue(0)
        self.status.setText("Error")
        QMessageBox.critical(self, "Error", msg)

    def _load_model(self, widget, path):
        try:
            if not os.path.exists(path):
                return

            import trimesh
            import numpy as np

            widget.clear()
            widget.add_axes()

            scene = trimesh.load(path, force="scene")

            if isinstance(scene, trimesh.Scene):
                geometries = list(scene.geometry.values())
                mesh = trimesh.util.concatenate(geometries) if geometries else None
            else:
                mesh = scene

            if not mesh or not hasattr(mesh, "vertices"):
                return

            pv_mesh = pv.wrap(mesh)

            texture = None
            if isinstance(scene, trimesh.Scene):
                for geom in scene.geometry.values():
                    if hasattr(geom, "visual") and hasattr(geom.visual, "material"):
                        mat = geom.visual.material
                        if (
                            hasattr(mat, "baseColorTexture")
                            and mat.baseColorTexture is not None
                        ):
                            img = mat.baseColorTexture
                            if hasattr(img, "convert"):
                                img = img.convert("RGB")
                                texture = pv.numpy_to_texture(np.array(img))
                                break

            if texture:
                widget.add_mesh(pv_mesh, texture=texture)
            else:
                widget.add_mesh(pv_mesh)

            widget.reset_camera()
        except:
            pass

    def _show_settings(self):
        SettingsDialog(self).exec()

    def _show_log(self):
        LogWindow(self).show()


class SettingsDialog(QDialog):
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        # API Key
        layout.addWidget(QLabel("DashScope API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.api_key_input.setText(self._load_api_key())
        layout.addWidget(self.api_key_input)

        # Model
        layout.addWidget(QLabel("Qwen Model"))
        self.model_input = QLineEdit()
        self.model_input.setText(self._load_model())
        layout.addWidget(self.model_input)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _load_api_key(self):
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH, encoding="utf-8")
        return config.get("Agent", "dashscope_api_key", fallback="")

    def _load_model(self):
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH, encoding="utf-8")
        return config.get("Agent", "qwen_model", fallback="qwen3.5-plus")

    def _save(self):
        config = configparser.ConfigParser()
        config.read(self.CONFIG_PATH, encoding="utf-8")

        if not config.has_section("Agent"):
            config.add_section("Agent")

        config.set("Agent", "dashscope_api_key", self.api_key_input.text())
        config.set("Agent", "qwen_model", self.model_input.text())

        with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
            config.write(f)

        QMessageBox.information(self, "Success", "Settings saved!")
        self.accept()


class LogWindow(QMainWindow):
    LOG_PATH = r"E:\ComfyUI_windows_portable\ComfyUI\user\comfyui.log"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log")
        self.setMinimumSize(800, 600)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.setCentralWidget(self.log_text)

        self._refresh()

    def _refresh(self):
        if not os.path.exists(self.LOG_PATH):
            self.log_text.setText("Log file not found")
            return

        with open(self.LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().splitlines()
            if len(lines) > 5000:
                lines = lines[-5000:]
            self.log_text.setText("\n".join(lines))

        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())


def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n[Error] {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
