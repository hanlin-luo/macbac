# macbac - MacOS Backup and Migration

`macbac` 是一款旨在简化 macOS 用户在新设备上恢复其工作环境的命令行工具。通过备份旧 Mac 上的应用程序列表、配置和关键数据，`macbac` 能够帮助用户快速、高效地在新 Mac 上完成环境设置。

## 功能特性

- 🍎 **App Store 应用备份**: 自动识别并备份从 App Store 安装的应用程序列表
- 🍺 **Homebrew 生态备份**: 生成完整的 Brewfile，包含所有 taps、formulae 和 casks
- 🛠️ **开发环境配置**: 备份常见的开发工具配置文件（Git、Shell、SSH 等）
- ✍️ **自定义字体**: 备份用户安装的所有自定义字体文件
- 📦 **手动安装应用**: 识别并记录非 App Store、非 Homebrew 的手动安装应用
- 📋 **清晰的备份清单**: 生成易读的 Markdown 格式备份报告

## 安装

### 使用 uv（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd python-xp-macbac

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 安装为可执行命令
uv pip install -e .
```

### 使用 pip

```bash
# 克隆项目
git clone <repository-url>
cd python-xp-macbac

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .
```

## 使用方法

### 基本备份

```bash
# 使用默认输出目录 (~/macbac_backups)
macbac backup

# 指定自定义输出目录
macbac backup --output /path/to/backup/directory
```

### 备份输出结构

备份完成后，会在指定目录下创建一个带时间戳的备份文件夹：

```
~/macbac_backups/
└── macbac_backup_20250806_221500/
    ├── configs/
    │   ├── .gitconfig
    │   ├── .zshrc
    │   └── ...
    ├── fonts/
    │   ├── CustomFont.ttf
    │   └── ...
    └── inventory.md
```

### 备份清单示例

`inventory.md` 文件包含完整的备份清单：

````markdown
# macbac Backup Inventory

- **Backup Date:** 2025-08-06 22:15:00
- **macOS Version:** 15.0.0

## 🍎 App Store & Sandboxed Applications

| ID         | Name      |
| ---------- | --------- |
| 497799835  | Xcode     |
| 1444383602 | GoodNotes |

## 🍺 Homebrew Ecosystem (Brewfile)

```brewfile
tap "homebrew/bundle"
brew "git"
brew "python@3.13"
cask "visual-studio-code"
```
````

## 🛠️ Development Environment & Toolchain

- `~/.gitconfig`
- `~/.zshrc`

## ✍️ Custom Fonts

- `CustomFont.ttf`

## 📦 Manually Installed Applications

| Application Name | Path                           |
| ---------------- | ------------------------------ |
| Sublime Text.app | /Applications/Sublime Text.app |

````

## 依赖要求

### 可选依赖

为了获得最佳体验，建议安装以下工具：

- **mas**: 用于获取 App Store 应用列表
  ```bash
  brew install mas
````

- **Homebrew**: 用于生成 Brewfile
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

## 开发

### 设置开发环境

```bash
# 克隆项目
git clone <repository-url>
cd python-xp-macbac

# 使用 uv 安装开发依赖
uv sync --dev

# 激活虚拟环境
source .venv/bin/activate
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_backup.py

# 运行测试并显示覆盖率
pytest --cov=macbac
```

### 代码质量检查

```bash
# 代码格式化和 linting
ruff check .
ruff format .

# 类型检查
mypy .
```

## 项目结构

```
macbac/
├── macbac/
│   ├── __init__.py
│   ├── cli.py              # 命令行接口
│   ├── backup.py           # 备份管理器
│   ├── storage.py          # 存储管理器
│   └── scanners/           # 扫描器模块
│       ├── __init__.py
│       ├── appstore_scanner.py
│       ├── homebrew_scanner.py
│       ├── dev_env_scanner.py
│       ├── font_scanner.py
│       └── manual_app_scanner.py
├── tests/
│   ├── __init__.py
│   └── test_backup.py
├── pyproject.toml
├── README.md
└── spec.md
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 未来计划

- 🔄 **恢复功能**: 实现 `macbac restore` 命令
- 🖥️ **图形界面**: 为非技术用户提供 GUI
- ☁️ **云同步**: 支持云存储服务集成
- 📈 **增量备份**: 实现增量备份功能
