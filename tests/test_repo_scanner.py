"""
Tests for the repository scanner module
"""

import pytest
from pathlib import Path
from src.repo_scanner import RepoScanner


class TestRepoScanner:
    """Test cases for RepoScanner"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = RepoScanner()
        self.test_dir = Path("test_repo")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test files
        (self.test_dir / "test.py").write_text("print('hello')")
        (self.test_dir / "test.js").write_text("console.log('hello')")
        (self.test_dir / "test.txt").write_text("hello")
        (self.test_dir / "node_modules" / "test.js").mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_scan_repository(self):
        """Test scanning repository for files"""
        files = self.scanner.scan_repository(
            str(self.test_dir),
            [".py", ".js"],
            ["node_modules"]
        )
        
        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "test.py" in file_names
        assert "test.js" in file_names
        assert "test.txt" not in file_names  # Should be excluded
    
    def test_read_file(self):
        """Test reading file content"""
        content = self.scanner.read_file(self.test_dir / "test.py")
        assert content == "print('hello')"
    
    def test_validate_repository(self):
        """Test repository validation"""
        assert self.scanner.validate_repository(str(self.test_dir)) == True
        
        # Test non-existent directory
        assert self.scanner.validate_repository("non_existent_dir") == False
    
    def test_get_repository_stats(self):
        """Test getting repository statistics"""
        stats = self.scanner.get_repository_stats(
            str(self.test_dir),
            [".py", ".js"],
            ["node_modules"]
        )
        
        assert stats["total_files"] == 2
        assert ".py" in stats["extensions"]
        assert ".js" in stats["extensions"] 