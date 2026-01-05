"""Command-line interface for the interior designer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from interior_designer.config import get_settings
from interior_designer.models.schemas import DesignPreferences
from interior_designer.pipeline import DesignPipeline

app = typer.Typer(
    name="interior-designer",
    help="AI-powered interior design assistant",
    no_args_is_help=True,
)
console = Console()


@app.command()
def analyze(
    images: Annotated[
        list[Path],
        typer.Argument(help="Room images to analyze"),
    ],
    style: Annotated[
        Optional[str],
        typer.Option("--style", "-s", help="Preferred style (modern, rustic, minimalist, etc.)"),
    ] = None,
    budget: Annotated[
        Optional[str],
        typer.Option("--budget", "-b", help="Budget level: low, medium, high"),
    ] = None,
    needs: Annotated[
        Optional[str],
        typer.Option("--needs", "-n", help="Specific requirements"),
    ] = None,
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Claude model: sonnet, opus, haiku"),
    ] = "sonnet",
    output_format: Annotated[
        str,
        typer.Option("--output-format", "-f", help="Output format: pdf, md"),
    ] = "pdf",
    no_images: Annotated[
        bool,
        typer.Option("--no-images", help="Skip AI image generation"),
    ] = False,
):
    """Analyze room photos and generate design recommendations."""
    # Validate images exist
    for img in images:
        if not img.exists():
            console.print(f"[red]Error: Image not found: {img}[/red]")
            raise typer.Exit(1)

    # Validate budget
    if budget and budget not in ("low", "medium", "high"):
        console.print(f"[red]Error: Budget must be low, medium, or high[/red]")
        raise typer.Exit(1)

    # Validate model
    if model not in ("sonnet", "opus", "haiku"):
        console.print(f"[red]Error: Model must be sonnet, opus, or haiku[/red]")
        raise typer.Exit(1)

    # Validate output format
    if output_format not in ("pdf", "md"):
        console.print(f"[red]Error: Output format must be pdf or md[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Interior Design AI Assistant[/bold]")
    console.print(f"Model: [cyan]{model}[/cyan]")
    console.print(f"Images: {len(images)}")
    if style:
        console.print(f"Style: {style}")
    if budget:
        console.print(f"Budget: {budget}")
    console.print()

    # Build preferences
    preferences = DesignPreferences(
        style=style,
        budget=budget,
        specific_needs=needs,
    )

    # Run pipeline with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting analysis...", total=None)

        def update_progress(message: str):
            progress.update(task, description=message)

        try:
            pipeline = DesignPipeline()
            report = pipeline.run(
                image_paths=images,
                preferences=preferences,
                generate_images=not no_images,
                progress_callback=update_progress,
                model=model,
                output_format=output_format,
            )

            progress.update(task, description="[green]Complete!")

        except Exception as e:
            progress.update(task, description=f"[red]Failed: {e}")
            console.print(f"\n[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Print results
    console.print(f"\n[green]Analysis complete![/green]")
    console.print(f"\nSession: [cyan]{report.session_id}[/cyan]")

    # Summary
    console.print(f"\n[bold]Summary[/bold]")
    console.print(report.summary[:500] + "..." if len(report.summary) > 500 else report.summary)

    # Recommendations count
    console.print(f"\n[bold]Recommendations:[/bold] {len(report.recommendations)}")
    for rec in report.recommendations[:3]:
        priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(rec.priority, "white")
        console.print(f"  [{priority_color}]{rec.priority.upper()}[/{priority_color}] {rec.category}: {rec.recommendation[:60]}...")

    # Output files
    settings = get_settings()
    session_dir = settings.output_dir / report.session_id

    if output_format == "pdf":
        pdf_path = session_dir / "report.pdf"
        if pdf_path.exists():
            console.print(f"\n[bold]PDF Report:[/bold] {pdf_path}")
    else:
        md_path = session_dir / "report.md"
        if md_path.exists():
            console.print(f"\n[bold]Markdown Report:[/bold] {md_path}")

    if report.generated_images:
        console.print(f"[bold]Generated Images:[/bold] {len(report.generated_images)}")
        for img in report.generated_images:
            console.print(f"  - {img.path}")


@app.command()
def models():
    """List available Claude models."""
    console.print("\n[bold]Available Claude Models[/bold]\n")
    console.print("  [cyan]sonnet[/cyan]  - Claude Sonnet (default, balanced)")
    console.print("  [cyan]opus[/cyan]    - Claude Opus (most capable)")
    console.print("  [cyan]haiku[/cyan]   - Claude Haiku (fastest)")
    console.print("\nUse with: --model <name>")


if __name__ == "__main__":
    app()
