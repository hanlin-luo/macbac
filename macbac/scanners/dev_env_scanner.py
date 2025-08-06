"""Scanner for development environment configurations."""

from pathlib import Path
from typing import Any, Dict


class DevEnvScanner:
    """Scans for development environment configuration files."""

    # Common development configuration files to backup
    CONFIG_FILES = [
        {
            "name": ".gitconfig",
            "path": "~/.gitconfig",
            "description": "Git global configuration",
        },
        {
            "name": ".zshrc",
            "path": "~/.zshrc",
            "description": "Zsh shell configuration",
        },
        {
            "name": ".bashrc",
            "path": "~/.bashrc",
            "description": "Bash shell configuration",
        },
        {
            "name": ".bash_profile",
            "path": "~/.bash_profile",
            "description": "Bash profile configuration",
        },
        {
            "name": ".vimrc",
            "path": "~/.vimrc",
            "description": "Vim editor configuration",
        },
        {
            "name": ".tmux.conf",
            "path": "~/.tmux.conf",
            "description": "Tmux terminal multiplexer configuration",
        },
        {
            "name": ".ssh/config",
            "path": "~/.ssh/config",
            "description": "SSH client configuration",
        },
        {
            "name": ".aws/config",
            "path": "~/.aws/config",
            "description": "AWS CLI configuration",
        },
        {
            "name": ".aws/credentials",
            "path": "~/.aws/credentials",
            "description": "AWS CLI credentials (sensitive)",
        },
        {"name": ".npmrc", "path": "~/.npmrc", "description": "NPM configuration"},
        {"name": ".pypirc", "path": "~/.pypirc", "description": "PyPI configuration"},
        {
            "name": ".gitignore_global",
            "path": "~/.gitignore_global",
            "description": "Global Git ignore patterns",
        },
    ]

    def scan(self) -> Dict[str, Any]:
        """Scan for development environment configuration files."""
        found_configs = []
        missing_configs = []

        for config in self.CONFIG_FILES:
            config_path = Path(config["path"]).expanduser()

            if config_path.exists() and config_path.is_file():
                # Get file size
                file_size = config_path.stat().st_size

                found_configs.append(
                    {
                        "name": config["name"],
                        "path": config["path"],
                        "description": config["description"],
                        "size_bytes": file_size,
                        "exists": True,
                    }
                )
            else:
                missing_configs.append(
                    {
                        "name": config["name"],
                        "path": config["path"],
                        "description": config["description"],
                        "exists": False,
                    }
                )

        return {
            "config_files": found_configs,
            "missing_files": missing_configs,
            "found_count": len(found_configs),
            "total_checked": len(self.CONFIG_FILES),
        }
