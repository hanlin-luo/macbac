"""Core restore management functionality."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


class RestoreManager:
    """Manages the restore process by reading backup data and executing restore operations."""

    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.manifest_path = backup_dir / "manifest.json"
        self.manifest_data: Dict[str, Any] = {}
        
        # Load manifest data
        self._load_manifest()

    def _load_manifest(self) -> None:
        """Load the manifest.json file."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")
        
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                self.manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid manifest file: {e}") from e

    def show_backup_summary(self) -> None:
        """Display a summary of the backup contents."""
        console.print("[bold blue]📦 Backup Summary[/bold blue]")
        console.print()
        
        backup_info = self.manifest_data.get("backup_info", {})
        console.print(f"[cyan]Backup Date:[/cyan] {backup_info.get('date', 'Unknown')}")
        console.print(f"[cyan]macOS Version:[/cyan] {backup_info.get('macos_version', 'Unknown')}")
        console.print(f"[cyan]macbac Version:[/cyan] {backup_info.get('macbac_version', 'Unknown')}")
        console.print()
        
        # Show available restore categories
        console.print("[bold green]Available restore categories:[/bold green]")
        
        if self.manifest_data.get("appstore"):
            app_count = len(self.manifest_data["appstore"])
            console.print(f"  🍎 [cyan]appstore[/cyan] - {app_count} App Store applications")
        
        if self.manifest_data.get("homebrew", {}).get("brewfile"):
            console.print(f"  🍺 [cyan]homebrew[/cyan] - Homebrew packages and casks")
        
        if self.manifest_data.get("fonts"):
            font_count = len(self.manifest_data["fonts"])
            console.print(f"  ✍️  [cyan]fonts[/cyan] - {font_count} custom fonts")
        
        console.print()
        console.print("[yellow]Use 'macbac restore --source <backup_dir> <category>' to restore specific categories.[/yellow]")

    def restore_appstore_apps(self) -> None:
        """Restore App Store applications using mas-cli."""
        apps = self.manifest_data.get("appstore", [])
        
        if not apps:
            console.print("[yellow]No App Store applications found in backup.[/yellow]")
            return
        
        # Check if mas is installed
        try:
            subprocess.run(["which", "mas"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[red]❌ mas-cli is not installed. Please install it first:[/red]")
            console.print("[cyan]brew install mas[/cyan]")
            return
        
        console.print(f"[bold green]🍎 Restoring {len(apps)} App Store applications...[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Installing apps...", total=len(apps))
            
            for app in apps:
                app_id = app.get("id")
                app_name = app.get("name", "Unknown")
                
                progress.update(task, description=f"Installing {app_name}...")
                
                try:
                    subprocess.run(
                        ["mas", "install", app_id],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    console.print(f"[green]✅ Installed: {app_name}[/green]")
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]❌ Failed to install {app_name}: {e}[/red]")
                
                progress.advance(task)
        
        console.print("[bold green]🍎 App Store restoration completed![/bold green]")

    def restore_homebrew(self) -> None:
        """Restore Homebrew packages using brew bundle."""
        homebrew_data = self.manifest_data.get("homebrew", {})
        brewfile_content = homebrew_data.get("brewfile")
        
        if not brewfile_content:
            console.print("[yellow]No Homebrew data found in backup.[/yellow]")
            return
        
        # Check if brew is installed
        try:
            subprocess.run(["which", "brew"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            console.print("[red]❌ Homebrew is not installed. Please install it first:[/red]")
            console.print("[cyan]/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"[/cyan]")
            return
        
        console.print("[bold green]🍺 Restoring Homebrew packages...[/bold green]")
        
        # Create temporary Brewfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.Brewfile', delete=False) as f:
            f.write(brewfile_content)
            temp_brewfile = f.name
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running brew bundle...", total=None)
                
                result = subprocess.run(
                    ["brew", "bundle", "--file", temp_brewfile],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    console.print("[green]✅ Homebrew restoration completed successfully![/green]")
                else:
                    console.print(f"[red]❌ Homebrew restoration failed:[/red]")
                    console.print(result.stderr)
                
                progress.update(task, description="✅ Homebrew restoration completed")
        
        finally:
            # Clean up temporary file
            Path(temp_brewfile).unlink(missing_ok=True)

    def restore_fonts(self) -> None:
        """Restore custom fonts to ~/Library/Fonts."""
        fonts = self.manifest_data.get("fonts", [])
        
        if not fonts:
            console.print("[yellow]No custom fonts found in backup.[/yellow]")
            return
        
        fonts_backup_dir = self.backup_dir / "fonts"
        if not fonts_backup_dir.exists():
            console.print("[red]❌ Fonts backup directory not found.[/red]")
            return
        
        # Ensure target directory exists
        target_dir = Path("~/Library/Fonts").expanduser()
        target_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"[bold green]✍️ Restoring {len(fonts)} custom fonts...[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Copying fonts...", total=len(fonts))
            
            copied_count = 0
            skipped_count = 0
            
            for font_name in fonts:
                progress.update(task, description=f"Copying {font_name}...")
                
                source_path = fonts_backup_dir / font_name
                target_path = target_dir / font_name
                
                if not source_path.exists():
                    console.print(f"[red]❌ Font file not found: {font_name}[/red]")
                    continue
                
                if target_path.exists():
                    console.print(f"[yellow]⚠️  Skipped (already exists): {font_name}[/yellow]")
                    skipped_count += 1
                else:
                    try:
                        shutil.copy2(source_path, target_path)
                        console.print(f"[green]✅ Copied: {font_name}[/green]")
                        copied_count += 1
                    except Exception as e:
                        console.print(f"[red]❌ Failed to copy {font_name}: {e}[/red]")
                
                progress.advance(task)
        
        console.print(f"[bold green]✍️ Font restoration completed! Copied: {copied_count}, Skipped: {skipped_count}[/bold green]")