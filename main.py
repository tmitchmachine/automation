#!/usr/bin/env python3
"""
AI Code Automation Assistant - Main Entry Point

A local AI assistant that can work across multiple codebases to automatically 
improve code based on high-level goals.
"""

import sys
import os
import logging
from pathlib import Path
import typer
from rich.console import Console

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cli import CLI
from src.task_manager import TaskManager


def setup_logging():
    """Setup logging configuration"""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "ai_assistant.log")
        ]
    )


def check_config():
    """Check if configuration file exists"""
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        console = Console()
        console.print("[red]Configuration file not found: config/settings.yaml[/red]")
        console.print("Please create the configuration file before running the assistant.")
        return False
    return True


def main():
    """Main entry point"""
    setup_logging()
    
    if not check_config():
        sys.exit(1)
    
    # Create Typer app
    app = typer.Typer(
        name="ai-code-assistant",
        help="AI Code Automation Assistant - Improve code across multiple repositories",
        add_completion=False
    )
    
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
    
    @app.command()
    def init():
        """Initialize the assistant (create necessary directories)"""
        console = Console()
        
        # Create necessary directories
        dirs_to_create = ["logs", "backups", "config"]
        for dir_name in dirs_to_create:
            dir_path = Path(dir_name)
            dir_path.mkdir(exist_ok=True)
            console.print(f"[green]Created directory: {dir_name}[/green]")
        
        # Check if config file exists
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            console.print("[yellow]Configuration file not found. Please create config/settings.yaml[/yellow]")
        else:
            console.print("[green]Configuration file found[/green]")
        
        console.print("[green]Initialization complete![/green]")
    
    @app.command()
    def version():
        """Show version information"""
        console = Console()
        console.print("AI Code Automation Assistant v0.1.0")
        console.print("A local AI assistant for improving code across multiple repositories")
    
    # Run the app
    app()


if __name__ == "__main__":
    main() 