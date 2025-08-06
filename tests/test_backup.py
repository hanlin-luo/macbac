"""Tests for backup functionality."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from macbac.backup import BackupManager
from macbac.storage import StorageManager


class TestBackupManager:
    """Test cases for BackupManager."""

    def test_init(self) -> None:
        """Test BackupManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            manager = BackupManager(output_path)

            assert manager.output_path == output_path
            assert isinstance(manager.storage_manager, StorageManager)
            assert len(manager.scanners) == 5
            assert "appstore" in manager.scanners
            assert "homebrew" in manager.scanners
            assert "dev_env" in manager.scanners
            assert "fonts" in manager.scanners
            assert "manual_apps" in manager.scanners

    @patch("macbac.backup.console")
    def test_start_backup_creates_directory(self, mock_console: Any) -> None:
        """Test that start_backup creates a timestamped directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            manager = BackupManager(output_path)

            # Mock all scanners to return empty data
            for scanner in manager.scanners.values():
                scanner.scan = Mock(return_value={})  # type: ignore

            # Mock storage manager methods
            manager.storage_manager.store_backup_data = Mock()  # type: ignore
            manager.storage_manager.generate_inventory = Mock()  # type: ignore

            backup_dir = manager.start_backup()

            assert backup_dir.exists()
            assert backup_dir.parent == output_path
            assert backup_dir.name.startswith("macbac_backup_")

    @patch("macbac.backup.console")
    def test_start_backup_handles_scanner_errors(self, mock_console: Any) -> None:
        """Test that start_backup handles scanner errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir)
            manager = BackupManager(output_path)

            # Mock one scanner to raise an exception
            manager.scanners["appstore"].scan = Mock(  # type: ignore
                side_effect=Exception("Test error")
            )

            # Mock other scanners to return empty data
            for name, scanner in manager.scanners.items():
                if name != "appstore":
                    scanner.scan = Mock(return_value={})  # type: ignore

            # Mock storage manager methods
            manager.storage_manager.store_backup_data = Mock()  # type: ignore
            manager.storage_manager.generate_inventory = Mock()  # type: ignore

            backup_dir = manager.start_backup()

            # Should still complete successfully
            assert backup_dir.exists()

            # Storage methods should still be called
            manager.storage_manager.store_backup_data.assert_called_once()
            manager.storage_manager.generate_inventory.assert_called_once()
