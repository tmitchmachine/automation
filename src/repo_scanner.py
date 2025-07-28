"""
Repository Scanner - Reads files by extension and manages file discovery
"""

import logging
import os
from typing import List, Optional, Set
from pathlib import Path
import fnmatch


class RepoScanner:
    """Scans repositories for files matching specified criteria"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def scan_repository(
        self, 
        repo_path: str, 
        file_extensions: List[str], 
        exclude_patterns: List[str]
    ) -> List[Path]:
        """
        Scan a repository for files matching the specified extensions
        
        Args:
            repo_path: Path to the repository
            file_extensions: List of file extensions to include (e.g., ['.py', '.js'])
            exclude_patterns: List of patterns to exclude (e.g., ['node_modules', '.git'])
        
        Returns:
            List of Path objects for matching files
        """
        repo_path = Path(repo_path)
        if not repo_path.exists():
            self.logger.error(f"Repository path does not exist: {repo_path}")
            return []
        
        if not repo_path.is_dir():
            self.logger.error(f"Repository path is not a directory: {repo_path}")
            return []
        
        self.logger.info(f"Scanning repository: {repo_path}")
        
        matching_files = []
        excluded_count = 0
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                # Check if file should be excluded
                if self._should_exclude(file_path, exclude_patterns):
                    excluded_count += 1
                    continue
                
                # Check if file extension matches
                if self._has_matching_extension(file_path, file_extensions):
                    matching_files.append(file_path)
        
        self.logger.info(f"Found {len(matching_files)} matching files, excluded {excluded_count} files")
        return matching_files
    
    def _should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if a file should be excluded based on patterns"""
        file_path_str = str(file_path)
        
        for pattern in exclude_patterns:
            # Handle directory patterns
            if pattern in file_path.parts:
                return True
            
            # Handle glob patterns
            if fnmatch.fnmatch(file_path_str, pattern):
                return True
            
            # Handle simple string matching
            if pattern in file_path_str:
                return True
        
        return False
    
    def _has_matching_extension(self, file_path: Path, file_extensions: List[str]) -> bool:
        """Check if file has a matching extension"""
        return file_path.suffix.lower() in [ext.lower() for ext in file_extensions]
    
    def read_file(self, file_path: Path) -> Optional[str]:
        """
        Read the content of a file
        
        Args:
            file_path: Path to the file to read
        
        Returns:
            File content as string, or None if file cannot be read
        """
        try:
            # Check file size limit
            file_size = file_path.stat().st_size
            max_size = 1024 * 1024  # 1MB default limit
            
            if file_size > max_size:
                self.logger.warning(f"File too large ({file_size} bytes): {file_path}")
                return None
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.debug(f"Read file: {file_path} ({len(content)} characters)")
            return content
            
        except UnicodeDecodeError:
            self.logger.warning(f"Could not decode file as UTF-8: {file_path}")
            return None
        except PermissionError:
            self.logger.warning(f"Permission denied reading file: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get information about a file"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': file_path.suffix,
                'name': file_path.name
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def get_repository_stats(self, repo_path: str, file_extensions: List[str], exclude_patterns: List[str]) -> dict:
        """Get statistics about a repository"""
        files = self.scan_repository(repo_path, file_extensions, exclude_patterns)
        
        stats = {
            'total_files': len(files),
            'total_size': 0,
            'extensions': {},
            'largest_files': []
        }
        
        file_sizes = []
        
        for file_path in files:
            try:
                size = file_path.stat().st_size
                stats['total_size'] += size
                file_sizes.append((file_path, size))
                
                ext = file_path.suffix.lower()
                stats['extensions'][ext] = stats['extensions'].get(ext, 0) + 1
                
            except Exception as e:
                self.logger.warning(f"Error getting stats for {file_path}: {e}")
        
        # Get largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats['largest_files'] = [
            {'path': str(fp), 'size': size} 
            for fp, size in file_sizes[:10]
        ]
        
        return stats
    
    def validate_repository(self, repo_path: str) -> bool:
        """Validate that a repository path is accessible and contains code files"""
        try:
            repo_path = Path(repo_path)
            
            if not repo_path.exists():
                self.logger.error(f"Repository path does not exist: {repo_path}")
                return False
            
            if not repo_path.is_dir():
                self.logger.error(f"Repository path is not a directory: {repo_path}")
                return False
            
            # Check if directory contains any files
            has_files = any(repo_path.iterdir())
            if not has_files:
                self.logger.warning(f"Repository appears to be empty: {repo_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating repository {repo_path}: {e}")
            return False 