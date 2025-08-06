"""Scanner for Homebrew packages and casks."""

import subprocess
from typing import Any, Dict


class HomebrewScanner:
    """Scans for Homebrew packages and generates Brewfile content."""

    def scan(self) -> Dict[str, Any]:
        """Scan Homebrew packages and generate Brewfile content."""
        try:
            # Check if brew is installedtry:
            subprocess.run(["which", "brew"], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("Homebrew not found - brew command not available") from e

        try:
            # Generate Brewfile content
            result = subprocess.run(
                ["brew", "bundle", "dump", "--file=-"],
                capture_output=True,
                text=True,
                check=True,
            )

            brewfile_content = result.stdout.strip()

            # Parse the content to get some statistics
            lines = brewfile_content.split("\n")
            taps = [line for line in lines if line.startswith("tap ")]
            brews = [line for line in lines if line.startswith("brew ")]
            casks = [line for line in lines if line.startswith("cask ")]
            mas_apps = [line for line in lines if line.startswith("mas ")]

            return {
                "brewfile_content": brewfile_content,
                "statistics": {
                    "taps": len(taps),
                    "formulae": len(brews),
                    "casks": len(casks),
                    "mas_apps": len(mas_apps),
                    "total_lines": len([line for line in lines if line.strip()]),
                },
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to generate Brewfile: {e}") from e
