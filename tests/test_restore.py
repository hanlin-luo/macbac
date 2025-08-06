"""Tests for the restore module."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from macbac.restore import RestoreManager


class TestRestoreManager:
    """Test cases for RestoreManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create a sample manifest.json
        self.manifest_data = {
            "backup_info": {
                "date": "2025-01-07T10:30:00Z",
                "macos_version": "15.0.0",
                "macbac_version": "0.2.0"
            },
            "appstore": [
                {"id": "497799835", "name": "Xcode"},
                {"id": "1444383602", "name": "GoodNotes"}
            ],
            "homebrew": {
                "brewfile": "tap \"homebrew/bundle\"\nbrew \"git\"\ncask \"visual-studio-code\""
            },
            "fonts": ["MyCustomFont.ttf", "AnotherFont.otf"],
            "manual_apps": [
                {"name": "Sublime Text.app", "path": "/Applications/Sublime Text.app"}
            ],
            "dev_tools": ["git", "python", "node"]
        }
        
        # Write manifest.json to temp directory
        manifest_path = self.temp_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest_data, f)
        
        # Create fonts directory with sample fonts
        fonts_dir = self.temp_dir / "fonts"
        fonts_dir.mkdir()
        (fonts_dir / "MyCustomFont.ttf").write_text("fake font data")
        (fonts_dir / "AnotherFont.otf").write_text("fake font data")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_manifest_success(self):
        """Test successful manifest loading."""
        restore_manager = RestoreManager(self.temp_dir)
        
        assert restore_manager.manifest_data == self.manifest_data
        assert restore_manager.backup_dir == self.temp_dir
        assert restore_manager.manifest_path == self.temp_dir / "manifest.json"

    def test_load_manifest_file_not_found(self):
        """Test manifest loading when file doesn't exist."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(FileNotFoundError, match="Manifest file not found"):
            RestoreManager(empty_dir)

    def test_load_manifest_invalid_json(self):
        """Test manifest loading with invalid JSON."""
        invalid_dir = self.temp_dir / "invalid"
        invalid_dir.mkdir()
        
        # Write invalid JSON
        manifest_path = invalid_dir / "manifest.json"
        manifest_path.write_text("invalid json content")
        
        with pytest.raises(ValueError, match="Invalid manifest file"):
            RestoreManager(invalid_dir)

    @patch('subprocess.run')
    def test_restore_appstore_apps_success(self, mock_run):
        """Test successful App Store apps restoration."""
        # Mock mas command availability and installation
        mock_run.side_effect = [
            Mock(returncode=0),  # which mas
            Mock(returncode=0),  # mas install Xcode
            Mock(returncode=0),  # mas install GoodNotes
        ]
        
        restore_manager = RestoreManager(self.temp_dir)
        
        # This should not raise an exception
        restore_manager.restore_appstore_apps()
        
        # Verify mas commands were called
        assert mock_run.call_count == 3
        mock_run.assert_any_call(["which", "mas"], check=True, capture_output=True)
        mock_run.assert_any_call(["mas", "install", "497799835"], check=True, capture_output=True, text=True)
        mock_run.assert_any_call(["mas", "install", "1444383602"], check=True, capture_output=True, text=True)

    @patch('subprocess.run')
    def test_restore_appstore_apps_mas_not_installed(self, mock_run):
        """Test App Store restoration when mas is not installed."""
        # Mock mas command not available
        mock_run.side_effect = [subprocess.CalledProcessError(1, "which")]
        
        restore_manager = RestoreManager(self.temp_dir)
        
        # This should not raise an exception but should print error message
        restore_manager.restore_appstore_apps()
        
        # Only the 'which mas' command should be called
        assert mock_run.call_count == 1

    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_restore_homebrew_success(self, mock_tempfile, mock_run):
        """Test successful Homebrew restoration."""
        # Mock temporary file
        mock_file = Mock()
        mock_file.name = "/tmp/test_brewfile"
        mock_tempfile.return_value.__enter__.return_value = mock_file
        
        # Mock brew command availability and bundle execution
        mock_run.side_effect = [
            Mock(returncode=0),  # which brew
            Mock(returncode=0, stderr=""),  # brew bundle
        ]
        
        restore_manager = RestoreManager(self.temp_dir)
        
        # This should not raise an exception
        restore_manager.restore_homebrew()
        
        # Verify brew commands were called
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["which", "brew"], check=True, capture_output=True)
        mock_run.assert_any_call(["brew", "bundle", "--file", "/tmp/test_brewfile"], capture_output=True, text=True)

    @patch('shutil.copy2')
    def test_restore_fonts_success(self, mock_copy):
        """Test successful font restoration."""
        restore_manager = RestoreManager(self.temp_dir)
        
        # Mock the target directory to avoid actual file operations
        with patch('pathlib.Path.expanduser') as mock_expanduser:
            # Create a mock Path object that supports / operator
            mock_target_dir = Mock(spec=Path)
            mock_target_dir.__truediv__ = Mock(side_effect=lambda x: Path(f'/tmp/mock_fonts/{x}'))
            mock_expanduser.return_value = mock_target_dir
            
            # Mock file existence checks
            def mock_exists(self):
                path_str = str(self)
                # Fonts backup directory exists
                if path_str.endswith('fonts'):
                    return True
                # Source font files exist
                if path_str.endswith(('.ttf', '.otf')) and 'mock_fonts' not in path_str:
                    return True
                # Target files don't exist
                if 'mock_fonts' in path_str:
                    return False
                return True
            
            with patch.object(Path, 'exists', mock_exists):
                restore_manager.restore_fonts()
                
                # Verify copy operations were attempted
                assert mock_copy.call_count == 2

    def test_restore_fonts_no_fonts(self):
        """Test font restoration when no fonts are in backup."""
        # Modify manifest to have no fonts
        self.manifest_data["fonts"] = []
        manifest_path = self.temp_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest_data, f)
        
        restore_manager = RestoreManager(self.temp_dir)
        
        # This should not raise an exception
        restore_manager.restore_fonts()

    def test_show_backup_summary(self, capsys):
        """Test backup summary display."""
        restore_manager = RestoreManager(self.temp_dir)
        
        # This should not raise an exception
        restore_manager.show_backup_summary()
        
        # We can't easily test rich output, but we can ensure no exceptions
        # The actual output testing would require more complex mocking