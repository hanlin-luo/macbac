"""Core backup management functionality."""

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .scanners.appstore_scanner import AppStoreScanner
from .scanners.dev_env_scanner import DevEnvScanner
from .scanners.font_scanner import FontScanner
from .scanners.homebrew_scanner import HomebrewScanner
from .scanners.manual_app_scanner import ManualAppScanner
from .storage import StorageManager

console = Console()


class BackupManager:
    """Manages the backup process by coordinating scanners and storage."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.storage_manager = StorageManager()

        # Initialize scanners
        self.scanners = {
            "appstore": AppStoreScanner(),
            "homebrew": HomebrewScanner(),
            "dev_env": DevEnvScanner(),
            "fonts": FontScanner(),
            "manual_apps": ManualAppScanner(),
        }

    def start_backup(self) -> Path:
        """Start the backup process and return the backup directory path."""
        # Create timestamped backup directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.output_path / f"macbac_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize storage manager with backup directory
        self.storage_manager.set_backup_dir(backup_dir)

        # Collect all backup data
        backup_data = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for scanner_name, scanner in self.scanners.items():
                task = progress.add_task(
                    f"Scanning {scanner_name.replace('_', ' ')}...", total=None
                )

                try:
                    data = scanner.scan()  # type: ignore
                    backup_data[scanner_name] = data
                    scanner_display = scanner_name.replace("_", " ")
                    progress.update(task, description=f"✅ {scanner_display} completed")
                except Exception as e:
                    console.print(
                        f"[yellow]⚠️  Warning: {scanner_name} scan failed: {e}[/yellow]"
                    )
                    backup_data[scanner_name] = {"error": str(e)}
                    scanner_display = scanner_name.replace("_", " ")
                    progress.update(task, description=f"⚠️  {scanner_display} failed")

            # Store backup data
            storage_task = progress.add_task("Storing backup data...", total=None)
            self.storage_manager.store_backup_data(backup_data)
            progress.update(storage_task, description="✅ Backup data stored")

            # Generate inventory
            inventory_task = progress.add_task("Generating inventory...", total=None)
            self.storage_manager.generate_inventory(backup_data)
            progress.update(inventory_task, description="✅ Inventory generated")

        return backup_dir
