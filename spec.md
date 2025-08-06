好的，这是一个根据您的需求编写的更为详细的 `macbac` (MacOS Backup and Migration) 软件设计文档。

---

## macbac (MacOS Backup and Migration) 软件设计文档

### 1. 概述

**1.1 项目简介**

`macbac` 是一款旨在简化 macOS 用户在新设备上恢复其工作环境的命令行工具。通过备份旧 Mac 上的应用程序列表、配置和关键数据，`macbac` 能够帮助用户快速、高效地在新 Mac 上完成环境设置，从而最大限度地减少迁移所需的时间和精力。本阶段的重点是实现一个强大的备份功能。

**1.2 目标**

- **高效备份:** 提供一个单一命令，能够快速启动对整个系统应用程序和配置的扫描与备份。
- **智能分类:** 能够识别不同来源的应用程序（App Store、Homebrew、手动安装等）并采用最优策略进行备份。
- **用户友好:** 提供清晰、美观的命令行界面和易于阅读的备份报告。
- **结构清晰:** 生成结构化、带时间戳的备份数据，方便用户管理和查阅。

### 2. 系统架构与设计

**2.1 总体架构**

`macbac` 将采用模块化的架构，将核心逻辑划分为多个独立的模块，每个模块负责一项具体的功能。这种设计有助于提高代码的可维护性、可测试性和可扩展性。

核心模块包括：

- **CLI (Command-Line Interface) 模块:** 负责处理用户输入、解析命令和参数，并调用核心备份逻辑。
- **Backup (备份核心) 模块:** 作为总控制器，协调各个扫描器模块的工作。
- **Scanner (扫描器) 模块:** 包含一系列子模块，每个子模块负责扫描特定类型的应用程序或配置。
- **Storage (存储) 模块:** 负责处理备份数据的组织、写入和清单文件的生成。
- **Logger (日志) 模块:** 使用 `rich` 库提供格式化的终端输出。

**2.2 模块详细设计**

- **CLI 模块 (`cli.py`)**

  - 使用 `click` 库创建命令行接口。
  - 定义主命令 `macbac backup`。
  - 提供 `--output` 选项，允许用户指定备份输出目录。

- **Backup 模块 (`backup.py`)**

  - `BackupManager` 类作为核心，接收来自 CLI 的指令。
  - 按顺序调用各个 `Scanner` 模块，收集备份数据。
  - 将收集到的数据传递给 `Storage` 模块进行处理。

- **Scanner 模块 (位于 `scanners/` 目录)**

  - **`appstore_scanner.py`:**
    - 通过执行 `mas list` 命令来获取所有从 App Store 安装的应用程序列表。
    - 提取应用名称和 ID，作为恢复时需要的信息。
  - **`homebrew_scanner.py`:**
    - 通过执行 `brew bundle dump --file=-` 命令生成 `Brewfile` 的内容。
    - 此方法无需手动创建临时文件，可以直接捕获输出，内容包括 Taps、Formulae 和 Casks。
  - **`dev_env_scanner.py`:**
    - 识别常见的开发工具链（如 Git, zsh, etc.）。
    - 备份相关的配置文件，例如 `~/.gitconfig`, `~/.zshrc` 等。
    - 允许未来通过配置文件扩展支持更多工具。
  - **`font_scanner.py`:**
    - 扫描 `~/Library/Fonts` 目录。
    - 备份所有用户安装的自定义字体文件。
  - **`manual_app_scanner.py`:**
    - 扫描 `/Applications` 和 `~/Applications` 目录。
    - 通过应用的 `Info.plist` 文件识别非 App Store 和非 Homebrew Cask 安装的应用。
    - 仅备份应用程序的名称和路径列表。

- **Storage 模块 (`storage.py`)**
  - `StorageManager` 类负责所有文件系统操作。
  - 创建一个以时间戳命名的备份根目录，格式为 `macbac_backup_YYYYMMDD_HHMMSS`。
  - 在根目录下，根据备份类别创建子目录（如 `fonts`, `configs`）。
  - 将备份文件写入相应的子目录。
  - 生成一个易于阅读的 `inventory.md` 清单文件。

### 3. 功能实现细节

**3.1 命令行接口 (CLI)**

将使用 `click` 库实现如下命令：

```bash
macbac backup [--output /path/to/your/dir]
```

- `backup`: 主命令，用于启动备份流程。
- `--output, -o`: 可选参数，用于指定备份文件的存储位置。如果未提供，则默认为 `~/macbac_backups`。

**示例代码 (`cli.py`):**

```python
import click
from rich.console import Console

@click.group()
def cli():
    """macbac - A tool for MacOS backup and migration."""
    pass

@cli.command()
@click.option('-o', '--output', default='~/macbac_backups', help='The directory to store the backup files.')
def backup(output):
    """Starts the backup process for applications and configurations."""
    console = Console()
    console.print("[bold green]Starting macbac backup process...[/bold green]")
    # 在此调用 BackupManager
```

