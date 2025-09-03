"""
Main CLI entry point for tractionbuild.
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.crew_controller import CrewController
from ..core.project_meta_memory import ProjectMetaMemoryManager
from ..core.output_validator import OutputValidator


app = typer.Typer()
console = Console()


@app.command()
def validate_idea(
    idea: str = typer.Argument(..., help="The idea to validate"),
    user_id: str = typer.Option("default_user", "--user-id", "-u", help="User ID for multi-tenant safety"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    token_limit: int = typer.Option(50000, "--token-limit", "-t", help="Token budget limit"),
    enable_safety: bool = typer.Option(True, "--safety", help="Enable safety features")
):
    """Validate an idea using the tractionbuild pipeline."""
    
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    console.print(Panel.fit(
        f"[bold blue]🚀 tractionbuild[/bold blue]\n"
        f"[dim]Validating idea: {idea[:100]}{'...' if len(idea) > 100 else ''}[/dim]",
        title="Idea Validation"
    ))
    
    # Initialize components with project data
    project_data = {
        "id": f"cli_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "idea": idea,
        "workflow": "validation_and_launch",
        "state": "IDEA_VALIDATION",
        "user_id": user_id,
        "token_limit": token_limit,
        "enable_safety": enable_safety,
        "created_at": datetime.now().isoformat()
    }
    
    crew_controller = CrewController(project_data)
    memory_manager = ProjectMetaMemoryManager()
    output_validator = OutputValidator()
    
    # Run validation
    async def run_validation():
        try:
            result = await crew_controller.route_and_execute()
            
            # Display results
            display_results(result, crew_controller, memory_manager)
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            return 1
        
        return 0
    
    return asyncio.run(run_validation())


@app.command()
def show_stats():
    """Show system statistics and memory information."""
    
    memory_manager = ProjectMetaMemoryManager()
    stats = memory_manager.get_memory_stats()
    
    # Create stats table
    table = Table(title="tractionbuild System Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Memory Entries", str(stats.get('total_entries', 0)))
    
    if stats.get('type_counts'):
        for memory_type, count in stats['type_counts'].items():
            table.add_row(f"Memory Type: {memory_type}", str(count))
    
    if stats.get('oldest_entry'):
        table.add_row("Oldest Entry", str(stats['oldest_entry']))
    
    if stats.get('newest_entry'):
        table.add_row("Newest Entry", str(stats['newest_entry']))
    
    console.print(table)


@app.command()
def cleanup_memory(
    days: int = typer.Option(30, "--days", "-d", help="Remove entries older than N days")
):
    """Clean up old memory entries."""
    
    memory_manager = ProjectMetaMemoryManager()
    removed_count = memory_manager.cleanup_old_memory(days)
    
    console.print(f"[green]Cleaned up {removed_count} old memory entries[/green]")


def display_results(
    result: dict, 
    crew_controller: CrewController, 
    memory_manager: ProjectMetaMemoryManager
):
    """Display validation results in a formatted way."""
    
    if result.get("status") == "completed":
        console.print(Panel.fit(
            "[bold green]✅ Validation Completed Successfully[/bold green]",
            title="Result"
        ))
        
        # Create results table
        table = Table(title="Validation Results")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Project ID", result.get("project_id", "N/A"))
        table.add_row("Token Usage", str(result.get("token_usage", 0)))
        table.add_row("Execution Time", f"{result.get('execution_time', 0):.2f}s")
        
        if "validation_result" in result:
            validation = result["validation_result"]
            if hasattr(validation, 'recommendation'):
                table.add_row("Recommendation", str(validation.recommendation))
            if hasattr(validation, 'confidence_score'):
                table.add_row("Confidence", f"{validation.confidence_score:.2f}")
        
        console.print(table)
        
        # Show project status
        project_id = result.get("project_id")
        if project_id:
            status = crew_controller.get_project_status(project_id)
            if "drift_detected" in status and status["drift_detected"]:
                console.print("[yellow]⚠️  Agent drift detected during execution[/yellow]")
        
    elif result.get("status") == "failed":
        console.print(Panel.fit(
            f"[bold red]❌ Validation Failed[/bold red]\n"
            f"Error: {result.get('error', 'Unknown error')}",
            title="Result"
        ))
    
    # Show memory stats
    memory_stats = memory_manager.get_memory_stats()
    console.print(f"[dim]Memory entries: {memory_stats.get('total_entries', 0)}[/dim]")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main() 