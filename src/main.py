"""
Llama.cpp Manager for Windows - 系统托盘主程序
PyQt6 实现 - 菜单栏风格应用
"""
import sys
import os
import threading
import subprocess
import traceback
from pathlib import Path

# 导入 PyQt6
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, 
    QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor

# 导入项目模块
from config_manager import ConfigManager, get_config_path
from process_manager import LlamaProcessManager, ServerState
from settings_window import SettingsWindow


def get_log_path():
    """获取日志文件路径"""
    log_dir = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "LlamaCppManager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def write_log(msg):
    """写日志"""
    try:
        log_path = get_log_path()
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass


def create_default_icon() -> QIcon:
    """创建默认图标 (Llama 主题)"""
    # 创建一个简单的图标
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # 画一个圆形背景
    painter.setBrush(QColor(255, 200, 50))  # 金色
    painter.setPen(Qt.GlobalColor.transparent)
    painter.drawEllipse(4, 4, 56, 56)
    
    # 画一个简单的 "L" 字母
    painter.setPen(QColor(80, 60, 30))
    font = painter.font()
    font.setPixelSize(36)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "L")
    
    painter.end()
    
    icon = QIcon(pixmap)
    return icon


class LlamaCppTrayApp(QApplication):
    """Llama.cpp Manager 系统托盘应用"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # 设置应用信息
        self.setApplicationName("Llama.cpp Manager")
        self.setApplicationDisplayName("Llama.cpp Manager")
        self.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序
        
        # 初始化配置和进程管理器
        self.config_manager = ConfigManager()
        self.process_manager = LlamaProcessManager(self.config_manager)
        
        # 连接信号
        self.process_manager.set_state_changed_callback(self.on_state_changed)
        
        # 初始化 UI
        self.tray_icon = None
        self.settings_window = None
        self._init_tray()
        
        # 自动启动
        if self.config_manager.get("auto_start", True):
            QTimer.singleShot(500, self.start_server)
    
    def _init_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(create_default_icon())
        self.tray_icon.setToolTip("Llama.cpp Manager")
        
        # 创建右键菜单
        self._update_menu()
        
        # 连接信号
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # 显示
        self.tray_icon.show()
    
    def _create_menu(self) -> QMenu:
        """创建右键菜单"""
        menu = QMenu()
        
        # 状态显示
        state = self.process_manager.state
        state_text = {
            ServerState.STOPPED: "○ 已停止",
            ServerState.STARTING: "◉ 启动中...",
            ServerState.RUNNING: "● 运行中",
            ServerState.STOPPING: "◐ 停止中...",
        }.get(state, "○ 已停止")
        
        state_action = QAction(state_text, menu)
        state_action.setEnabled(False)
        menu.addAction(state_action)
        
        # 如果运行中，显示 PID 和端口
        if state == ServerState.RUNNING:
            pid = self.process_manager.get_pid()
            port = self.config_manager.get("port", 8080)
            info_action = QAction(f"   PID: {pid} | Port: {port}", menu)
            info_action.setEnabled(False)
            menu.addAction(info_action)
        
        menu.addSeparator()
        
        # 启动/停止按钮
        if state in (ServerState.STOPPED, ServerState.STOPPING):
            start_action = QAction("▶ 启动服务器", menu)
            start_action.triggered.connect(self.start_server)
            menu.addAction(start_action)
        else:
            stop_action = QAction("⏹ 停止服务器", menu)
            stop_action.triggered.connect(self.stop_server)
            menu.addAction(stop_action)
        
        # 复制命令
        copy_action = QAction("📋 复制命令", menu)
        copy_action.triggered.connect(self.copy_command)
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        # 设置
        settings_action = QAction("⚙ 设置...", menu)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # 检查更新
        update_action = QAction("🔄 检查 llamacpp 更新...", menu)
        update_action.triggered.connect(self.check_llama_update)
        menu.addAction(update_action)
        
        menu.addSeparator()
        
        # 关于
        about_action = QAction("ℹ 关于", menu)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        # 退出
        quit_action = QAction("✕ 退出", menu)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        return menu
    
    def _update_menu(self):
        """更新托盘菜单"""
        menu = self._create_menu()
        self.tray_icon.setContextMenu(menu)
        
        # 更新托盘提示
        state = self.process_manager.state
        if state == ServerState.RUNNING:
            model = self.config_manager.get("model_name", "Unknown")
            self.tray_icon.setToolTip(f"Llama.cpp - {model[:30]}\n运行中")
        else:
            self.tray_icon.setToolTip("Llama.cpp Manager - 已停止")
    
    def on_tray_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # 双击显示/隐藏设置窗口
            if self.settings_window and self.settings_window.isVisible():
                self.settings_window.hide()
            else:
                self.show_settings()
    
    def on_state_changed(self, new_state: ServerState):
        """状态变化回调"""
        self._update_menu()
        
        # 如果设置窗口打开，更新它
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.update_status()
        
        # 运行状态改变时发送系统通知
        if new_state == ServerState.RUNNING:
            self.tray_icon.showMessage(
                "Llama.cpp Manager",
                f"服务器已启动\n模型: {self.config_manager.get('model_name', '')}",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        elif new_state == ServerState.STOPPED:
            self.tray_icon.showMessage(
                "Llama.cpp Manager",
                "服务器已停止",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
    
    def start_server(self):
        """启动服务器"""
        try:
            self.process_manager.start()
            self._update_menu()
        except FileNotFoundError as e:
            QMessageBox.critical(
                None,  # parent
                "错误",
                f"找不到 llama-server 可执行文件！\n\n"
                f"请在设置中指定 llama-server 的路径，\n"
                f"或者将 llama-server 添加到系统 PATH。\n\n"
                f"你可以从这里下载: https://github.com/ggerganov/llama.cpp/releases"
            )
            self.show_settings()
        except Exception as e:
            QMessageBox.critical(None, "错误", f"启动服务器失败:\n{str(e)}")
    
    def stop_server(self):
        """停止服务器"""
        try:
            self.process_manager.stop()
            self._update_menu()
        except Exception as e:
            QMessageBox.critical(None, "错误", f"停止服务器失败:\n{str(e)}")
    
    def copy_command(self):
        """复制命令到剪贴板"""
        command = self.process_manager.get_command_string()
        clipboard = self.clipboard()
        clipboard.setText(command)
        
        self.tray_icon.showMessage(
            "已复制",
            "启动命令已复制到剪贴板",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
    
    def show_settings(self):
        """显示设置窗口"""
        if not self.settings_window:
            self.settings_window = SettingsWindow(
                self.config_manager, 
                self.process_manager
            )
            self.settings_window.settings_changed.connect(self._on_settings_changed)
        
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
    
    def _on_settings_changed(self):
        """设置变化回调"""
        self._update_menu()
    
    def check_llama_update(self):
        """检查 llamacpp 更新"""
        QMessageBox.information(
            None,
            "检查更新",
            "请访问 https://github.com/ggerganov/llama.cpp/releases\n"
            "下载最新的 llama.cpp 二进制文件。\n\n"
            "下载后，在设置中更新 llama-server 路径。"
        )
    
    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            None,
            "关于 Llama.cpp Manager",
            "<h3>Llama.cpp Manager</h3>"
            "<p>版本 1.0.0</p>"
            "<p>Windows 版</p>"
            "<p>基于 PyQt6 开发</p>"
            "<p>---</p>"
            "<p>一个轻量级的 llama.cpp 服务器管理工具，"
            "让你轻松管理 HuggingFace 上的 GGUF 模型。</p>"
            "<p>---</p>"
            "<p><b>原版 macOS:</b> phucngodev/llama.cpp-manager</p>"
        )
    
    def quit_app(self):
        """退出应用"""
        # 先停止服务器
        if self.process_manager.state in (ServerState.RUNNING, ServerState.STARTING):
            self.process_manager.stop()
        
        # 退出
        self.quit()


def main():
    """主入口"""
    # 启用高 DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = LlamaCppTrayApp(sys.argv)
    
    # 设置样式
    app.setStyle("Fusion")
    
    return app.exec()


if __name__ == "__main__":
    try:
        write_log("Application starting...")
        ret = main()
        write_log(f"Application exited with code: {ret}")
        sys.exit(ret)
    except Exception as e:
        error_msg = f"FATAL ERROR: {e}\n{traceback.format_exc()}"
        write_log(error_msg)
        print(error_msg, file=sys.stderr)
        input("按回车键退出...")  # 防止窗口一闪而过
        sys.exit(1)
