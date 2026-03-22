import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QProgressBar,
    QRadioButton, QButtonGroup, QFrame, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap

import pyvista as pv
from pyvistaqt import QtInteractor

from api_client import run_comfyui_pipeline


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
                self.mode, self.quality, self.prompt, self.img1, self.img2,
                progress=on_progress, intermediate_callback=on_intermediate
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
        layout.addWidget(header)
        
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
        self.rb_text2img = QRadioButton("Text to 3D")
        self.rb_img2model = QRadioButton("Image to 3D")
        self.rb_dual = QRadioButton("Dual Image Fusion")
        self.rb_text2img.setChecked(True)
        
        for rb in [self.rb_text2img, self.rb_img2model, self.rb_dual]:
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
        
        # Prompt
        self.lbl_prompt = QLabel("Prompt")
        left_layout.addWidget(self.lbl_prompt)
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("A mechanical watch gear, brass material, close-up view")
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
        self.preview_normal.setStyleSheet("border: 1px solid #ddd; background: #1a1a2e;")
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
        
        show_prompt = "Image to 3D" not in mode
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
        if self.rb_text2img.isChecked():
            mode = "Text to 3D"
        elif self.rb_img2model.isChecked():
            mode = "Image to 3D"
        else:
            mode = "Dual Image Fusion"
        
        quality = "quality" if self.rb_quality.isChecked() else "fast"
        return mode, quality
    
    def _select_img1(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image 1", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.img1_path = path
            px = QPixmap(path).scaled(self.img1_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img1_preview.setPixmap(px)
            self.img1_preview.setText("")
    
    def _select_img2(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image 2", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.img2_path = path
            px = QPixmap(path).scaled(self.img2_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img2_preview.setPixmap(px)
            self.img2_preview.setText("")
    
    def _generate(self):
        mode, quality = self._get_mode()
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
    
    def _on_intermediate(self, ftype, fpath):
        if not fpath or not os.path.exists(fpath):
            return
        
        if ftype == '2d':
            px = QPixmap(fpath).scaled(self.preview_2d.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_2d.setPixmap(px)
            self.preview_2d.setText("")
        elif ftype == 'normal':
            px = QPixmap(fpath).scaled(self.preview_normal.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_normal.setPixmap(px)
            self.preview_normal.setText("")
        elif ftype == 'uv':
            px = QPixmap(fpath).scaled(self.preview_uv.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_uv.setPixmap(px)
            self.preview_uv.setText("")
        elif ftype == 'model':
            self._load_model(self.vtk_widget, fpath)
    
    def _on_done(self, img2d, normal, uv, model):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("Generate")
        self.status.setText("Done")
        
        if img2d and os.path.exists(img2d):
            px = QPixmap(img2d).scaled(self.preview_2d.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_2d.setPixmap(px)
        
        if normal and os.path.exists(normal):
            px = QPixmap(normal).scaled(self.preview_normal.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_normal.setPixmap(px)
        
        if uv and os.path.exists(uv):
            px = QPixmap(uv).scaled(self.preview_uv.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.preview_uv.setPixmap(px)
        
        if model and os.path.exists(model):
            self._load_model(self.vtk_widget, model)
    
    def _on_error(self, msg):
        self.btn_gen.setEnabled(True)
        self.btn_gen.setText("Generate")
        self.progress.setValue(0)
        self.status.setText("Error")
        QMessageBox.critical(self, "Error", msg)
    
    def _load_model(self, widget, path):
        try:
            import trimesh
            import numpy as np
            
            if not os.path.exists(path):
                return
            
            widget.clear()
            widget.add_axes()
            
            mesh = trimesh.load(path, force='scene')
            
            if isinstance(mesh, trimesh.Scene):
                geometries = []
                for g in mesh.geometry.values():
                    geometries.append(g)
                if geometries:
                    mesh = trimesh.util.concatenate(geometries)
            
            if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                pv_mesh = pv.wrap(mesh)
                widget.add_mesh(pv_mesh, color="lightgray")
                widget.reset_camera()
        
        except Exception as e:
            print(f"Load model error: {e}")
    
    def _show_log(self):
        LogWindow(self).show()


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
        
        with open(self.LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
            if len(lines) > 5000:
                lines = lines[-5000:]
            self.log_text.setText('\n'.join(lines))
        
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