## macbac (MacOS Backup and Migration) 软件设计文档 - v4

### 1. 概述

**1.1 项目简介**

`macbac` 是一款旨在简化 macOS 用户备份及恢复工作环境的命令行工具。通过备份旧 Mac 上的应用程序列表、字体和关键数据，`macbac` 能够帮助用户快速、高效地在新 Mac 上通过自动化命令恢复环境，从而最大限度地减少迁移所需的时间和精力。

**1.2 目标**

- **高效备份:** 提供单一命令，快速启动对整个系统应用程序和配置的扫描与备份。
- **可靠恢复:** 提供按类别划分的恢复命令，引导用户在新设备上可靠地恢复其环境。
- **智能分类:** 能够识别不同来源的应用程序（App Store、Homebrew、手动安装等）并采用最优策略进行备份与恢复。
- **用户友好:** 提供清晰、美观的命令行界面和易于阅读的备份报告。
- **结构清晰:** 生成结构化、带时间戳的备份数据，方便用户管理、查阅和程序化恢复。

### 2. 系统架构与设计

**2.1 总体架构**

`macbac` 将采用模块化的架构，将核心逻辑划分为多个独立的模块。

核心模块包括：

- **CLI (Command-Line Interface) 模块:** 负责处理用户输入、解析命令和参数，并调用核心的备份或恢复逻辑。
- **Backup (备份核心) 模块:** 作为备份操作的总控制器，协调各个扫描器模块的工作。
- **Restore (恢复核心) 模块:** 作为恢复操作的总控制器，读取备份数据并执行恢复流程。
- **Scanner (扫描器) 模块:** 包含一系列子模块，每个子模块负责扫描特定类型的应用程序或数据。
- **Storage (存储) 模块:** 负责处理备份数据的组织、写入、清单文件的生成以及在恢复时读取数据。
- **Logger (日志) 模块:** 使用 `rich` 库提供格式化的终端输出。

**2.2 模块详细设计**

- **CLI 模块 (`cli.py`)**

  - 使用 `click` 库创建命令行接口。
  - 定义主命令 `macbac` 及其子命令 `backup` 和 `restore`。
  - `backup` 命令提供 `--output` 选项。
  - `restore` 命令提供 `--source` 选项指定备份目录，并包含 `appstore`、`homebrew`、`fonts` 等子命令。

- **Backup 模块 (`backup.py`)**

  - `BackupManager` 类作为核心，接收来自 CLI 的 `backup` 指令。
  - 按顺序调用各个 `Scanner` 模块，收集备份数据。
  - 将收集到的数据传递给 `Storage` 模块进行处理。

- **Restore 模块 (`restore.py`)**

  - `RestoreManager` 类作为核心，接收来自 CLI 的 `restore` 指令。
  - 从 `Storage` 模块读取结构化的备份数据（`manifest.json`）。
  - 根据不同的恢复子命令（如 `appstore`），执行相应的恢复操作（如调用 `mas-cli`）。

- **Scanner 模块 (位于 `scanners/` 目录)**

  - **`appstore_scanner.py`:** 通过执行 `mas list` 获取 App Store 应用列表。
  - **`homebrew_scanner.py`:** 通过执行 `brew bundle dump --file=-` 生成 `Brewfile` 内容。
  - **`dev_env_scanner.py`:**
    - **(已变更)** 仅识别常见的开发工具链（如 `git`, `node`, `python` 等）的安装情况。
    - 不再备份具体的配置文件（如 `~/.gitconfig`）。此变更简化了备份范围，避免了复杂且个性化极强的配置迁移问题。
  - **`font_scanner.py`:** 扫描并备份 `~/Library/Fonts` 目录下的用户字体文件。
  - **`manual_app_scanner.py`:** 扫描 `/Applications` 和 `~/Applications` 目录，识别非 App Store 和非 Homebrew Cask 安装的应用，仅记录列表。

- **Storage 模块 (`storage.py`)**
  - `StorageManager` 类负责所有文件系统操作。
  - **(已改进)** 在创建带时间戳的备份目录后，将采用两种格式存储数据：
    1.  **`manifest.json`:** 一个机器可读的 JSON 文件，结构化地存储所有备份信息（如应用 ID、Brewfile 内容、字体文件列表等）。这将是 `restore` 功能的主要数据源。
    2.  **`inventory.md`:** 一个人类可读的 Markdown 文件，作为备份报告，清晰地列出所有备份项。

### 3. 功能实现细节

**3.1 命令行接口 (CLI)**

**备份命令:**

```bash
macbac backup [--output /path/to/your/dir]
```

**恢复命令:**

```bash
# 主恢复命令，用于引导用户
macbac restore --source /path/to/backup/dir

# 分类恢复命令
macbac restore --source /path/to/backup/dir appstore
macbac restore --source /path/to/backup/dir homebrew
macbac restore --source /path/to/backup/dir fonts
```

- `--source, -s`: **(新增)** `restore` 命令的必需参数，用于指定要从中恢复的备份目录（例如 `~/macbac_backups/macbac_backup_20250807_103000`）。

**3.2 备份数据存储结构 (已改进)**

为了更好地支持恢复功能，备份数据的存储结构经过优化，引入了机器可读的 `manifest.json`。

