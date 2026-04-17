"""
Llama.cpp Manager for Windows - 自动下载管理器
自动下载 llama.cpp 最新 release 的 bin 文件
"""
import os
import sys
import re
import requests
import zipfile
import tarfile
import shutil
import tempfile
import platform
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass


@dataclass
class LlamaAsset:
    name: str
    download_url: str
    size: int
    asset_type: str  # 'vulkan', 'cublas', 'openblas', 'cpu'


class LlamaDownloadManager:
    """llama.cpp 下载管理器"""
    
    RELEASES_API = "https://api.github.com/repos/ggerganov/llama.cpp/releases/latest"
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "LlamaCppManager-Windows/1.0"
        })
    
    def _report_progress(self, current: int, total: int, status: str = ""):
        """报告下载进度"""
        if self.progress_callback:
            percent = int(current * 100 / total) if total > 0 else 0
            self.progress_callback(percent, status)
    
    def _get_platform_key(self) -> str:
        """获取当前平台标识"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            return "win-x64"
        elif system == "darwin":
            if machine == "arm64":
                return "osx-arm64"
            return "osx-x64"
        else:
            return "linux-x64"
    
    def _detect_gpu_acceleration(self) -> str:
        """检测 GPU 加速类型"""
        # 检查 NVIDIA CUDA
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return "cublas"
        except:
            pass
        
        # 检查 Vulkan (Windows)
        if sys.platform == "win32":
            try:
                import subprocess
                result = subprocess.run(
                    ["vulkaninfo", "--summary"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return "vulkan"
            except:
                pass
        
        return "cpu"
    
    def get_latest_release_info(self) -> Optional[Tuple[str, List[LlamaAsset]]]:
        """获取最新 release 信息和所有 assets"""
        try:
            response = self.session.get(self.RELEASES_API, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            version = data.get("tag_name", "").lstrip("b")
            assets = data.get("assets", [])
            
            llama_assets: List[LlamaAsset] = []
            
            for asset in assets:
                name = asset.get("name", "").lower()
                
                # 跳过非二进制文件
                if not name.endswith((".zip", ".tar.gz")):
                    continue
                
                # 确定 GPU 类型
                asset_type = "cpu"
                if "vulkan" in name:
                    asset_type = "vulkan"
                elif "cublas" in name or "cuda" in name:
                    asset_type = "cublas"
                elif "openblas" in name or "blas" in name:
                    asset_type = "openblas"
                
                # 确定平台
                platform_match = None
                for plat in ["win", "linux", "darwin", "osx"]:
                    if plat in name:
                        platform_match = plat
                        break
                
                if not platform_match:
                    continue
                
                # 确定架构
                arch_match = None
                for arch in ["x64", "x86_64", "arm64", "aarch64"]:
                    if arch in name:
                        arch_match = arch
                        break
                
                if not arch_match:
                    continue
                
                # 只保留当前平台的
                current_plat = "win" if sys.platform == "win32" else ("darwin" if sys.platform == "darwin" else "linux")
                if platform_match != current_plat:
                    continue
                
                llama_assets.append(LlamaAsset(
                    name=asset.get("name"),
                    download_url=asset.get("browser_download_url"),
                    size=asset.get("size", 0),
                    asset_type=asset_type
                ))
            
            return version, llama_assets
            
        except requests.RequestException as e:
            print(f"获取 release 信息失败: {e}")
            return None
    
    def get_best_asset(self, assets: List[LlamaAsset]) -> Optional[LlamaAsset]:
        """选择最佳资产（根据 GPU 加速类型）"""
        if not assets:
            return None
        
        preferred_order = ["cublas", "vulkan", "openblas", "cpu"]
        
        # 先按 GPU 类型筛选
        for accel_type in preferred_order:
            for asset in assets:
                if asset.asset_type == accel_type:
                    return asset
        
        return assets[0] if assets else None
    
    def download_and_extract(
        self, 
        version: str,
        asset: LlamaAsset, 
        dest_dir: Path,
        check_existing: bool = True
    ) -> bool:
        """
        下载并解压 llama.cpp bin 文件
        """
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已有 llama-server
        if check_existing:
            existing = self._find_existing_llama(dest_dir)
            if existing:
                print(f"发现已有的 llama: {existing}")
                return True
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            archive_path = tmp_path / asset.name
            
            # 确定压缩格式
            is_tar_gz = asset.name.endswith(".tar.gz")
            
            # 下载
            self._report_progress(0, 100, f"正在下载 llama.cpp {version}...")
            
            try:
                response = self.session.get(
                    asset.download_url,
                    stream=True,
                    timeout=600
                )
                response.raise_for_status()
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(archive_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size:
                                mb = downloaded // (1024 * 1024)
                                total_mb = total_size // (1024 * 1024)
                                self._report_progress(
                                    int(downloaded * 100 / total_size),
                                    100,
                                    f"已下载 {mb}/{total_mb} MB"
                                )
                
                self._report_progress(100, 100, "正在解压...")
                
                # 解压
                if is_tar_gz:
                    with tarfile.open(archive_path, "r:gz") as tar_ref:
                        tar_ref.extractall(dest_dir)
                else:
                    with zipfile.ZipFile(archive_path, "r") as zip_ref:
                        zip_ref.extractall(dest_dir)
                
                self._report_progress(100, 100, "完成!")
                
                return True
                
            except requests.RequestException as e:
                print(f"下载失败: {e}")
                return False
            except Exception as e:
                print(f"解压失败: {e}")
                return False
    
    def _find_existing_llama(self, search_dir: Path) -> Optional[Path]:
        """查找已有的 llama 可执行文件"""
        names = [
            "llama-server.exe", "llama-server", 
            "llama-cli.exe", "llama-cli",
            "build\\bin\\llama-server.exe",  # 从源码编译的路径
        ]
        for name in names:
            for p in search_dir.rglob(name):
                return p
            direct = search_dir / name
            if direct.exists():
                return direct
        return None
    
    def get_dest_dir(self) -> Path:
        """获取默认安装目录"""
        if sys.platform == "win32":
            base = Path(os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home()
        
        return base / "LlamaCppManager" / "bin"


def auto_download_llama(
    progress_callback: Optional[Callable] = None,
    force: bool = False,
    gpu_type: str = "auto"
) -> Optional[Path]:
    """
    自动下载 llama.cpp
    
    Args:
        progress_callback: 进度回调 (percent, status)
        force: 是否强制重新下载
        gpu_type: GPU 加速类型 ('auto', 'cublas', 'vulkan', 'openblas', 'cpu')
    
    Returns:
        llama-server 路径，失败返回 None
    """
    manager = LlamaDownloadManager(progress_callback)
    
    # 获取最新 release
    info = manager.get_latest_release_info()
    if not info:
        print("无法获取 llama.cpp release 信息")
        return None
    
    version, assets = info
    print(f"发现版本: {version}")
    print(f"可用资产: {[a.name for a in assets]}")
    
    if gpu_type == "auto":
        gpu_type = manager._detect_gpu_acceleration()
        print(f"检测到 GPU 加速: {gpu_type}")
    
    # 按 GPU 类型筛选
    filtered = [a for a in assets if a.asset_type == gpu_type]
    if not filtered:
        filtered = assets  # 回退到所有资产
    
    asset = manager.get_best_asset(filtered)
    if not asset:
        print(f"没有找到适合 {gpu_type} 的资产")
        return None
    
    print(f"选择资产: {asset.name}")
    
    dest_dir = manager.get_dest_dir()
    
    success = manager.download_and_extract(version, asset, dest_dir, check_existing=not force)
    
    if success:
        found = manager._find_existing_llama(dest_dir)
        return found
    
    return None


if __name__ == "__main__":
    def progress(percent, status):
        print(f"\r{percent}% - {status}", end="", flush=True)
    
    print("开始下载 llama.cpp...")
    result = auto_download_llama(progress_callback=progress)
    
    if result:
        print(f"\n下载完成: {result}")
    else:
        print("\n下载失败")
