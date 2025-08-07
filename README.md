# macbac - MacOS Backup and Migration

`macbac` 是一款旨在简化 macOS 用户在新设备上恢复其工作环境的命令行工具。通过备份旧 Mac 上的应用程序列表、配置和关键数据，并提供一键恢复功能，`macbac` 能够帮助用户快速、高效地在新 Mac 上完成环境设置。

## 功能特性

### 备份功能

- 🍎 **App Store 应用备份**: 自动识别并备份从 App Store 安装的应用程序列表
- 🍺 **Homebrew 生态备份**: 生成完整的 Brewfile，包含所有 taps、formulae 和 casks
- 🛠️ **开发环境检测**: 检测已安装的开发工具及其版本信息
- ✍️ **自定义字体**: 备份用户安装的所有自定义字体文件
- 📦 **手动安装应用**: 识别并记录非 App Store、非 Homebrew 的手动安装应用
- 📋 **清晰的备份清单**: 生成易读的 Markdown 格式备份报告和机器可读的 manifest.json

### 恢复功能 🆕

- 🔄 **App Store 应用恢复**: 使用 `mas` 工具自动安装备份的 App Store 应用
- 🍺 **Homebrew 包恢复**: 使用 Brewfile 一键恢复所有 Homebrew 包和应用
- ✍️ **字体文件恢复**: 自动恢复备份的自定义字体到系统字体目录
- 📊 **备份摘要显示**: 显示备份内容的详细摘要信息

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

### 备份操作

```bash
# 使用默认输出目录 (~/macbac_backups)
macbac backup

# 指定自定义输出目录
macbac backup --output /path/to/backup/directory
例如：
macbac backup --output ~/os_backups/app_fonts_backups
```

### 恢复操作 🆕

```bash
# 显示备份摘要
macbac restore summary /path/to/backup/directory

# 恢复 App Store 应用
macbac restore appstore /path/to/backup/directory

# 恢复 Homebrew 包
macbac restore homebrew /path/to/backup/directory

# 恢复自定义字体
macbac restore fonts /path/to/backup/directory
```

### 备份输出结构

备份完成后，会在指定目录下创建一个带时间戳的备份文件夹：

```
~/macbac_backups/
└── macbac_backup_20250107_103000/
    ├── fonts/
    │   ├── CustomFont.ttf
    │   └── AnotherFont.otf
    ├── manifest.json      # 机器可读的备份清单
    └── inventory.md       # 人类可读的备份报告
```

### 备份清单示例

#### manifest.json（机器可读）

```json
{
  "backup_info": {
    "date": "2025-01-07T10:30:00Z",
    "macos_version": "15.0.0",
    "macbac_version": "0.2.0"
  },
  "appstore": [
    { "id": "497799835", "name": "Xcode" },
    { "id": "1444383602", "name": "GoodNotes" }
  ],
  "homebrew": {
    "brewfile": "tap \"homebrew/bundle\"\nbrew \"git\"\ncask \"visual-studio-code\""
  },
  "fonts": ["CustomFont.ttf", "AnotherFont.otf"],
  "manual_apps": [
    { "name": "Sublime Text.app", "path": "/Applications/Sublime Text.app" }
  ],
  "dev_tools": ["git", "python", "node"]
}
```

#### inventory.md（人类可读）

````markdown
# macbac Backup Inventory

- **Backup Date:** 2025-01-07 10:30:00
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
cask "visual-studio-code"
```

## 🛠️ Development Environment & Toolchain (Installed)

- **git** - Distributed version control system (git version 2.39.0)
- **python** - Interpreted, interactive, object-oriented programming language (Python 3.13.0)
- **node** - Platform built on V8 to build network applications (v20.10.0)

## ✍️ Custom Fonts

- `CustomFont.ttf`
- `AnotherFont.otf`

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
  ```

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
pytest tests/test_restore.py

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
│   ├── restore.py          # 恢复管理器 🆕
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
│   ├── test_backup.py
│   └── test_restore.py     # 恢复功能测试 🆕
├── pyproject.toml
├── README.md
├── spec-v4.md
└── uv.lock
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 版本历史

### v0.2.0 🆕

- ✅ 实现完整的恢复功能
- ✅ 添加 `manifest.json` 机器可读格式
- ✅ 支持 App Store 应用、Homebrew 包和字体的一键恢复
- ✅ 改进开发环境检测，显示已安装工具的版本信息
- ✅ 完善的测试覆盖

### v0.1.0

- ✅ 基础备份功能
- ✅ 支持 App Store 应用、Homebrew、字体和手动应用的备份
- ✅ 生成 Markdown 格式的备份报告

## 未来计划

- 🖥️ **图形界面**: 为非技术用户提供 GUI
- ☁️ **云同步**: 支持云存储服务集成
- 📈 **增量备份**: 实现增量备份功能
- 🔧 **配置文件恢复**: 支持开发环境配置文件的备份和恢复
- 🎯 **选择性恢复**: 允许用户选择性地恢复特定类型的数据
