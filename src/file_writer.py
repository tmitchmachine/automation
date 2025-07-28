"""
File Writer - Applies changes to files with backup functionality
"""

import logging
import shutil
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import difflib


class FileWriter:
    """Handles file writing and backup operations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_dir = Path(config.get('file_processing', {}).get('backup_directory', './backups'))
        self.auto_apply = config.get('file_processing', {}).get('auto_apply_changes', True)
        self.backup_original = config.get('file_processing', {}).get('backup_original_files', True)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def apply_changes(self, file_path: Path, new_content: str) -> bool:
        """
        Apply changes to a file with optional backup
        
        Args:
            file_path: Path to the file to modify
            new_content: New content to write to the file
        
        Returns:
            True if changes were applied successfully, False otherwise
        """
        try:
            # Read original content
            original_content = self._read_file(file_path)
            if original_content is None:
                return False
            
            # Check if content actually changed
            if original_content.strip() == new_content.strip():
                self.logger.info(f"No changes needed for {file_path}")
                return True
            
            # Create backup if enabled
            if self.backup_original:
                backup_path = self._create_backup(file_path)
                if not backup_path:
                    self.logger.warning(f"Failed to create backup for {file_path}")
                    return False
            
            # Write new content
            if self.auto_apply:
                success = self._write_file(file_path, new_content)
                if success:
                    self.logger.info(f"Applied changes to {file_path}")
                    self._log_changes(file_path, original_content, new_content)
                    return True
                else:
                    self.logger.error(f"Failed to write changes to {file_path}")
                    return False
            else:
                # Preview mode - just log what would be changed
                self.logger.info(f"Preview mode: Would apply changes to {file_path}")
                self._log_changes(file_path, original_content, new_content)
                return True
                
        except Exception as e:
            self.logger.error(f"Error applying changes to {file_path}: {e}")
            return False
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _write_file(self, file_path: Path, content: str) -> bool:
        """Write content to file safely"""
        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of the original file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def _log_changes(self, file_path: Path, original_content: str, new_content: str):
        """Log the changes made to a file"""
        try:
            # Generate diff
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(file_path),
                tofile=str(file_path)
            ))
            
            if diff:
                diff_text = ''.join(diff)
                self.logger.info(f"Changes for {file_path}:\n{diff_text}")
            else:
                self.logger.info(f"No changes detected for {file_path}")
                
        except Exception as e:
            self.logger.error(f"Error logging changes for {file_path}: {e}")
    
    def restore_from_backup(self, file_path: Path, backup_path: Path) -> bool:
        """Restore a file from its backup"""
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"Restored {file_path} from backup {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring {file_path} from backup: {e}")
            return False
    
    def list_backups(self, file_path: Path = None) -> list:
        """List available backups"""
        try:
            backups = []
            for backup_file in self.backup_dir.glob("*"):
                if backup_file.is_file():
                    backup_info = {
                        'path': backup_file,
                        'name': backup_file.name,
                        'size': backup_file.stat().st_size,
                        'modified': datetime.fromtimestamp(backup_file.stat().st_mtime)
                    }
                    
                    # Filter by original file if specified
                    if file_path:
                        if file_path.stem in backup_file.stem:
                            backups.append(backup_info)
                    else:
                        backups.append(backup_info)
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x['modified'], reverse=True)
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
            return []
    
    def cleanup_old_backups(self, max_backups: int = 10):
        """Clean up old backups, keeping only the most recent ones"""
        try:
            backups = self.list_backups()
            
            if len(backups) > max_backups:
                backups_to_delete = backups[max_backups:]
                
                for backup in backups_to_delete:
                    try:
                        backup['path'].unlink()
                        self.logger.info(f"Deleted old backup: {backup['name']}")
                    except Exception as e:
                        self.logger.error(f"Error deleting backup {backup['name']}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
    
    def get_file_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get statistics about a file"""
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'exists': file_path.exists(),
                'is_file': file_path.is_file(),
                'is_dir': file_path.is_dir()
            }
        except Exception as e:
            self.logger.error(f"Error getting file stats for {file_path}: {e}")
            return {}
    
    def validate_file_path(self, file_path: Path) -> bool:
        """Validate that a file path is safe to modify"""
        try:
            # Check if file exists and is writable
            if file_path.exists():
                if not file_path.is_file():
                    self.logger.error(f"Path is not a file: {file_path}")
                    return False
                
                # Check if file is writable
                if not os.access(file_path, os.W_OK):
                    self.logger.error(f"File is not writable: {file_path}")
                    return False
            
            # Check if parent directory is writable
            parent_dir = file_path.parent
            if not os.access(parent_dir, os.W_OK):
                self.logger.error(f"Parent directory is not writable: {parent_dir}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file path {file_path}: {e}")
            return False 