```
~/macbac_backups/
└── macbac_backup_20250807_103000/
    ├── fonts/
    │   ├── MyCustomFont.ttf
    │   └── AnotherFont.otf
    ├── manifest.json         # (新增) 机器可读的备份清单，用于恢复
    └── inventory.md          # 人类可读的备份报告
```

**`manifest.json` 文件格式示例:**

```json
{
  "backup_info": {
    "date": "2025-08-07T10:30:00Z",
    "macos_version": "15.0.0",
    "macbac_version": "0.2.0"
  },
  "appstore": [
    { "id": "497799835", "name": "Xcode" },
    { "id": "1444383602", "name": "GoodNotes" }
  ],
  "homebrew": {
    "brewfile": "tap \"homebrew/bundle\"\ntap \"homebrew/cask\"\nbrew \"git\"\nbrew \"python@3.13\"\ncask \"visual-studio-code\""
  },
  "fonts": ["MyCustomFont.ttf", "AnotherFont.otf"],
  "manual_apps": [
    { "name": "Sublime Text.app", "path": "/Applications/Sublime Text.app" }
  ],
  "dev_tools": ["git", "python", "node"]
}
```

**`inventory.md` 文件格式示例 (已更新):**

````markdown
# macbac Backup Inventory

- **Backup Date:** 2025-08-07 10:30:00
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
cask "visual-studio-code"
```

---

## ✍️ Custom Fonts

- `MyCustomFont.ttf`
- `AnotherFont.otf`

---

## 🛠️ Development Environment & Toolchain (Installed)

- git
- python
- node

---

## 📦 Manually Installed Applications

| Application Name | Path                           |
| ---------------- | ------------------------------ |
| Sublime Text.app | /Applications/Sublime Text.app |
````

**3.3 恢复流程 (新增)**

1.  **启动恢复:** 用户执行 `macbac restore -s <backup_dir>`。

    - 程序读取 `manifest.json` 文件。
    - 在终端显示一个备份摘要，并提示用户可以运行哪些恢复子命令（`appstore`, `homebrew`, `fonts`）。

2.  **App Store 应用恢复:**

    - 用户执行 `macbac restore -s <backup_dir> appstore`。
    - `RestoreManager` 解析 `manifest.json` 中的 `appstore` 列表。
    - 使用 `rich.progress` 显示进度条，并依次执行 `mas install <id>` 命令来安装每一个应用。

3.  **Homebrew 生态恢复:**

    - 用户执行 `macbac restore -s <backup_dir> homebrew`。
    - `RestoreManager` 从 `manifest.json` 中提取 `brewfile` 的内容，并将其写入一个临时的 `Brewfile`。
    - 执行 `brew bundle --file=<path_to_temp_brewfile>` 命令。`brew bundle` 会自动处理 taps、formulae 和 casks 的安装。

4.  **字体恢复:**
    - 用户执行 `macbac restore -s <backup_dir> fonts`。
    - `RestoreManager` 获取备份目录中 `fonts/` 子目录下的所有字体文件。
    - 将这些字体文件复制到新系统的 `~/Library/Fonts` 目录下。
    - 在复制前会检查目标文件是否存在，避免覆盖，并向用户报告跳过的文件。

### 4. 技术栈与项目配置

技术栈保持不变，但 `pyproject.toml` 中的依赖可能需要根据恢复功能所需的库（如 `mas-cli` 的 Python 包装器，如果使用的话）进行更新。

- **编程语言:** Python 3.13
- **CLI 框架:** `click`
- **终端输出:** `rich`
- **包与环境管理:** `uv`
- **项目依赖管理:** `pyproject.toml`
- **代码风格检查:** `ruff`
- **类型检查:** `mypy`
- **单元测试:** `pytest`

### 5. 测试策略

- **单元测试 (`pytest`):**
  - **(扩展)** 为 `RestoreManager` 编写单元测试。
  - 使用 `pytest` 的 `monkeypatch` 来模拟对 `subprocess.run` 的调用，以验证是否使用正确的参数调用了 `mas` 和 `brew` 命令，而无需实际安装任何东西。
  - 测试字体恢复逻辑，包括文件已存在时的跳过行为。
- **集成测试:**
  - **(扩展)** 编写端到端的测试脚本：
    1.  在一个受控环境中运行 `macbac backup`。
    2.  验证生成的 `manifest.json` 和 `inventory.md` 文件内容符合预期。
    3.  运行 `macbac restore` 的各个子命令。
    4.  验证恢复命令的执行流程和日志输出是否正确。
- **代码质量:** 保持 CI/CD 流程中集成的 `ruff` 和 `mypy` 检查。

### 6. 未来展望（超出当前范围）

- **图形用户界面 (GUI):** 为非技术用户提供一个简单的图形界面，用于执行备份和恢复。
- **云同步:** 支持将备份数据（`manifest.json` 和 `fonts` 目录）直接上传到 iCloud Drive, Google Drive 或 Dropbox 等云存储服务，并在恢复时从云端拉取。
- **增量备份:** 实现增量备份功能，仅备份自上次备份以来发生变化的文件和配置。
- **配置恢复:** 重新审视并提供一个可选的、基于白名单的配置文件恢复功能，允许用户选择性地恢复他们信任的配置文件。
