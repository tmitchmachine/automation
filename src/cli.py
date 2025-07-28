"""
CLI - Command-line interface and interactive chat functionality
"""

import logging
import sys
import time
from typing import Dict, Any, List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text

from .task_manager import TaskManager


class CLI:
    """Command-line interface for the AI Code Assistant"""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config_path = config_path
        self.console = Console()
        self.task_manager = TaskManager(config_path)
        self.logger = logging.getLogger(__name__)
        
        # Setup logging to also output to console
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging to output to console with rich formatting"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("logs/ai_assistant.log")
            ]
        )
    
    def run_interactive(self):
        """Run the interactive CLI mode"""
        self.console.print(Panel.fit(
            "[bold blue]AI Code Automation Assistant[/bold blue]\n"
            "Your local AI assistant for improving code across multiple repositories",
            border_style="blue"
        ))
        
        while True:
            try:
                self._show_main_menu()
                choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "q"])
                
                if choice == "q":
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break
                elif choice == "1":
                    self._run_single_task()
                elif choice == "2":
                    self._run_batch_tasks()
                elif choice == "3":
                    self._show_status()
                elif choice == "4":
                    self._configure_repositories()
                elif choice == "5":
                    self._test_ai_connection()
                elif choice == "6":
                    self._show_help()
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted by user[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                self.logger.error(f"CLI error: {e}")
    
    def _show_main_menu(self):
        """Display the main menu"""
        menu = Table(title="Main Menu", show_header=False, border_style="blue")
        menu.add_column("Option", style="cyan")
        menu.add_column("Description", style="white")
        
        menu.add_row("1", "Run single task")
        menu.add_row("2", "Run batch tasks")
        menu.add_row("3", "Show status")
        menu.add_row("4", "Configure repositories")
        menu.add_row("5", "Test AI connection")
        menu.add_row("6", "Help")
        menu.add_row("q", "Quit")
        
        self.console.print(menu)
    
    def _run_single_task(self):
        """Run a single task on a repository"""
        # Show available repositories
        repos = self._get_available_repositories()
        if not repos:
            self.console.print("[red]No repositories configured[/red]")
            return
        
        repo_table = Table(title="Available Repositories")
        repo_table.add_column("Name", style="cyan")
        repo_table.add_column("Path", style="white")
        repo_table.add_column("Status", style="green")
        
        for repo in repos:
            status = "✓" if self.task_manager.repo_scanner.validate_repository(repo['path']) else "✗"
            repo_table.add_row(repo['name'], repo['path'], status)
        
        self.console.print(repo_table)
        
        # Get repository choice
        repo_name = Prompt.ask("Select repository", choices=[repo['name'] for repo in repos])
        
        # Get goal
        goals = self._get_available_goals()
        goal_table = Table(title="Available Goals")
        goal_table.add_column("Goal", style="cyan")
        goal_table.add_column("Description", style="white")
        
        for goal, description in goals.items():
            goal_table.add_row(goal, description)
        
        self.console.print(goal_table)
        
        goal = Prompt.ask("Select goal", choices=list(goals.keys()))
        goal_description = goals[goal]
        
        # Confirm task
        if Confirm.ask(f"Run '{goal_description}' on repository '{repo_name}'?"):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                
                # Create and execute task
                task_obj = self.task_manager.create_task(repo_name, goal_description)
                success = self.task_manager.execute_task(task_obj)
                
                if success:
                    self.console.print(f"[green]Task completed successfully![/green]")
                else:
                    self.console.print(f"[red]Task failed![/red]")
    
    def _run_batch_tasks(self):
        """Run multiple tasks in batch"""
        # Get default goals
        default_goals = self.task_manager.get_default_goals()
        repos = self._get_available_repositories()
        
        if not repos or not default_goals:
            self.console.print("[red]No repositories or goals configured[/red]")
            return
        
        # Create tasks for all repos with all default goals
        tasks_created = 0
        for repo in repos:
            for goal in default_goals:
                try:
                    self.task_manager.create_task(repo['name'], goal)
                    tasks_created += 1
                except Exception as e:
                    self.console.print(f"[red]Error creating task for {repo['name']}: {e}[/red]")
        
        if tasks_created == 0:
            self.console.print("[red]No tasks created[/red]")
            return
        
        # Execute all tasks
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(f"Executing {tasks_created} tasks...", total=tasks_created)
            
            results = self.task_manager.execute_all_tasks()
            
            progress.update(task, completed=tasks_created)
        
        # Show results
        self.console.print(f"[green]Batch completed![/green]")
        self.console.print(f"Completed: {results['completed']}")
        self.console.print(f"Failed: {results['failed']}")
        self.console.print(f"Total: {results['total']}")
    
    def _show_status(self):
        """Show current status of tasks and repositories"""
        # Task status
        status = self.task_manager.get_task_status()
        status_table = Table(title="Task Status")
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="white")
        
        for status_name, count in status.items():
            color = "green" if status_name == "completed" else "yellow" if status_name == "pending" else "red"
            status_table.add_row(status_name, str(count), style=color)
        
        self.console.print(status_table)
        
        # Repository status
        repos = self._get_available_repositories()
        if repos:
            repo_table = Table(title="Repository Status")
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Path", style="white")
            repo_table.add_column("Status", style="green")
            repo_table.add_column("Files", style="blue")
            
            for repo in repos:
                status = "✓" if self.task_manager.repo_scanner.validate_repository(repo['path']) else "✗"
                files = len(self.task_manager.repo_scanner.scan_repository(
                    repo['path'], repo['file_extensions'], repo['exclude_patterns']
                ))
                repo_table.add_row(repo['name'], repo['path'], status, str(files))
            
            self.console.print(repo_table)
    
    def _configure_repositories(self):
        """Configure repositories interactively"""
        self.console.print("[yellow]Repository configuration is done via config/settings.yaml[/yellow]")
        self.console.print("Please edit the configuration file to add or modify repositories.")
    
    def _test_ai_connection(self):
        """Test connection to AI providers"""
        ai_interface = self.task_manager.ai_interface
        
        providers = ai_interface.get_available_providers()
        if not providers:
            self.console.print("[red]No AI providers available[/red]")
            return
        
        for provider in providers:
            self.console.print(f"Testing {provider} connection...")
            success = ai_interface.test_connection(provider)
            
            if success:
                self.console.print(f"[green]✓ {provider} connection successful[/green]")
            else:
                self.console.print(f"[red]✗ {provider} connection failed[/red]")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
