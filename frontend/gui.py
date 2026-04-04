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
    QScrollArea,
    QSizePolicy,
)
import configparser
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

import pyvista as pv
from pyvistaqt import QtInteractor

from api_client import run_comfyui_pipeline
from agent_core import run_smart_agent


STYLESHEET = """
QMainWindow {
    background-color: #f5f7fa;
}
QGroupBox {
    font-weight: bold;
    font-size: 12px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: #4a5568;
}
QRadioButton {
    font-size: 12px;
    padding: 4px;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QPushButton {
    font-size: 12px;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
}
QPushButton:hover {
    background-color: #f7fafc;
    border-color: #cbd5e0;
}
QPushButton:disabled {
    background-color: #edf2f7;
    color: #a0aec0;
}
QTextEdit {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    background-color: #ffffff;
}
QTextEdit:focus {
    border-color: #3182ce;
}
QLineEdit {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    background-color: #ffffff;
}
QLineEdit:focus {
    border-color: #3182ce;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #e2e8f0;
    text-align: center;
    font-size: 11px;
    font-weight: bold;
    color: #4a5568;
}
QProgressBar::chunk {
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #63b3ed);
}
QLabel {
    font-size: 12px;
    color: #4a5568;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
"""


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
        self.setWindowTitle("3D Asset Generator v3.0")
        self.setMinimumSize(1500, 900)
        self.setStyleSheet(STYLESHEET)

        self.img1_path = None
        self.img2_path = None
        self.smart_img_path = None

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = self._create_header()
        layout.addWidget(header)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)

        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)

        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setStretchFactor(2, 1)

        self._update_visibility()

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet("background-color: #2d3748; padding: 8px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("3D Asset Generator")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #ffffff; background: transparent;"
        )
        header_layout.addWidget(title)

        version = QLabel("v3.0")
        version.setStyleSheet(
            "font-size: 12px; color: #a0aec0; background: transparent;"
        )
        header_layout.addWidget(version)
        header_layout.addStretch()

        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #718096;
            }
        """)
        self.btn_settings.clicked.connect(self._show_settings)
        header_layout.addWidget(self.btn_settings)

        self.btn_log = QPushButton("📋 Log")
        self.btn_log.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #718096;
            }
        """)
        self.btn_log.clicked.connect(self._show_log)
        header_layout.addWidget(self.btn_log)

        return header

    def _create_left_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(4)

        self.mode_group = QButtonGroup()
        self.rb_smart = QRadioButton("🤖 Smart Mode")
        self.rb_text2img = QRadioButton("📝 Text to 3D")
        self.rb_img2model = QRadioButton("🖼️ Image to 3D")
        self.rb_dual = QRadioButton("🔀 Dual Image Fusion")
        self.rb_smart.setChecked(True)

        for rb in [self.rb_smart, self.rb_text2img, self.rb_img2model, self.rb_dual]:
            self.mode_group.addButton(rb)
            mode_layout.addWidget(rb)
            rb.toggled.connect(self._update_visibility)

        layout.addWidget(mode_group)

        api_group = QGroupBox("API Mode")
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(4)

        self.api_mode_group = QButtonGroup()
        self.rb_api_on = QRadioButton("🤖 Smart (Use API)")
        self.rb_api_off = QRadioButton("📦 Classic (No API)")
        self.rb_api_on.setChecked(True)
        self.api_mode_group.addButton(self.rb_api_on)
        self.api_mode_group.addButton(self.rb_api_off)
        api_layout.addWidget(self.rb_api_on)
        api_layout.addWidget(self.rb_api_off)
        self.rb_api_on.toggled.connect(self._update_visibility)
        self.rb_api_off.toggled.connect(self._update_visibility)

        layout.addWidget(api_group)

        quality_group = QGroupBox("Quality")
        quality_layout = QHBoxLayout(quality_group)
        self.quality_group = QButtonGroup()
        self.rb_fast = QRadioButton("⚡ Fast (4B)")
        self.rb_quality = QRadioButton("🎯 Quality (9B)")
        self.rb_fast.setChecked(True)
        self.quality_group.addButton(self.rb_fast)
        self.quality_group.addButton(self.rb_quality)
        quality_layout.addWidget(self.rb_fast)
        quality_layout.addWidget(self.rb_quality)
        layout.addWidget(quality_group)

        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        input_layout.setSpacing(8)

        self.lbl_img1 = QLabel("Image 1")
        self.img1_preview = QLabel("Click to select")
        self.img1_preview.setMinimumHeight(100)
        self.img1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img1_preview.setStyleSheet("""
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            background-color: #edf2f7;
            font-size: 12px;
            color: #718096;
        """)
        self.img1_preview.mousePressEvent = lambda e: self._select_img1()
        input_layout.addWidget(self.lbl_img1)
        input_layout.addWidget(self.img1_preview)

        self.lbl_img2 = QLabel("Image 2")
        self.img2_preview = QLabel("Click to select")
        self.img2_preview.setMinimumHeight(100)
        self.img2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img2_preview.setStyleSheet("""
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            background-color: #edf2f7;
            font-size: 12px;
            color: #718096;
        """)
        self.img2_preview.mousePressEvent = lambda e: self._select_img2()
        input_layout.addWidget(self.lbl_img2)
        input_layout.addWidget(self.img2_preview)

        self.lbl_prompt = QLabel("Prompt")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "A mechanical watch gear, brass material, close-up view"
        )
        self.prompt_input.setMaximumHeight(80)
        input_layout.addWidget(self.lbl_prompt)
        input_layout.addWidget(self.prompt_input)

        layout.addWidget(input_group)

        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.progress = QProgressBar()
        self.progress.setMinimumHeight(24)
        status_layout.addWidget(self.progress)

        self.status = QLabel("Ready")
        self.status.setStyleSheet("font-size: 11px; color: #718096;")
        status_layout.addWidget(self.status)

        layout.addWidget(status_group)

        self.btn_gen = QPushButton("🚀 Generate")
        self.btn_gen.setMinimumHeight(48)
        self.btn_gen.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #63b3ed);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c5282, stop:1 #3182ce);
            }
            QPushButton:disabled {
                background: #a0aec0;
            }
        """)
        self.btn_gen.clicked.connect(self._generate)
        layout.addWidget(self.btn_gen)

        layout.addStretch()
        return panel

    def _create_center_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #e2e8f0;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        grid = QHBoxLayout()

        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        col1.addWidget(self._create_preview_label("2D Preview"))
        self.preview_2d = QLabel("Waiting...")
        self.preview_2d.setMinimumSize(200, 200)
        self.preview_2d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_2d.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 14px;
            color: #a0aec0;
        """)
        col1.addWidget(self.preview_2d)

        col1.addWidget(self._create_preview_label("UV Texture"))
        self.preview_uv = QLabel("Waiting...")
        self.preview_uv.setMinimumSize(200, 200)
        self.preview_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_uv.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 14px;
            color: #a0aec0;
        """)
        col1.addWidget(self.preview_uv)

        col2.addWidget(self._create_preview_label("Normal Map"))
        self.preview_normal = QLabel("Waiting...")
        self.preview_normal.setMinimumSize(200, 200)
        self.preview_normal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_normal.setStyleSheet("""
            border: 1px solid #cbd5e0;
            border-radius: 8px;
            background-color: #1a1a2e;
            font-size: 14px;
            color: #a0aec0;
        """)
        col2.addWidget(self.preview_normal)

        col2.addWidget(self._create_preview_label("3D Model"))
        self.vtk_widget = QtInteractor(self)
        self.vtk_widget.add_axes()
        self.vtk_widget.interactor.setMinimumSize(200, 200)
        col2.addWidget(self.vtk_widget.interactor)

        grid.addLayout(col1)
        grid.addLayout(col2)
        layout.addLayout(grid)

        return panel

    def _create_preview_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #4a5568; background: transparent;"
        )
        return label

    def _create_right_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        ai_group = QGroupBox("🤖 AI Assistant")
        ai_layout = QVBoxLayout(ai_group)

        self.qwen_response = QTextEdit()
        self.qwen_response.setReadOnly(True)
        self.qwen_response.setMinimumHeight(300)
        self.qwen_response.setStyleSheet("""
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            background-color: #ffffff;
            font-size: 11px;
            padding: 8px;
        """)
        self.qwen_response.setPlaceholderText("AI analysis results will appear here...")
        ai_layout.addWidget(self.qwen_response)

        layout.addWidget(ai_group)

        smart_group = QGroupBox("Smart Input")
        smart_layout = QVBoxLayout(smart_group)

        self.lbl_smart_img = QLabel("📷 Input Image")
        smart_layout.addWidget(self.lbl_smart_img)

        self.smart_img_preview = QLabel("Click to select")
        self.smart_img_preview.setMinimumHeight(150)
        self.smart_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.smart_img_preview.setStyleSheet("""
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            background-color: #edf2f7;
            font-size: 12px;
            color: #718096;
        """)
        self.smart_img_preview.mousePressEvent = lambda e: self._select_smart_img()
        smart_layout.addWidget(self.smart_img_preview)

        self.lbl_smart_input = QLabel("🧠 Natural Language (Optional)")
        smart_layout.addWidget(self.lbl_smart_input)

        self.smart_input = QTextEdit()
        self.smart_input.setPlaceholderText(
            "可不输入，AI将自动分析\n输入: 把材质改成金属"
        )
        self.smart_input.setMaximumHeight(60)
        smart_layout.addWidget(self.smart_input)

        layout.addWidget(smart_group)

        status_group = QGroupBox("Progress")
        status_layout = QVBoxLayout(status_group)

        self.ai_progress = QProgressBar()
        self.ai_progress.setMinimumHeight(24)
        status_layout.addWidget(self.ai_progress)

        self.ai_status = QLabel("Ready")
        self.ai_status.setStyleSheet("font-size: 11px; color: #718096;")
        status_layout.addWidget(self.ai_status)

        layout.addWidget(status_group)

        self.btn_smart_gen = QPushButton("🚀 Generate")
        self.btn_smart_gen.setMinimumHeight(48)
        self.btn_smart_gen.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #48bb78, stop:1 #68d391);
                color: white;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38a169, stop:1 #48bb78);
            }
            QPushButton:disabled {
                background: #a0aec0;
            }
        """)
        self.btn_smart_gen.clicked.connect(self._generate)
        layout.addWidget(self.btn_smart_gen)

        layout.addStretch()
        return panel

    def _update_visibility(self):
        mode, _, _ = self._get_mode()
        is_smart = self.rb_smart.isChecked()
        use_api = self.rb_api_on.isChecked()

        self.qwen_response.parent().parent().setVisible(is_smart and use_api)
        self.smart_img_preview.parent().parent().setVisible(is_smart and use_api)
        self.ai_progress.parent().parent().setVisible(is_smart and use_api)
        self.btn_smart_gen.setVisible(is_smart and use_api)

        show_prompt = "Image to 3D" not in mode and not is_smart
        show_img1 = ("Image to 3D" in mode or "Dual" in mode) or (
            is_smart and not use_api
        )
        show_img2 = "Dual" in mode

        self.lbl_prompt.setVisible(show_prompt)
        self.prompt_input.setVisible(show_prompt)

        self.lbl_img1.setVisible(show_img1)
        self.img1_preview.setVisible(show_img1)

        self.lbl_img2.setVisible(show_img2)
        self.img2_preview.setVisible(show_img2)

        show_classic_controls = not is_smart or not use_api
        self.progress.parent().parent().setVisible(show_classic_controls)
        self.status.parent().parent().setVisible(show_classic_controls)
        self.btn_gen.setVisible(show_classic_controls)

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
        use_api = self.rb_api_on.isChecked()
        return mode, quality, use_api

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
        mode, quality, use_api = self._get_mode()

        if mode == "Smart" and use_api:
            if not self.smart_img_path:
                QMessageBox.warning(self, "Error", "Please select an image")
                return

            user_input = self.smart_input.toPlainText().strip()

            self.btn_smart_gen.setEnabled(False)
            self.btn_smart_gen.setText("Generating...")
            self.ai_progress.setValue(0)
            self.ai_status.setText("Starting...")
            self.qwen_response.clear()

            self.smart_worker = SmartWorker(user_input, self.smart_img_path, quality)
            self.smart_worker.progress.connect(self._on_ai_progress)
            self.smart_worker.qwen_message.connect(self._on_qwen_message)
            self.smart_worker.intermediate.connect(self._on_intermediate)
            self.smart_worker.done.connect(self._on_smart_done)
            self.smart_worker.err.connect(self._on_ai_error)
            self.smart_worker.start()
            return

        prompt = self.prompt_input.toPlainText().strip()

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

        if mode == "Smart" and not use_api:
            if not self.img1_path:
                QMessageBox.warning(self, "Error", "Image 1 required")
                return

        self.btn_gen.setEnabled(False)
        self.btn_gen.setText("Generating...")
        self.progress.setValue(0)
        self.status.setText("Starting...")

        actual_mode = "Image to 3D" if mode == "Smart" else mode
        self.worker = Worker(
            actual_mode, quality, prompt, self.img1_path, self.img2_path
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.intermediate.connect(self._on_intermediate)
        self.worker.done.connect(self._on_done)
        self.worker.err.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, val, desc):
        self.progress.setValue(int(val * 100))
        self.status.setText(desc)

    def _on_ai_progress(self, val, desc):
        self.ai_progress.setValue(int(val * 100))
        self.ai_status.setText(desc)

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
        self.btn_gen.setText("🚀 Generate")
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
        self.btn_smart_gen.setEnabled(True)
        self.btn_smart_gen.setText("🚀 Generate")
        self.ai_progress.setValue(100)
        self.ai_status.setText("Done")

        if model_path and os.path.exists(model_path):
            self.qwen_response.append(f"🎉 3D模型生成完成")
            self._load_model(self.vtk_widget, model_path)
        else:
            self.qwen_response.append("⚠️ 未生成模型文件")

    def _on_error(self, msg):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("🚀 Generate")
        self.progress.setValue(0)
        self.status.setText("Error")
        self.status.setStyleSheet("font-size: 11px; color: #e53e3e;")
        QMessageBox.critical(self, "Error", msg)

    def _on_ai_error(self, msg):
        self.btn_smart_gen.setEnabled(True)
        self.btn_smart_gen.setText("🚀 Generate")
        self.ai_progress.setValue(0)
        self.ai_status.setText("Error")
        self.ai_status.setStyleSheet("font-size: 11px; color: #e53e3e;")
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
        self.setMinimumSize(400, 220)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout(api_group)

        api_layout.addWidget(QLabel("DashScope API Key"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.api_key_input.setText(self._load_api_key())
        api_layout.addWidget(self.api_key_input)

        api_layout.addWidget(QLabel("Qwen Model"))
        self.model_input = QLineEdit()
        self.model_input.setText(self._load_model())
        api_layout.addWidget(self.model_input)

        layout.addWidget(api_group)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #48bb78, stop:1 #68d391);
                color: white;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38a169, stop:1 #48bb78);
            }
        """)
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
        self.setStyleSheet(STYLESHEET)

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
