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
    QSizePolicy,
)
import configparser
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

import pyvista as pv
from pyvistaqt import QtInteractor

from api_client import run_comfyui_pipeline
from agent_core import run_smart_agent

# ==========================================
# 资源配置
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "assets", "icons")


def get_icon(filename):
    return os.path.join(ICONS_DIR, filename)


# ==========================================
# 专业深色主题
# ==========================================
STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #cccccc;
}
QWidget {
    color: #cccccc;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}
QFrame {
    border: none;
}
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    border: 1px solid #333333;
    border-radius: 4px;
    margin-top: 16px;
    padding-top: 12px;
    background-color: #252526;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    color: #999999;
    background-color: transparent;
}
QRadioButton {
    font-size: 12px;
    padding: 4px 2px;
    color: #cccccc;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 1px solid #555555;
    background-color: #1e1e1e;
}
QRadioButton::indicator:checked {
    border: 4px solid #007acc;
    background-color: #1e1e1e;
}
QPushButton {
    font-size: 12px;
    padding: 6px 12px;
    border-radius: 3px;
    border: 1px solid #3c3c3c;
    background-color: #333333;
    color: #cccccc;
}
QPushButton:hover {
    background-color: #3f3f46;
    border-color: #555555;
}
QPushButton:pressed {
    background-color: #2d2d30;
}
QPushButton:disabled {
    background-color: #2d2d30;
    color: #555555;
    border: 1px solid #333333;
}
QPushButton#primaryAction {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    font-weight: 600;
}
QPushButton#primaryAction:hover { background-color: #1177bb; }
QPushButton#primaryAction:disabled { background-color: #4d4d4f; color: #888888; }
QTextEdit, QLineEdit {
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    padding: 6px;
    font-size: 12px;
    background-color: #1e1e1e;
    color: #cccccc;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #007acc;
}
QProgressBar {
    border: 1px solid #333333;
    border-radius: 2px;
    background-color: #1e1e1e;
    text-align: center;
    font-size: 10px;
    color: #ffffff;
}
QProgressBar::chunk {
    background-color: #0e639c;
}
QLabel {
    font-size: 12px;
    color: #cccccc;
}
QSplitter::handle {
    background-color: #1e1e1e;
    width: 4px;
}
QSplitter::handle:hover {
    background-color: #333333;
}
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #4f4f4f;
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
        self.setWindowTitle("3D资产生成器")
        self.setMinimumSize(1400, 850)
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
        main_splitter.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(main_splitter)

        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)

        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([300, 800, 300])

        self._update_visibility()

    def _create_header(self):
        header = QFrame()
        header.setStyleSheet(
            "background-color: #2d2d30; border-bottom: 1px solid #1e1e1e;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("3D资产生成器")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff;")
        header_layout.addWidget(title)

        version = QLabel("v3.0")
        version.setStyleSheet("font-size: 11px; color: #858585;")
        header_layout.addWidget(version)
        header_layout.addStretch()

        self.btn_settings = QPushButton(" 设置")
        self.btn_settings.setIcon(QIcon(get_icon("settings.png")))
        self.btn_settings.clicked.connect(self._show_settings)
        header_layout.addWidget(self.btn_settings)

        self.btn_log = QPushButton(" 控制台")
        self.btn_log.setIcon(QIcon(get_icon("console.png")))
        self.btn_log.clicked.connect(self._show_log)
        header_layout.addWidget(self.btn_log)

        return header

    def _create_left_panel(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(8)

        # 1. 管线模式组
        mode_group = QGroupBox("管线模式")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(8)

        self.mode_group = QButtonGroup()
        self.rb_smart = QRadioButton("智能计算 (云端API)")
        self.rb_text2img = QRadioButton("文本 -> 图像 -> 3D (本地)")
        self.rb_img2model = QRadioButton("图像 -> 3D (本地)")
        self.rb_dual = QRadioButton("双图融合 (本地)")
        self.rb_smart.setChecked(True)

        for rb in [self.rb_smart, self.rb_text2img, self.rb_img2model, self.rb_dual]:
            self.mode_group.addButton(rb)
            mode_layout.addWidget(rb)
            rb.toggled.connect(self._update_visibility)

        layout.addWidget(mode_group)

        # 2. 渲染质量组
        quality_group = QGroupBox("渲染质量")
        quality_layout = QHBoxLayout(quality_group)
        self.quality_group = QButtonGroup()
        self.rb_fast = QRadioButton("草稿 (4B)")
        self.rb_quality = QRadioButton("成品 (9B)")
        self.rb_fast.setChecked(True)
        self.quality_group.addButton(self.rb_fast)
        self.quality_group.addButton(self.rb_quality)
        quality_layout.addWidget(self.rb_fast)
        quality_layout.addWidget(self.rb_quality)
        layout.addWidget(quality_group)

        # 3. 本地管线输入组
        self.input_group = QGroupBox("本地管线输入")
        input_layout = QVBoxLayout(self.input_group)
        input_layout.setSpacing(8)

        placeholder_style = (
            "border: 1px dashed #555555; background-color: #1e1e1e; color: #888888;"
        )

        self.lbl_img1 = QLabel("基础图像")
        self.img1_preview = QLabel("点击加载图像")
        self.img1_preview.setMinimumHeight(100)
        self.img1_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img1_preview.setStyleSheet(placeholder_style)
        self.img1_preview.mousePressEvent = lambda e: self._select_img1()
        input_layout.addWidget(self.lbl_img1)
        input_layout.addWidget(self.img1_preview)

        self.lbl_img2 = QLabel("参考图像")
        self.img2_preview = QLabel("点击加载图像")
        self.img2_preview.setMinimumHeight(100)
        self.img2_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img2_preview.setStyleSheet(placeholder_style)
        self.img2_preview.mousePressEvent = lambda e: self._select_img2()
        input_layout.addWidget(self.lbl_img2)
        input_layout.addWidget(self.img2_preview)

        self.lbl_prompt = QLabel("文本提示词")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("输入描述性提示词...")
        self.prompt_input.setMaximumHeight(60)
        input_layout.addWidget(self.lbl_prompt)
        input_layout.addWidget(self.prompt_input)

        layout.addWidget(self.input_group)

        # 4. 处理状态组
        self.status_group = QGroupBox("处理状态")
        status_layout = QVBoxLayout(self.status_group)
        self.progress = QProgressBar()
        self.progress.setMinimumHeight(12)
        self.progress.setTextVisible(False)
        status_layout.addWidget(self.progress)
        self.status = QLabel("空闲")
        self.status.setStyleSheet("color: #999999;")
        status_layout.addWidget(self.status)
        layout.addWidget(self.status_group)

        # 5. 执行按钮
        self.btn_gen = QPushButton(" 执行本地管线")
        self.btn_gen.setObjectName("primaryAction")
        self.btn_gen.setIcon(QIcon(get_icon("play.png")))
        self.btn_gen.setMinimumHeight(36)
        self.btn_gen.clicked.connect(self._generate)
        layout.addWidget(self.btn_gen)

        layout.addStretch()
        return panel

    def _create_center_panel(self):
        panel = QFrame()
        panel.setStyleSheet("background-color: #252526; border: 1px solid #333333;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        grid = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()

        preview_box_style = (
            "border: 1px solid #3c3c3c; background-color: #1e1e1e; color: #555555;"
        )

        col1.addWidget(self._create_preview_label("2D 预览", "view_2d.png"))
        self.preview_2d = QLabel("无数据")
        self.preview_2d.setFixedSize(320, 320)
        self.preview_2d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_2d.setStyleSheet(preview_box_style)
        col1.addWidget(self.preview_2d, alignment=Qt.AlignmentFlag.AlignCenter)

        col1.addWidget(self._create_preview_label("UV 贴图", "view_uv.png"))
        self.preview_uv = QLabel("无数据")
        self.preview_uv.setFixedSize(320, 320)
        self.preview_uv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_uv.setStyleSheet(preview_box_style)
        col1.addWidget(self.preview_uv, alignment=Qt.AlignmentFlag.AlignCenter)

        col2.addWidget(self._create_preview_label("法线贴图", "view_normal.png"))
        self.preview_normal = QLabel("无数据")
        self.preview_normal.setFixedSize(320, 320)
        self.preview_normal.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_normal.setStyleSheet(preview_box_style)
        col2.addWidget(self.preview_normal, alignment=Qt.AlignmentFlag.AlignCenter)

        col2.addWidget(self._create_preview_label("3D 视窗", "view_3d.png"))
        self.vtk_container = QFrame()
        self.vtk_container.setFixedSize(320, 320)
        self.vtk_container.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #3c3c3c;"
        )
        vtk_layout = QVBoxLayout(self.vtk_container)
        vtk_layout.setContentsMargins(1, 1, 1, 1)

        self.vtk_widget = QtInteractor(self.vtk_container)
        self.vtk_widget.set_background("#1e1e1e")
        self.vtk_widget.add_axes()
        vtk_layout.addWidget(self.vtk_widget.interactor)

        col2.addWidget(self.vtk_container, alignment=Qt.AlignmentFlag.AlignCenter)

        grid.addLayout(col1)
        grid.addLayout(col2)
        layout.addLayout(grid)

        return panel

    def _create_preview_label(self, text, icon_name):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 4)

        icon_label = QLabel()
        icon_label.setPixmap(QIcon(get_icon(icon_name)).pixmap(16, 16))

        text_label = QLabel(text)
        text_label.setStyleSheet("font-weight: 600; color: #cccccc;")

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()
        return container

    def _create_right_panel(self):
        self.right_panel = QFrame()
        layout = QVBoxLayout(self.right_panel)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(8)

        ai_group = QGroupBox("控制台输出")
        ai_layout = QVBoxLayout(ai_group)
        self.qwen_response = QTextEdit()
        self.qwen_response.setReadOnly(True)
        self.qwen_response.setMinimumHeight(250)
        self.qwen_response.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 11px;"
        )
        self.qwen_response.setPlaceholderText("等待处理初始化...")
        ai_layout.addWidget(self.qwen_response)
        layout.addWidget(ai_group)

        smart_group = QGroupBox("API源资产")
        smart_layout = QVBoxLayout(smart_group)

        self.lbl_smart_img = QLabel("输入图像")
        smart_layout.addWidget(self.lbl_smart_img)

        self.smart_img_preview = QLabel("点击加载图像")
        self.smart_img_preview.setMinimumHeight(120)
        self.smart_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.smart_img_preview.setStyleSheet(
            "border: 1px dashed #555555; background-color: #1e1e1e; color: #888888;"
        )
        self.smart_img_preview.mousePressEvent = lambda e: self._select_smart_img()
        smart_layout.addWidget(self.smart_img_preview)

        self.lbl_smart_input = QLabel("指令覆盖 (可选)")
        smart_layout.addWidget(self.lbl_smart_input)

        self.smart_input = QTextEdit()
        self.smart_input.setPlaceholderText("例如: 应用生锈金属材质")
        self.smart_input.setMaximumHeight(60)
        smart_layout.addWidget(self.smart_input)
        layout.addWidget(smart_group)

        status_group = QGroupBox("任务状态")
        status_layout = QVBoxLayout(status_group)
        self.ai_progress = QProgressBar()
        self.ai_progress.setMinimumHeight(12)
        self.ai_progress.setTextVisible(False)
        status_layout.addWidget(self.ai_progress)
        self.ai_status = QLabel("空闲")
        self.ai_status.setStyleSheet("color: #999999;")
        status_layout.addWidget(self.ai_status)
        layout.addWidget(status_group)

        self.btn_smart_gen = QPushButton(" 云端计算")
        self.btn_smart_gen.setObjectName("primaryAction")
        self.btn_smart_gen.setIcon(QIcon(get_icon("play.png")))
        self.btn_smart_gen.setMinimumHeight(36)
        self.btn_smart_gen.clicked.connect(self._generate)
        layout.addWidget(self.btn_smart_gen)

        layout.addStretch()
        return self.right_panel

    def _update_visibility(self):
        mode = self._get_mode()
        is_smart = mode == "Smart"

        self.right_panel.setVisible(is_smart)

        self.input_group.setVisible(not is_smart)
        self.status_group.setVisible(not is_smart)
        self.btn_gen.setVisible(not is_smart)

        if not is_smart:
            show_prompt = mode in ["Text to 3D", "Dual Image Fusion"]
            show_img1 = mode in ["Image to 3D", "Dual Image Fusion"]
            show_img2 = mode == "Dual Image Fusion"

            self.lbl_prompt.setVisible(show_prompt)
            self.prompt_input.setVisible(show_prompt)
            self.lbl_img1.setVisible(show_img1)
            self.img1_preview.setVisible(show_img1)
            self.lbl_img2.setVisible(show_img2)
            self.img2_preview.setVisible(show_img2)

    def _get_mode(self):
        if self.rb_smart.isChecked():
            return "Smart"
        if self.rb_text2img.isChecked():
            return "Text to 3D"
        if self.rb_img2model.isChecked():
            return "Image to 3D"
        return "Dual Image Fusion"

    def _select_img1(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择基础图像", "", "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.img1_path = path
            px = QPixmap(path).scaled(
                self.img1_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img1_preview.setStyleSheet(
                "border: 1px solid #3c3c3c; background-color: #1e1e1e;"
            )
            self.img1_preview.setPixmap(px)

    def _select_img2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择参考图像", "", "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.img2_path = path
            px = QPixmap(path).scaled(
                self.img2_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img2_preview.setStyleSheet(
                "border: 1px solid #3c3c3c; background-color: #1e1e1e;"
            )
            self.img2_preview.setPixmap(px)

    def _select_smart_img(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择资产", "", "图像文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.smart_img_path = path
            px = QPixmap(path).scaled(
                self.smart_img_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.smart_img_preview.setStyleSheet(
                "border: 1px solid #3c3c3c; background-color: #1e1e1e;"
            )
            self.smart_img_preview.setPixmap(px)

    def _generate(self):
        mode = self._get_mode()
        quality = "quality" if self.rb_quality.isChecked() else "fast"

        if mode == "Smart":
            if not self.smart_img_path:
                QMessageBox.warning(self, "警告", "请选择源图像。")
                return

            user_input = self.smart_input.toPlainText().strip()
            self.btn_smart_gen.setEnabled(False)
            self.btn_smart_gen.setText(" 处理中...")
            self.ai_progress.setValue(0)
            self.ai_status.setText("初始化...")
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

        if mode == "Text to 3D" and not prompt:
            QMessageBox.warning(self, "警告", "请输入文本提示词。")
            return
        if mode == "Image to 3D" and not self.img1_path:
            QMessageBox.warning(self, "警告", "请选择基础图像。")
            return
        if mode == "Dual Image Fusion":
            if not prompt:
                QMessageBox.warning(self, "警告", "请输入文本提示词。")
                return
            if not self.img1_path or not self.img2_path:
                QMessageBox.warning(self, "警告", "请选择基础图像和参考图像。")
                return

        self.btn_gen.setEnabled(False)
        self.btn_gen.setText(" 执行中...")
        self.progress.setValue(0)
        self.status.setText(f"初始化 {mode} 管线...")

        self.worker = Worker(mode, quality, prompt, self.img1_path, self.img2_path)
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
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            data = json.loads(msg)
            type_ = data.get("type", "INFO")
            content = data.get("content", msg)

            color_map = {
                "INFO": "#cccccc",
                "ANALYSIS": "#007acc",
                "DECISION": "#dcdcaa",
                "SUCCESS": "#4CAF50",
                "WARNING": "#ce9178",
                "ERROR": "#f44336",
                "PREVIEW_2D": "#c586c0",
                "PREVIEW_NORMAL": "#c586c0",
                "PREVIEW_UV": "#c586c0",
                "MODEL_READY": "#4CAF50",
                "TOOL_CALL": "#4fc1ff",
                "TOOL_RESULT": "#4fc1ff",
                "THINKING": "#888888",
                "DONE": "#4CAF50",
            }
            color = color_map.get(type_, "#cccccc")

            type_map = {
                "INFO": "信息",
                "ANALYSIS": "分析",
                "DECISION": "决策",
                "SUCCESS": "成功",
                "WARNING": "警告",
                "ERROR": "错误",
                "PREVIEW_2D": "2D预览",
                "PREVIEW_NORMAL": "法线",
                "PREVIEW_UV": "UV",
                "MODEL_READY": "模型就绪",
                "TOOL_CALL": "工具调用",
                "TOOL_RESULT": "工具结果",
                "THINKING": "思考中",
                "DONE": "完成",
            }
            type_text = type_map.get(type_, type_)

            self.qwen_response.append(
                f"<span style='color:#666666;'>[{timestamp}]</span> <span style='color:{color};'>[{type_text}]</span> <span style='color:#cccccc;'>{content}</span>"
            )

            if type_ == "PREVIEW_2D" and content and os.path.exists(content):
                self._update_preview_image(self.preview_2d, content)
            elif type_ == "PREVIEW_NORMAL" and content and os.path.exists(content):
                self._update_preview_image(self.preview_normal, content)
            elif type_ == "PREVIEW_UV" and content and os.path.exists(content):
                self._update_preview_image(self.preview_uv, content)
            elif type_ == "MODEL_READY" and content and os.path.exists(content):
                self._load_model(self.vtk_widget, content)
        except:
            self.qwen_response.append(
                f"<span style='color:#666666;'>[{timestamp}]</span> <span style='color:#cccccc;'>{msg}</span>"
            )

    def _update_preview_image(self, label, path):
        px = QPixmap(path).scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setStyleSheet("border: 1px solid #3c3c3c; background-color: #1e1e1e;")
        label.setPixmap(px)

    def _on_intermediate(self, ftype, fpath):
        if not fpath or not os.path.exists(fpath):
            return
        if ftype == "2d":
            self._update_preview_image(self.preview_2d, fpath)
        elif ftype == "normal":
            self._update_preview_image(self.preview_normal, fpath)
        elif ftype == "uv":
            self._update_preview_image(self.preview_uv, fpath)
        elif ftype == "model":
            self._load_model(self.vtk_widget, fpath)

    def _on_done(self, img2d, normal, uv, model):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText(" 执行本地管线")
        self.status.setText("处理完成")
        if img2d and os.path.exists(img2d):
            self._update_preview_image(self.preview_2d, img2d)
        if normal and os.path.exists(normal):
            self._update_preview_image(self.preview_normal, normal)
        if uv and os.path.exists(uv):
            self._update_preview_image(self.preview_uv, uv)
        if model and os.path.exists(model):
            self._load_model(self.vtk_widget, model)

    def _on_smart_done(self, model_path):
        self.btn_smart_gen.setEnabled(True)
        self.btn_smart_gen.setText(" 云端计算")
        self.ai_progress.setValue(100)
        self.ai_status.setText("处理完成")
        if model_path and os.path.exists(model_path):
            self._load_model(self.vtk_widget, model_path)

    def _on_error(self, msg):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText(" 执行本地管线")
        self.progress.setValue(0)
        self.status.setText("处理失败")
        self.status.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "执行错误", msg)

    def _on_ai_error(self, msg):
        self.btn_smart_gen.setEnabled(True)
        self.btn_smart_gen.setText(" 云端计算")
        self.ai_progress.setValue(0)
        self.ai_status.setText("处理失败")
        self.ai_status.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "执行错误", msg)

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
                widget.add_mesh(pv_mesh, color="#cccccc", specular=0.5)

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
        self.setWindowTitle("首选项")
        self.setMinimumSize(400, 220)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        api_group = QGroupBox("API 配置")
        api_layout = QVBoxLayout(api_group)

        api_layout.addWidget(QLabel("DashScope API 密钥"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        self.api_key_input.setText(self._load_api_key())
        api_layout.addWidget(self.api_key_input)

        api_layout.addWidget(QLabel("语言模型"))
        self.model_input = QLineEdit()
        self.model_input.setText(self._load_model())
        api_layout.addWidget(self.model_input)

        layout.addWidget(api_group)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("应用")
        btn_save.setObjectName("primaryAction")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
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
        self.accept()


class LogWindow(QMainWindow):
    LOG_PATH = r"E:\ComfyUI_windows_portable\ComfyUI\user\comfyui.log"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统控制台")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(STYLESHEET)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 12px; background-color: #1e1e1e; border: none;"
        )
        self.setCentralWidget(self.log_text)
        self._refresh()

    def _refresh(self):
        if not os.path.exists(self.LOG_PATH):
            self.log_text.setText("[系统] 未找到指定路径的日志文件。")
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
        print(f"\n[致命错误] {e}")
        input("按回车键退出...")


if __name__ == "__main__":
    main()
