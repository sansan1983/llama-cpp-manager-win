"""
Llama.cpp Manager for Windows - llama-server 进程管理
"""
import subprocess
import os
import sys
import threading
import time
import signal
from pathlib import Path
from typing import Optional, List
from enum import Enum

import requests


class ServerState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


class LlamaProcessManager:
    """管理 llama-server 进程的类"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.process: Optional[subprocess.Popen] = None
        self.state = ServerState.STOPPED
        self.state_changed_callback = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def set_state_changed_callback(self, callback):
        """设置状态变化回调"""
        self.state_changed_callback = callback
    
    def _set_state(self, new_state: ServerState):
        """更新状态并触发回调"""
        if self.state != new_state:
            self.state = new_state
            if self.state_changed_callback:
                self.state_changed_callback(new_state)
    
    def _find_llama_server(self) -> Optional[str]:
        """查找 llama-server 可执行文件"""
        config_path = self.config_manager.get("llama_bin_path", "")
        
        if config_path and os.path.exists(config_path):
            return config_path
        
        # 尝试从 PATH 中查找
        for name in ["llama-server.exe", "llama-server", "llama-cli.exe", "llama-cli"]:
            # 在 Windows 上先尝试 PATH
            path = self._find_in_path(name)
            if path:
                return path
        
        # 尝试同目录
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包的情况
            app_dir = Path(sys.executable).parent
            for name in ["llama-server.exe", "llama-server", "llama-cli.exe", "llama-cli"]:
                candidate = app_dir / name
                if candidate.exists():
                    return str(candidate)
        
        return None
    
    def _find_in_path(self, name: str) -> Optional[str]:
        """在 PATH 中查找可执行文件"""
        path_env = os.environ.get("PATH", "")
        for dir_path in path_env.split(os.pathsep):
            candidate = Path(dir_path) / name
            if candidate.exists():
                return str(candidate)
            # Windows 可能不带 .exe
            if sys.platform == "win32" and not name.endswith(".exe"):
                candidate_exe = Path(dir_path) / (name + ".exe")
                if candidate_exe.exists():
                    return str(candidate_exe)
        return None
    
    def build_command(self) -> List[str]:
        """构建 llama-server 启动命令"""
        config = self.config_manager.config
        
        llama_path = self._find_llama_server()
        if not llama_path:
            raise FileNotFoundError("llama-server not found!")
        
        cmd = [llama_path]
        
        # 模型 - 从 HuggingFace
        cmd.extend(["-hf", config["model_name"]])
        cmd.append("--no-mmproj")
        
        # GPU 层数
        if config["mmap_enabled"]:
            cmd.extend(["-ngl", "0", "--mmap"])
        else:
            cmd.extend(["-ngl", str(config["gpu_layers"])])
        
        # 服务器配置
        cmd.extend([
            "--host", config["host"],
            "--port", str(config["port"]),
        ])
        
        # 采样参数
        cmd.extend([
            "-c", str(config["context_size"]),
            "-fa",  # Flash Attention
            "--temp", str(config["temperature"]),
            "--top-p", str(config["top_p"]),
            "--top-k", str(config["top_k"]),
            "--min-p", str(config["min_p"]),
            "--repeat-penalty", str(config["repeat_penalty"]),
            "--presence-penalty", str(config["presence_penalty"]),
            "--threads", str(config["num_threads"]),
        ])
        
        # Web UI
        if config["no_webui"]:
            cmd.append("--no-webui")
        
        # Chat Template
        if config.get("chat_template_file"):
            cmd.extend(["--chat-template-file", config["chat_template_file"]])
            cmd.append("--jinja")
        
        return cmd
    
    def get_command_string(self) -> str:
        """获取命令字符串（用于复制）"""
        try:
            cmd_list = self.build_command()
            return subprocess.list2cmdline(cmd_list)
        except FileNotFoundError as e:
            return f"# Error: {e}"
    
    def _is_server_responding(self) -> bool:
        """检查服务器是否响应"""
        config = self.config_manager.config
        host = config["host"]
        port = config["port"]
        url = f"http://{host}:{port}/health"
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            # 可能服务器还没完全启动，尝试其他端点
            try:
                url = f"http://{host}:{port}/v1/models"
                response = requests.get(url, timeout=2)
                return response.status_code == 200
            except:
                return False
    
    def _monitor_server(self):
        """监控服务器状态"""
        while not self._stop_event.is_set():
            if self.process and self.process.poll() is None:
                # 进程还在运行
                if self._is_server_responding():
                    self._set_state(ServerState.RUNNING)
                else:
                    self._set_state(ServerState.STARTING)
            else:
                # 进程已退出
                if self.state != ServerState.STOPPED:
                    self._set_state(ServerState.STOPPED)
                break
            
            self._stop_event.wait(timeout=1.0)
    
    def start(self) -> bool:
        """启动 llama-server"""
        if self.state in (ServerState.RUNNING, ServerState.STARTING):
            return False
        
        try:
            self._set_state(ServerState.STARTING)
            
            cmd = self.build_command()
            
            # 创建新进程组（Windows）
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                creation_flags = 0
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                cwd=os.path.dirname(cmd[0]) if os.path.dirname(cmd[0]) else None,
            )
            
            # 启动监控线程
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_server, daemon=True)
            self._monitor_thread.start()
            
            return True
            
        except FileNotFoundError as e:
            self._set_state(ServerState.STOPPED)
            raise e
        except Exception as e:
            self._set_state(ServerState.STOPPED)
            raise e
    
    def stop(self) -> bool:
        """停止 llama-server"""
        if self.state == ServerState.STOPPED:
            return True
        
        self._set_state(ServerState.STOPPING)
        
        try:
            if self.process:
                if sys.platform == "win32":
                    # Windows: 发送 CTRL_BREAK_EVENT 或使用 taskkill
                    try:
                        # 先尝试优雅终止
                        self.process.terminate()
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        # 强制杀死
                        self.process.kill()
                        self.process.wait(timeout=2)
                else:
                    # Unix-like
                    self.process.send_signal(signal.SIGTERM)
                    try:
                        self.process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                
                self.process = None
            
            self._stop_event.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2)
            
            self._set_state(ServerState.STOPPED)
            return True
            
        except Exception as e:
            self._set_state(ServerState.STOPPED)
            return False
    
    def is_running(self) -> bool:
        """检查服务器是否运行"""
        return self.state == ServerState.RUNNING
    
    def get_pid(self) -> Optional[int]:
        """获取进程 PID"""
        return self.process.pid if self.process else None
