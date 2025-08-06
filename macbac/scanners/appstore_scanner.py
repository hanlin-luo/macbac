"""Scanner for App Store applications."""

import subprocess
from typing import Any, Dict


class AppStoreScanner:
    """Scans for applications installed from the App Store."""

    def scan(self) -> Dict[str, Any]:
        """Scan for App Store applications using mas command."""
        try:
            # Check if mas is installed
            subprocess.run(["which", "mas"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Try to get apps without mas (limited functionality)
            return self._scan_without_mas()

        try:
            # Run mas list command
            result = subprocess.run(
                ["mas", "list"], capture_output=True, text=True, check=True
            )

            apps = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.split(" ", 1)
                    if len(parts) >= 2:
                        app_id = parts[0]
                        app_name = parts[1]
                        apps.append({"id": app_id, "name": app_name})

            return {"apps": apps, "total_count": len(apps)}

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run mas list: {e}") from e

    def _scan_without_mas(self) -> Dict[str, Any]:
        """Fallback method to scan App Store apps without mas."""
        # This is a limited fallback - we can't get App Store IDs without mas
        # But we can identify some App Store apps by their receipt files
        from pathlib import Path

        apps = []
        applications_dir = Path("/Applications")

        if applications_dir.exists():
            for app_path in applications_dir.glob("*.app"):
                # Check if app has App Store receipt
                receipt_path = app_path / "Contents" / "_MASReceipt" / "receipt"
                if receipt_path.exists():
                    apps.append(
                        {
                            "id": "unknown",
                            "name": app_path.stem,
                            "note": "App Store app (mas not installed - ID unavailable)",
                        }
                    )

        return {
            "apps": apps,
            "total_count": len(apps),
            "warning": "mas command not found - limited App Store app detection",
        }
