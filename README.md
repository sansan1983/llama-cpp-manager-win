# Llama.cpp Manager for Windows

基于 [phucngodev/llama.cpp-manager](https://github.com/phucngodev/llama.cpp-manager) 开发的 Windows 版本，使用 PyQt6 重写。

## 功能特性

- ✅ **系统托盘运行** - 后台运行，不占任务栏
- ▶️ **一键启动/停止** llama.cpp server
- 📋 **复制启动命令** 到剪贴板
- ⚙️ **丰富的配置选项**
  - HuggingFace GGUF 模型
  - 服务器 Host/Port
  - 采样参数 (Temperature, Top-P, Top-K, Min-P)
  - 重复惩罚 (Repeat Penalty, Presence Penalty)
  - Context Size, Threads
  - GPU Layers, mmap 选项
  - Chat Template 支持
- 🔄 **自动下载 llama.cpp** (可选)
- 🚀 **启动时自动开启** 服务器

## 系统要求

- Windows 10/11 (64-bit)
- Python 3.10+ (如从源码运行)
- [llama.cpp](https://github.com/ggerganov/llama.cpp/releases) 二进制文件 (可选，程序可自动下载)

## 安装

### 方式一: 使用预编译版本 (推荐)

1. 从 [Releases](https://github.com/YOUR_USERNAME/llama-cpp-manager-win/releases) 下载最新版本
2. 解压到任意目录
3. 运行 `LlamaCppManager.exe`

### 方式二: 从源码运行

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/llama-cpp-manager-win.git
cd llama-cpp-manager-win

# 安装依赖
pip install -r requirements.txt

# 运行
python src/main.py
```

### 方式三: 打包成 EXE

```bash
pip install pyinstaller
pyinstaller llama_manager.spec
```

## 配置说明

### llama-server 路径

程序会按以下顺序查找 llama-server:

1. 设置中指定的路径
2. 系统 PATH 环境变量
3. 程序同目录下的 `llama-server.exe`

### 自动下载

如果找不到 llama-server，程序会提示你手动下载。你也可以让程序自动从 GitHub 下载最新版本。

下载地址: https://github.com/ggerganov/llama.cpp/releases

推荐下载包含以下关键词的版本:
- `win-vulkan-x64` - Vulkan 加速 (推荐，有显卡加速)
- `win-cublas-x64` - CUDA 加速 (NVIDIA 显卡)
- `win-cpu-x64` - 纯 CPU 版本

### HuggingFace GGUF 模型

程序使用 `-hf` 参数直接从 HuggingFace 下载模型。例如:

- `Jackrong/Qwen3.5-9B-GGUF`
- `meta-llama/Llama-3.1-8B-GGUF`
- `THUDM/glm-4-9b-chat-GGUF`

你可以在 [HuggingFace](https://huggingface.co/models?other=gguf) 找到更多 GGUF 模型。

### Chat Template

某些模型需要特定的 chat template 才能正确对话。你可以使用:

- 程序内置的 qwen.jinja (Qwen 系列)
- 从模型页面下载的模板
- 或者留空使用默认模板

## 项目结构

```
llama-cpp-manager-win/
├── src/
│   ├── main.py              # 主程序入口
│   ├── config_manager.py    # 配置管理
│   ├── process_manager.py   # llama-server 进程管理
│   ├── settings_window.py   # 设置窗口 UI
│   └── download_manager.py  # 自动下载管理器
├── resources/
│   └── qwen.jinja           # Qwen chat template
├── requirements.txt         # Python 依赖
├── build.bat               # Windows 构建脚本
└── README.md
```

## 与 macOS 版的区别

| 功能 | macOS 版 | Windows 版 |
|------|----------|------------|
| UI 框架 | Swift/AppKit | PyQt6 |
| 菜单栏 | macOS 菜单栏 | Windows 系统托盘 |
| 配置存储 | UserDefaults | JSON 文件 |
| 自动下载 | Shell 脚本 | Python 下载器 |

## License

MIT License - 基于原版 llama.cpp-manager 的 MIT License