**3.2 备份流程**

1.  **初始化:** CLI 接收到 `backup` 命令，实例化 `BackupManager`。
2.  **创建备份目录:** `StorageManager` 根据当前时间戳在指定路径（或默认路径）下创建主备份目录。
3.  **执行扫描:** `BackupManager` 依次调用各个 `Scanner`。
    - 每个 `Scanner` 开始工作时，使用 `rich` 的 `status` 或 `progress` 在终端显示当前正在进行的操作。
    - 例如: `[bold cyan]Scanning App Store applications...[/bold cyan]`
4.  **数据收集:** 每个 `Scanner` 将其扫描结果（如文件列表、配置内容等）返回给 `BackupManager`。
5.  **数据存储:** `BackupManager` 将收集到的数据传递给 `StorageManager`。
    - `StorageManager` 将字体文件、配置文件等物理文件复制到对应的备份子目录中。
    - 对于 App Store 列表和 Homebrew `Brewfile` 内容，直接写入 `inventory.md`。
6.  **生成清单文件:** 所有扫描和文件复制完成后，`StorageManager` 开始生成 `inventory.md` 文件。该文件将使用 Markdown 表格清晰地列出所有备份项。

**3.3 备份数据存储结构**

备份将存储在用户指定的目录中，结构如下：

```
~/macbac_backups/
└── macbac_backup_20250806_221500/
    ├── configs/
    │   ├── .gitconfig
    │   └── .zshrc
    ├── fonts/
    │   ├── MyCustomFont.ttf
    │   └── AnotherFont.otf
    └── inventory.md
```

**`inventory.md` 文件格式示例:**

````markdown
# macbac Backup Inventory

- **Backup Date:** 2025-08-06 22:15:00
- **macOS Version:** 15.0.0

---

##  App Store & Sandboxed Applications

| ID         | Name      |
| ---------- | --------- |
| 497799835  | Xcode     |
| 1444383602 | GoodNotes |

---

## 🍺 Homebrew Ecosystem (Brewfile)

```brewfile
tap "homebrew/bundle"
tap "homebrew/cask"
brew "git"
brew "python@3.13"
brew "uv"
cask "visual-studio-code"
cask "iterm2"
```
````

---

## 🛠️ Development Environment & Toolchain

- `~/.gitconfig`
- `~/.zshrc`

---

## ✍️ Custom Fonts

- `MyCustomFont.ttf`
- `AnotherFont.otf`

---

## 📦 Manually Installed Applications

| Application Name | Path                           |
| ---------------- | ------------------------------ |
| Sublime Text.app | /Applications/Sublime Text.app |

````

### 4. 技术栈与项目配置

*   **编程语言:** Python 3.13
*   **CLI 框架:** `click`
*   **终端输出:** `rich`
*   **包与环境管理:** `uv`
*   **项目依赖管理:** `pyproject.toml`
*   **代码风格检查:** `ruff`
*   **类型检查:** `mypy`
*   **单元测试:** `pytest`

**`pyproject.toml` 配置示例:**

```toml
[project]
name = "macbac"
version = "0.1.0"
description = "MacOS Backup and Migration tool."
authors = [{ name = "Your Name", email = "your.email@example.com" }]
requires-python = ">=3.13"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.scripts]
macbac = "macbac.cli:cli"

[tool.uv]
# uv 配置

[tool.ruff]
# ruff 配置规则
line-length = 88
select = ["E", "F", "I", "W", "C4", "B"]

[tool.mypy]
# mypy 配置
strict = true

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = [
    "tests",
]
````

### 5. 测试策略

- **单元测试 (`pytest`):**
  - 针对每个 `Scanner` 模块编写测试，模拟系统环境（例如，使用假的 `plist` 文件，模拟的命令行输出来源）来验证其是否能正确提取信息。
  - 测试 `StorageManager` 是否能正确创建目录结构和生成清单文件。
  - 使用 `pytest` 的 `monkeypatch` 来模拟文件系统操作和子进程调用。
- **集成测试:**
  - 编写测试脚本，完整地运行 `macbac backup` 命令。
  - 验证备份目录是否成功创建，以及 `inventory.md` 的内容是否符合预期。
- **代码质量:**
  - 在 CI/CD 流程中集成 `ruff` 和 `mypy`，确保每次提交都符合代码风格和类型安全标准。

### 6. 未来展望（超出当前范围）

- **恢复功能:** 开发 `macbac restore` 命令，读取 `inventory.md` 文件并自动在新系统上执行安装和配置恢复操作。
- **图形用户界面 (GUI):** 为非技术用户提供一个简单的图形界面。
- **云同步:** 支持将备份数据直接上传到 iCloud Drive, Google Drive 或 Dropbox 等云存储服务。
- **增量备份:** 实现增量备份功能，仅备份自上次备份以来发生变化的文件和配置，以节省时间和存储空间。
