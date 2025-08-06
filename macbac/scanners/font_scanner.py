"""Scanner for custom fonts."""

from pathlib import Path
from typing import Any, Dict, List


class FontScanner:
    """Scans for custom fonts installed by the user."""

    # Font file extensions to look for
    FONT_EXTENSIONS = {
        ".ttf": "TrueType Font",
        ".otf": "OpenType Font",
        ".ttc": "TrueType Collection",
        ".otc": "OpenType Collection",
        ".woff": "Web Open Font Format",
        ".woff2": "Web Open Font Format 2",
        ".eot": "Embedded OpenType",
        ".pfb": "PostScript Type 1",
        ".pfm": "PostScript Type 1 Metrics",
        ".afm": "Adobe Font Metrics",
        ".bdf": "Bitmap Distribution Format",
        ".pcf": "Portable Compiled Format",
        ".snf": "Server Normal Format",
    }

    def scan(self) -> Dict[str, Any]:
        """Scan for custom fonts in user font directories."""
        font_files = []
        total_size = 0

        # Scan user fonts directory
        user_fonts_dir = Path("~/Library/Fonts").expanduser()
        if user_fonts_dir.exists():
            font_files.extend(self._scan_directory(user_fonts_dir))

        # Calculate total size
        for font in font_files:
            total_size += font["size_bytes"]

        # Group fonts by type
        fonts_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for font in font_files:
            font_type = font["type"]
            if font_type not in fonts_by_type:
                fonts_by_type[font_type] = []
            fonts_by_type[font_type].append(font)

        return {
            "font_files": font_files,
            "total_count": len(font_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "fonts_by_type": fonts_by_type,
            "scanned_directories": [
                str(user_fonts_dir)
                if user_fonts_dir.exists()
                else f"{user_fonts_dir} (not found)"
            ],
        }

    def _scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Scan a directory for font files."""
        fonts = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    extension = file_path.suffix.lower()
                    if extension in self.FONT_EXTENSIONS:
                        try:
                            file_size = file_path.stat().st_size
                            fonts.append(
                                {
                                    "name": file_path.name,
                                    "path": str(file_path),
                                    "extension": extension,
                                    "type": self.FONT_EXTENSIONS[extension],
                                    "size_bytes": file_size,
                                    "size_kb": round(file_size / 1024, 2),
                                }
                            )
                        except OSError:
                            # Skip files that can't be accessed
                            continue
        except PermissionError:
            # Skip directories that can't be accessed
            pass

        return fonts
