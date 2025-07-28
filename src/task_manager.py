"""
Task Manager - Handles goals and task orchestration
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml

from .repo_scanner import RepoScanner
from .ai_interface import AIInterface
from .file_writer import FileWriter


@dataclass
class Task:
    """Represents a task to be performed on a repository"""
    repo_name: str
    repo_path: str
    goal: str
    file_extensions: List[str]
    exclude_patterns: List[str]
    priority: int = 1
    status: str = "pending"


class TaskManager:
    """Manages tasks and orchestrates the improvement process"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.repo_scanner = RepoScanner()
        self.ai_interface = AIInterface(self.config)
        self.file_writer = FileWriter(self.config)
        
        self.tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration: {e}")
            raise
    
    def create_task(self, repo_name: str, goal: str, priority: int = 1) -> Task:
        """Create a new task for a repository"""
        repo_config = self._get_repo_config(repo_name)
        if not repo_config:
            raise ValueError(f"Repository '{repo_name}' not found in configuration")
        
        task = Task(
            repo_name=repo_name,
            repo_path=repo_config['path'],
            goal=goal,
            file_extensions=repo_config['file_extensions'],
            exclude_patterns=repo_config['exclude_patterns'],
            priority=priority
        )
        
        self.tasks.append(task)
        self.logger.info(f"Created task: {repo_name} - {goal}")
        return task
    
    def _get_repo_config(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository configuration by name"""
        for repo in self.config.get('repositories', []):
            if repo['name'] == repo_name and repo.get('enabled', True):
                return repo
        return None
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks sorted by priority"""
        return sorted(
            [task for task in self.tasks if task.status == "pending"],
            key=lambda x: x.priority,
            reverse=True
        )
    
    def execute_task(self, task: Task) -> bool:
        """Execute a single task"""
        try:
            self.logger.info(f"Executing task: {task.repo_name} - {task.goal}")
            task.status = "running"
            
            # 1. Scan repository for files
            files = self.repo_scanner.scan_repository(
                task.repo_path,
                task.file_extensions,
                task.exclude_patterns
            )
            
            if not files:
                self.logger.warning(f"No files found in {task.repo_name}")
                task.status = "completed"
                return True
            
            # 2. Process each file
            processed_files = 0
            for file_path in files:
                try:
                    success = self._process_file(file_path, task.goal)
                    if success:
                        processed_files += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
            
            # 3. Update task status
            task.status = "completed"
            self.completed_tasks.append(task)
            self.tasks.remove(task)
            
            self.logger.info(f"Task completed: {processed_files} files processed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            task.status = "failed"
            return False
    
    def _process_file(self, file_path: Path, goal: str) -> bool:
        """Process a single file with the given goal"""
        try:
            # Read file content
            content = self.repo_scanner.read_file(file_path)
            if not content:
                return False
            
            # Get AI suggestions
            suggestions = self.ai_interface.get_suggestions(content, goal, str(file_path))
            if not suggestions:
                return False
            
            # Apply changes
            success = self.file_writer.apply_changes(file_path, suggestions)
            return success
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return False
    
    def execute_all_tasks(self) -> Dict[str, int]:
        """Execute all pending tasks"""
        results = {"completed": 0, "failed": 0, "total": 0}
        
        pending_tasks = self.get_pending_tasks()
        results["total"] = len(pending_tasks)
        
        for task in pending_tasks:
            success = self.execute_task(task)
            if success:
                results["completed"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get current task status"""
        return {
            "pending": len([t for t in self.tasks if t.status == "pending"]),
            "running": len([t for t in self.tasks if t.status == "running"]),
            "completed": len(self.completed_tasks),
            "failed": len([t for t in self.tasks if t.status == "failed"])
        }
    
    def clear_completed_tasks(self):
        """Clear completed tasks from memory"""
        self.completed_tasks.clear()
        self.logger.info("Cleared completed tasks")
    
    def get_custom_goals(self) -> Dict[str, str]:
        """Get available custom goals from configuration"""
        return self.config.get('tasks', {}).get('custom_goals', {})
    
    def get_default_goals(self) -> List[str]:
        """Get default goals from configuration"""
        return self.config.get('tasks', {}).get('default_goals', []) 