[bold]AI Code Automation Assistant Help[/bold]

This tool helps you automatically improve code across multiple repositories using AI.

[bold]Basic Usage:[/bold]
1. Configure repositories in config/settings.yaml
2. Set up AI provider API keys (Gemini/Claude)
3. Run tasks to improve your code

[bold]Goals:[/bold]
- refactor: Improve code readability and maintainability
- test: Add comprehensive unit tests
- performance: Optimize code for better performance
- security: Fix potential security vulnerabilities
- documentation: Add or improve documentation

[bold]Configuration:[/bold]
Edit config/settings.yaml to:
- Add repository paths
- Configure AI providers
- Set file processing options
- Customize goals and tasks

[bold]Safety Features:[/bold]
- Automatic backups before changes
- Preview mode available
- Detailed logging of all changes
- Rollback capability from backups
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def _get_available_repositories(self) -> List[Dict[str, Any]]:
        """Get list of available repositories from config"""
        repos = []
        for repo in self.task_manager.config.get('repositories', []):
            if repo.get('enabled', True):
                repos.append(repo)
        return repos
    
    def _get_available_goals(self) -> Dict[str, str]:
        """Get available goals from configuration"""
        custom_goals = self.task_manager.get_custom_goals()
        default_goals = self.task_manager.get_default_goals()
        
        goals = {}
        
        # Add custom goals
        goals.update(custom_goals)
        
        # Add default goals as simple strings
        for goal in default_goals:
            goals[goal] = goal
        
        return goals


def main():
    """Main CLI entry point"""
    app = typer.Typer(help="AI Code Automation Assistant")
    
    @app.command()
    def interactive():
        """Start interactive mode"""
        cli = CLI()
        cli.run_interactive()
    
    @app.command()
    def run(
        repo: str = typer.Option(None, "--repo", "-r", help="Repository name"),
        goal: str = typer.Option(None, "--goal", "-g", help="Improvement goal"),
        watch: bool = typer.Option(False, "--watch", "-w", help="Watch mode"),
        interval: int = typer.Option(300, "--interval", "-i", help="Watch interval in seconds")
    ):
        """Run tasks on repositories"""
        cli = CLI()
        
        if watch:
            cli._run_watch_mode(interval)
        elif repo and goal:
            cli._run_single_task_cli(repo, goal)
        else:
            cli.run_interactive()
    
    @app.command()
    def status():
        """Show current status"""
        cli = CLI()
        cli._show_status()
    
    @app.command()
    def test():
        """Test AI connections"""
        cli = CLI()
        cli._test_ai_connection()
    
    app()


if __name__ == "__main__":
    main() 