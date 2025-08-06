"""Storage management for backup data."""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class StorageManager:
    """Manages storage of backup data and generation of inventory files."""

    def __init__(self) -> None:
        self.backup_dir: Path | None = None

    def set_backup_dir(self, backup_dir: Path) -> None:
        """Set the backup directory."""
        self.backup_dir = backup_dir

    def store_backup_data(self, backup_data: Dict[str, Any]) -> None:
        """Store backup data to appropriate directories."""
        if not self.backup_dir:
            raise ValueError("Backup directory not set")

        # Create subdirectories
        configs_dir = self.backup_dir / "configs"
        fonts_dir = self.backup_dir / "fonts"

        configs_dir.mkdir(exist_ok=True)
        fonts_dir.mkdir(exist_ok=True)

        # Store configuration files
        if "dev_env" in backup_data and "config_files" in backup_data["dev_env"]:
            for config_file in backup_data["dev_env"]["config_files"]:
                src_path = Path(config_file["path"]).expanduser()
                if src_path.exists():
                    dst_path = configs_dir / src_path.name
                    shutil.copy2(src_path, dst_path)

        # Store font files
        if "fonts" in backup_data and "font_files" in backup_data["fonts"]:
            for font_file in backup_data["fonts"]["font_files"]:
                src_path = Path(font_file["path"])
                if src_path.exists():
                    dst_path = fonts_dir / src_path.name
                    shutil.copy2(src_path, dst_path)

    def generate_inventory(self, backup_data: Dict[str, Any]) -> None:
        """Generate inventory.md file with backup summary."""
        if not self.backup_dir:
            raise ValueError("Backup directory not set")

        inventory_path = self.backup_dir / "inventory.md"

        # Get macOS version
        try:
            macos_version = subprocess.run(
                ["sw_vers", "-productVersion"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            macos_version = "Unknown"

        with open(inventory_path, "w", encoding="utf-8") as f:
            f.write("# macbac Backup Inventory\n\n")
            backup_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"- **Backup Date:** {backup_date}\n")
            f.write(f"- **macOS Version:** {macos_version}\n\n")
            f.write("---\n\n")

            # App Store applications
            self._write_appstore_section(f, backup_data.get("appstore", {}))

            # Homebrew section
            self._write_homebrew_section(f, backup_data.get("homebrew", {}))

            # Development environment
            self._write_dev_env_section(f, backup_data.get("dev_env", {}))

            # Custom fonts
            self._write_fonts_section(f, backup_data.get("fonts", {}))

            # Manual applications
            self._write_manual_apps_section(f, backup_data.get("manual_apps", {}))

    def _write_appstore_section(self, f: Any, appstore_data: Dict[str, Any]) -> None:
        """Write App Store applications section."""
        f.write("## 🍎 App Store & Sandboxed Applications\n\n")

        if "error" in appstore_data:
            f.write(f"❌ Error: {appstore_data['error']}\n\n")
            return

        apps = appstore_data.get("apps", [])
        if apps:
            f.write("| ID | Name |\n")
            f.write("|----|------|\n")
            for app in apps:
                f.write(f"| {app['id']} | {app['name']} |\n")
        else:
            f.write("No App Store applications found.\n")

        f.write("\n---\n\n")

    def _write_homebrew_section(self, f: Any, homebrew_data: Dict[str, Any]) -> None:
        """Write Homebrew section."""
        f.write("## 🍺 Homebrew Ecosystem (Brewfile)\n\n")

        if "error" in homebrew_data:
            f.write(f"❌ Error: {homebrew_data['error']}\n\n")
            return

        brewfile_content = homebrew_data.get("brewfile_content", "")
        if brewfile_content:
            f.write("```brewfile\n")
            f.write(brewfile_content)
            f.write("\n```\n")
        else:
            f.write("No Homebrew packages found.\n")

        f.write("\n---\n\n")

    def _write_dev_env_section(self, f: Any, dev_env_data: Dict[str, Any]) -> None:
        """Write development environment section."""
        f.write("## 🛠️ Development Environment & Toolchain\n\n")

        if "error" in dev_env_data:
            f.write(f"❌ Error: {dev_env_data['error']}\n\n")
            return

        config_files = dev_env_data.get("config_files", [])
        if config_files:
            for config in config_files:
                f.write(f"- `{config['name']}`\n")
        else:
            f.write("No development configuration files found.\n")

        f.write("\n---\n\n")

    def _write_fonts_section(self, f: Any, fonts_data: Dict[str, Any]) -> None:
        """Write custom fonts section."""
        f.write("## ✍️ Custom Fonts\n\n")

        if "error" in fonts_data:
            f.write(f"❌ Error: {fonts_data['error']}\n\n")
            return

        font_files = fonts_data.get("font_files", [])
        if font_files:
            for font in font_files:
                f.write(f"- `{font['name']}`\n")
        else:
            f.write("No custom fonts found.\n")

        f.write("\n---\n\n")

    def _write_manual_apps_section(
        self, f: Any, manual_apps_data: Dict[str, Any]
    ) -> None:
        """Write manually installed applications section."""
        f.write("## 📦 Manually Installed Applications\n\n")

        if "error" in manual_apps_data:
            f.write(f"❌ Error: {manual_apps_data['error']}\n\n")
            return

        apps = manual_apps_data.get("apps", [])
        if apps:
            f.write("| Application Name | Path |\n")
            f.write("|------------------|------|\n")
            for app in apps:
                f.write(f"| {app['name']} | {app['path']} |\n")
        else:
            f.write("No manually installed applications found.\n")

        f.write("\n")
