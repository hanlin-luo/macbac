"""Command-line interface for macbac."""

from pathlib import Path

import click
from rich.console import Console

from .backup import BackupManager
from .restore import RestoreManager

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


@cli.group(invoke_without_command=True)
@click.option(
    "-s",
    "--source",
    required=True,
    help="The backup directory to restore from.",
)
@click.pass_context
def restore(ctx: click.Context, source: str) -> None:
    """Restore applications and configurations from a backup."""
    # Expand user path
    source_path = Path(source).expanduser().resolve()

    if not source_path.exists():
        console.print(
            f"[bold red]❌ Backup directory not found: {source_path}[/bold red]"
        )
        raise click.ClickException(f"Backup directory not found: {source_path}")

    try:
        # Initialize restore manager
        restore_manager = RestoreManager(source_path)

        # Store restore manager in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj["restore_manager"] = restore_manager

        # If no subcommand is provided, show backup summary
        if ctx.invoked_subcommand is None:
            restore_manager.show_backup_summary()

    except Exception as e:
        console.print(f"[bold red]❌ Failed to load backup: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


@restore.command()
@click.pass_context
def appstore(ctx: click.Context) -> None:
    """Restore App Store applications."""
    restore_manager = ctx.obj["restore_manager"]
    try:
        restore_manager.restore_appstore_apps()
    except Exception as e:
        console.print(f"[bold red]❌ App Store restore failed: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


@restore.command()
@click.pass_context
def homebrew(ctx: click.Context) -> None:
    """Restore Homebrew packages and casks."""
    restore_manager = ctx.obj["restore_manager"]
    try:
        restore_manager.restore_homebrew()
    except Exception as e:
        console.print(f"[bold red]❌ Homebrew restore failed: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


@restore.command()
@click.pass_context
def fonts(ctx: click.Context) -> None:
    """Restore custom fonts."""
    restore_manager = ctx.obj["restore_manager"]
    try:
        restore_manager.restore_fonts()
    except Exception as e:
        console.print(f"[bold red]❌ Font restore failed: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


@restore.command()
@click.pass_context
def summary(ctx: click.Context) -> None:
    """Show backup summary."""
    restore_manager = ctx.obj["restore_manager"]
    try:
        restore_manager.show_backup_summary()
    except Exception as e:
        console.print(f"[bold red]❌ Failed to show backup summary: {e}[/bold red]")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
