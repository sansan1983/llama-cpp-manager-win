"""
Llama.cpp Manager for Windows - 配置管理
基于 JSON 的配置持久化
"""
import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


def get_config_path() -> Path:
    """获取配置文件路径"""
    config_dir = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "LlamaCppManager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


@dataclass
class LlamaConfig:
    # 模型配置
    model_name: str = "Jackrong/Qwen3.5-9B-GGUF"
    chat_template_file: str = ""
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8080
    
    # 采样参数
    context_size: int = 65536
    temperature: float = 0.6
    top_p: float = 0.95
    top_k: int = 20
    min_p: float = 0.0
    repeat_penalty: float = 1.0
    presence_penalty: float = 0.0
    
    # 性能参数
    num_threads: int = 4
    gpu_layers: int = 99
    
    # 行为选项
    auto_start: bool = True
    no_webui: bool = True
    mmap_enabled: bool = False
    
    # llama.cpp 路径
    llama_bin_path: str = ""  # 空表示从 PATH 或同目录获取


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "model_name": "Jackrong/Qwen3.5-9B-GGUF",
        "chat_template_file": "",
        "host": "0.0.0.0",
        "port": 8080,
        "context_size": 65536,
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "repeat_penalty": 1.0,
        "presence_penalty": 0.0,
        "num_threads": 4,
        "gpu_layers": 99,
        "auto_start": True,
        "no_webui": True,
        "mmap_enabled": False,
        "llama_bin_path": "",
    }
    
    def __init__(self):
        self.config_path = get_config_path()
        self.config: dict = {}
        self.load()
    
    def load(self) -> None:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                # 合并默认配置（防止新版本新增字段）
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except (json.JSONDecodeError, IOError):
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
    
    def save(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value) -> None:
        self.config[key] = value
        self.save()
    
    def update(self, **kwargs) -> None:
        self.config.update(kwargs)
        self.save()
    
    def get_llama_config(self) -> LlamaConfig:
        """获取 LlamaConfig 对象"""
        return LlamaConfig(**{k.replace("_", ""): v for k, v in self.config.items()})
    
    def reset_defaults(self) -> None:
        """重置为默认配置"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
