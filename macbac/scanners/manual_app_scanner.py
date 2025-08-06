"""Scanner for manually installed applications."""

import plistlib
from pathlib import Path
from typing import Any, Dict, List, Optional


class ManualAppScanner:
    """Scans for manually installed applications (non-App Store, non-Homebrew)."""

    def scan(self) -> Dict[str, Any]:
        """Scan for manually installed applications."""
        apps = []

        # Scan system Applications directory
        system_apps_dir = Path("/Applications")
        if system_apps_dir.exists():
            apps.extend(self._scan_applications_directory(system_apps_dir))

        # Scan user Applications directory
        user_apps_dir = Path("~/Applications").expanduser()
        if user_apps_dir.exists():
            apps.extend(self._scan_applications_directory(user_apps_dir))

        # Filter out App Store apps and Homebrew casks
        manual_apps = []
        for app in apps:
            if not self._is_app_store_app(app["path"]) and not self._is_homebrew_app(
                app
            ):
                manual_apps.append(app)

        return {
            "apps": manual_apps,
            "total_count": len(manual_apps),
            "all_apps_count": len(apps),
            "scanned_directories": [
                (
                    str(system_apps_dir)
                    if system_apps_dir.exists()
                    else f"{system_apps_dir} (not found)"
                ),
                (
                    str(user_apps_dir)
                    if user_apps_dir.exists()
                    else f"{user_apps_dir} (not found)"
                ),
            ],
        }

    def _scan_applications_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Scan an Applications directory for .app bundles."""
        apps = []

        try:
            for app_path in directory.glob("*.app"):
                if app_path.is_dir():
                    app_info = self._get_app_info(app_path)
                    if app_info:
                        apps.append(app_info)
        except PermissionError:
            # Skip directories that can't be accessed
            pass

        return apps

    def _get_app_info(self, app_path: Path) -> Optional[Dict[str, Any]]:
        """Extract information from an application bundle."""
        try:
            # Read Info.plist
            info_plist_path = app_path / "Contents" / "Info.plist"
            if not info_plist_path.exists():
                return None

            with open(info_plist_path, "rb") as f:
                plist_data = plistlib.load(f)

            # Extract basic information
            bundle_name = plist_data.get("CFBundleName", app_path.stem)
            bundle_id = plist_data.get("CFBundleIdentifier", "unknown")
            version = plist_data.get("CFBundleShortVersionString", "unknown")

            return {
                "name": bundle_name,
                "path": str(app_path),
                "bundle_id": bundle_id,
                "version": version,
                "display_name": plist_data.get("CFBundleDisplayName", bundle_name),
            }

        except (OSError, plistlib.InvalidFileException, KeyError):
            # Return basic info if plist can't be read
            return {
                "name": app_path.stem,
                "path": str(app_path),
                "bundle_id": "unknown",
                "version": "unknown",
                "display_name": app_path.stem,
            }

    def _is_app_store_app(self, app_path: str) -> bool:
        """Check if an app was installed from the App Store."""
        app_path_obj = Path(app_path)

        # Check for App Store receipt
        receipt_path = app_path_obj / "Contents" / "_MASReceipt" / "receipt"
        if receipt_path.exists():
            return True

        # Check for sandboxed apps (usually from App Store)
        info_plist_path = app_path_obj / "Contents" / "Info.plist"
        if info_plist_path.exists():
            try:
                with open(info_plist_path, "rb") as f:
                    plist_data = plistlib.load(f)

                # Check for sandbox entitlements
                if plist_data.get("com.apple.security.app-sandbox"):
                    return True

            except (OSError, plistlib.InvalidFileException):
                pass

        return False

    def _is_homebrew_app(self, app_info: Dict[str, Any]) -> bool:
        """Check if an app was installed via Homebrew Cask."""
        app_path = Path(app_info["path"])

        # Check if the app is a symlink (common for Homebrew casks)
        if app_path.is_symlink():
            # Check if it points to a Homebrew location
            try:
                real_path = app_path.resolve()
                if "/opt/homebrew/" in str(real_path) or "/usr/local/" in str(
                    real_path
                ):
                    return True
            except OSError:
                pass

        # Check for common Homebrew cask bundle identifiers
        bundle_id = app_info.get("bundle_id", "")
        homebrew_indicators = ["org.homebrew.", "homebrew."]

        for indicator in homebrew_indicators:
            if indicator in bundle_id:
                return True

        return False
