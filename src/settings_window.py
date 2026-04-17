"""
Llama.cpp Manager for Windows - 设置窗口
使用 PyQt6 实现参数配置界面
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QGroupBox, QScrollArea,
    QMessageBox, QFileDialog, QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SettingsWindow(QWidget):
    """设置窗口"""
    
    settings_changed = pyqtSignal()
    
    def __init__(self, config_manager, process_manager):
        super().__init__()
        self.config_manager = config_manager
        self.process_manager = process_manager
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Llama.cpp Manager - 设置")
        self.setMinimumSize(550, 500)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        tabs = QTabWidget()
        tabs.addTab(self._create_model_tab(), "模型配置")
        tabs.addTab(self._create_server_tab(), "服务器配置")
        tabs.addTab(self._create_sampling_tab(), "采样参数")
        tabs.addTab(self._create_advanced_tab(), "高级选项")
        
        layout.addWidget(tabs)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        download_btn = QPushButton("下载 llama.cpp...")
        download_btn.clicked.connect(self.download_llama)
        button_layout.addWidget(download_btn)
        
        reset_btn = QPushButton("重置默认")
        reset_btn.clicked.connect(self.reset_defaults)
        button_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_model_tab(self) -> QWidget:
        """模型配置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 模型名称
        model_group = QGroupBox("HuggingFace GGUF 模型")
        model_layout = QVBoxLayout()
        
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("模型名称:"))
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("例如: Jackrong/Qwen3.5-9B-GGUF")
        model_row.addWidget(self.model_name_edit)
        model_layout.addLayout(model_row)
        
        model_info = QLabel("从 HuggingFace 下载 GGUF 格式模型\n"
                            "例如: Qwen, Llama, GLM, Phi 等模型都有 GGUF 格式")
        model_info.setStyleSheet("color: gray; font-size: 11px;")
        model_layout.addWidget(model_info)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Chat Template
        template_group = QGroupBox("Chat Template (可选)")
        template_layout = QVBoxLayout()
        
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("模板文件:"))
        self.template_edit = QLineEdit()
        self.template_edit.setPlaceholderText("自定义 chat template 文件路径 (.jinja)")
        template_row.addWidget(self.template_edit)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_template)
        template_row.addWidget(browse_btn)
        template_layout.addLayout(template_row)
        
        template_info = QLabel("某些模型需要特定的 chat template 才能正确对话\n"
                              "Qwen 系列模型请使用 qwen.jinja")
        template_info.setStyleSheet("color: gray; font-size: 11px;")
        template_layout.addWidget(template_info)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        layout.addStretch()
        return widget
    
    def _create_server_tab(self) -> QWidget:
        """服务器配置页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 服务器设置
        server_group = QGroupBox("服务器设置")
        server_layout = QGridLayout()
        
        server_layout.addWidget(QLabel("Host:"), 0, 0)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("0.0.0.0")
        server_layout.addWidget(self.host_edit, 0, 1)
        
        server_layout.addWidget(QLabel("Port:"), 0, 2)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setPrefix("")
        server_layout.addWidget(self.port_spin, 0, 3)
        
        server_layout.addWidget(QLabel("llama-server 路径:"), 1, 0)
        self.llama_path_edit = QLineEdit()
        self.llama_path_edit.setPlaceholderText("留空则从 PATH 或同目录查找")
        server_layout.addWidget(self.llama_path_edit, 1, 1, 1, 2)
        
        browse_llama_btn = QPushButton("浏览...")
        browse_llama_btn.clicked.connect(self.browse_llama)
        server_layout.addWidget(browse_llama_btn, 1, 3)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # 行为选项
        behavior_group = QGroupBox("行为选项")
        behavior_layout = QVBoxLayout()
        
        self.auto_start_check = QCheckBox("启动时自动开启服务器")
        behavior_layout.addWidget(self.auto_start_check)
        
        self.no_webui_check = QCheckBox("禁用 Web UI (--no-webui)")
        behavior_layout.addWidget(self.no_webui_check)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return widget
    
    def _create_sampling_tab(self) -> QWidget:
        """采样参数页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 上下文
        context_group = QGroupBox("上下文设置")
        context_layout = QGridLayout()
        
        context_layout.addWidget(QLabel("Context Size (-c):"), 0, 0)
        self.context_spin = QSpinBox()
        self.context_spin.setRange(512, 1048576)
        self.context_spin.setSingleStep(512)
        self.context_spin.setSuffix(" tokens")
        context_layout.addWidget(self.context_spin, 0, 1)
        
        context_layout.addWidget(QLabel("Threads:"), 0, 2)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 128)
        context_layout.addWidget(self.threads_spin, 0, 3)
        
        context_group.setLayout(context_layout)
        layout.addWidget(context_group)
        
        # 采样参数
        sampling_group = QGroupBox("采样参数")
        sampling_layout = QGridLayout()
        
        sampling_layout.addWidget(QLabel("Temperature:"), 0, 0)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setDecimals(2)
        sampling_layout.addWidget(self.temp_spin, 0, 1)
        
        sampling_layout.addWidget(QLabel("Top-P:"), 0, 2)
        self.topp_spin = QDoubleSpinBox()
        self.topp_spin.setRange(0.0, 1.0)
        self.topp_spin.setSingleStep(0.05)
        self.topp_spin.setDecimals(2)
        sampling_layout.addWidget(self.topp_spin, 0, 3)
        
        sampling_layout.addWidget(QLabel("Top-K:"), 1, 0)
        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(1, 200)
        sampling_layout.addWidget(self.topk_spin, 1, 1)
        
        sampling_layout.addWidget(QLabel("Min-P:"), 1, 2)
        self.minp_spin = QDoubleSpinBox()
        self.minp_spin.setRange(0.0, 1.0)
        self.minp_spin.setSingleStep(0.05)
        self.minp_spin.setDecimals(2)
        sampling_layout.addWidget(self.minp_spin, 1, 3)
        
        sampling_group.setLayout(sampling_layout)
        layout.addWidget(sampling_group)
        
        # 惩罚参数
        penalty_group = QGroupBox("重复惩罚")
        penalty_layout = QGridLayout()
        
        penalty_layout.addWidget(QLabel("Repeat Penalty:"), 0, 0)
        self.repeat_penalty_spin = QDoubleSpinBox()
        self.repeat_penalty_spin.setRange(0.0, 2.0)
        self.repeat_penalty_spin.setSingleStep(0.05)
        self.repeat_penalty_spin.setDecimals(2)
        penalty_layout.addWidget(self.repeat_penalty_spin, 0, 1)
        
        penalty_layout.addWidget(QLabel("Presence Penalty:"), 0, 2)
        self.presence_penalty_spin = QDoubleSpinBox()
        self.presence_penalty_spin.setRange(-2.0, 2.0)
        self.presence_penalty_spin.setSingleStep(0.05)
        self.presence_penalty_spin.setDecimals(2)
        penalty_layout.addWidget(self.presence_penalty_spin, 0, 3)
        
        penalty_group.setLayout(penalty_layout)
        layout.addWidget(penalty_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """高级选项页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # GPU 设置
        gpu_group = QGroupBox("GPU 设置")
        gpu_layout = QVBoxLayout()
        
        self.mmap_check = QCheckBox("使用 mmap 内存映射 (--mmap)")
        gpu_layout.addWidget(self.mmap_check)
        
        mmap_note = QLabel("启用 mmap 可以减少内存占用，但会略微降低性能\n"
                          "如果你的 GPU 显存不够，可以启用 mmap 并将 -ngl 设为 0")
        mmap_note.setStyleSheet("color: gray; font-size: 11px;")
        gpu_layout.addWidget(mmap_note)
        
        gpu_layout.addWidget(QLabel("GPU Layers (-ngl):"))
        self.gpu_layers_spin = QSpinBox()
        self.gpu_layers_spin.setRange(0, 999)
        self.gpu_layers_spin.setSuffix(" 层")
        gpu_layout.addWidget(self.gpu_layers_spin)
        
        gpu_group.setLayout(gpu_layout)
        layout.addWidget(gpu_group)
        
        # 状态信息
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("状态: 未启动")
        status_layout.addWidget(self.status_label)
        
        self.pid_label = QLabel("PID: -")
        status_layout.addWidget(self.pid_label)
        
        self.model_status_label = QLabel("模型: -")
        status_layout.addWidget(self.model_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        return widget
    
    def load_settings(self):
        """加载配置到 UI"""
        config = self.config_manager.config
        
        # 模型配置
        self.model_name_edit.setText(config.get("model_name", ""))
        self.template_edit.setText(config.get("chat_template_file", ""))
        
        # 服务器配置
        self.host_edit.setText(config.get("host", "0.0.0.0"))
        self.port_spin.setValue(config.get("port", 8080))
        self.llama_path_edit.setText(config.get("llama_bin_path", ""))
        
        # 行为选项
        self.auto_start_check.setChecked(config.get("auto_start", True))
        self.no_webui_check.setChecked(config.get("no_webui", True))
        
        # 采样参数
        self.context_spin.setValue(config.get("context_size", 65536))
        self.threads_spin.setValue(config.get("num_threads", 4))
        self.temp_spin.setValue(config.get("temperature", 0.6))
        self.topp_spin.setValue(config.get("top_p", 0.95))
        self.topk_spin.setValue(config.get("top_k", 20))
        self.minp_spin.setValue(config.get("min_p", 0.0))
        self.repeat_penalty_spin.setValue(config.get("repeat_penalty", 1.0))
        self.presence_penalty_spin.setValue(config.get("presence_penalty", 0.0))
        
        # 高级选项
        self.mmap_check.setChecked(config.get("mmap_enabled", False))
        self.gpu_layers_spin.setValue(config.get("gpu_layers", 99))
        
        self.update_status()
    
    def save_settings(self):
        """保存 UI 配置"""
        config = self.config_manager.config
        
        # 模型配置
        config["model_name"] = self.model_name_edit.text().strip()
        config["chat_template_file"] = self.template_edit.text().strip()
        
        # 服务器配置
        config["host"] = self.host_edit.text().strip()
        config["port"] = self.port_spin.value()
        config["llama_bin_path"] = self.llama_path_edit.text().strip()
        
        # 行为选项
        config["auto_start"] = self.auto_start_check.isChecked()
        config["no_webui"] = self.no_webui_check.isChecked()
        
        # 采样参数
        config["context_size"] = self.context_spin.value()
        config["num_threads"] = self.threads_spin.value()
        config["temperature"] = self.temp_spin.value()
        config["top_p"] = self.topp_spin.value()
        config["top_k"] = self.topk_spin.value()
        config["min_p"] = self.minp_spin.value()
        config["repeat_penalty"] = self.repeat_penalty_spin.value()
        config["presence_penalty"] = self.presence_penalty_spin.value()
        
        # 高级选项
        config["mmap_enabled"] = self.mmap_check.isChecked()
        config["gpu_layers"] = self.gpu_layers_spin.value()
        
        self.config_manager.save()
        self.settings_changed.emit()
        
        QMessageBox.information(self, "保存成功", "设置已保存！")
    
    def reset_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_defaults()
            self.load_settings()
            self.settings_changed.emit()
    
    def browse_template(self):
        """浏览 chat template 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Chat Template 文件",
            "",
            "Jinja Files (*.jinja);;All Files (*)"
        )
        if file_path:
            self.template_edit.setText(file_path)
    
    def browse_llama(self):
        """浏览 llama-server 可执行文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 llama-server 可执行文件",
            "",
            "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.llama_path_edit.setText(file_path)
    
    def download_llama(self):
        """下载 llama.cpp"""
        from download_manager import auto_download_llama
        
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowTitle("下载 llama.cpp")
        progress_dialog.setText("正在从 GitHub 下载 llama.cpp...\n\n请稍候，这可能需要几分钟时间。")
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.NoButton)
        progress_dialog.show()
        
        def progress(percent, status):
            progress_dialog.setInformativeText(f"{percent}% - {status}")
            QApplication.processEvents()
        
        result = auto_download_llama(progress_callback=progress)
        
        progress_dialog.close()
        
        if result:
            self.llama_path_edit.setText(str(result))
            QMessageBox.information(
                self, "下载完成",
                f"llama.cpp 下载完成！\n\n路径: {result}\n\n"
                f"已自动保存到设置中。"
            )
        else:
            QMessageBox.critical(
                self, "下载失败",
                "无法下载 llama.cpp。\n\n"
                "请手动下载: https://github.com/ggerganov/llama.cpp/releases\n\n"
                "推荐下载:\n"
                "- Vulkan 版本 (有显卡加速): llama-*-bin-win-vulkan-x64.zip\n"
                "- CUDA 版本 (NVIDIA): llama-*-bin-win-cublas-x64.zip\n"
                "- CPU 版本: llama-*-bin-win-cpu-x64.zip"
            )
    
    def update_status(self):
        """更新状态显示"""
        state = self.process_manager.state
        state_text = {
            "stopped": "未启动",
            "starting": "启动中...",
            "running": "运行中",
            "stopping": "停止中..."
        }.get(state.value, state.value)
        
        self.status_label.setText(f"状态: {state_text}")
        
        pid = self.process_manager.get_pid()
        self.pid_label.setText(f"PID: {pid if pid else '-'}")
        
        model = self.config_manager.get("model_name", "-")
        self.model_status_label.setText(f"模型: {model}")
