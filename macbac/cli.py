"""Command-line interface for macbac."""

from pathlib import Path

import click
from rich.console import Console

from .backup import BackupManager

console = Console()


@click.group()
def cli() -> None:
    """macbac - A tool for MacOS backup and migration."""
    pass


@cli.command()
@click.option(
    "-o",
    "--output",
    default="~/macbac_backups",
    help="The directory to store the backup files.",
)
def backup(output: str) -> None:
    """Starts the backup process for applications and configurations."""
    console.print("[bold green]Starting macbac backup process...[/bold green]")

    # Expand user path
    output_path = Path(output).expanduser().resolve()

    try:
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)

        # Initialize backup manager
        backup_manager = BackupManager(output_path)

        # Start backup process
        backup_path = backup_manager.start_backup()

        console.print("[bold green]✅ Backup completed successfully![/bold green]")
        console.print(f"[cyan]Backup location: {backup_path}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]❌ Backup failed: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
