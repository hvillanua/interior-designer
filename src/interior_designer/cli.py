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


@app.command(name="test-image")
def test_image(
    prompt: Annotated[
        str,
        typer.Option("--prompt", "-p", help="Text prompt for image generation"),
    ] = "A modern minimalist living room with a gray sofa and wooden floor",
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Override image model"),
    ] = None,
    image: Annotated[
        Optional[Path],
        typer.Option("--image", "-i", help="Optional input image for editing"),
    ] = None,
):
    """Test image generation (text-to-image or image editing)."""
    from openai import OpenAI
    from interior_designer.utils.image import create_session_dir
    import base64

    if image and not image.exists():
        console.print(f"[red]Error: Image not found: {image}[/red]")
        raise typer.Exit(1)

    settings = get_settings()
    image_model = model or settings.openrouter_image_model

    console.print("[bold]Testing image generation...[/bold]\n")
    console.print(f"Model: [cyan]{image_model}[/cyan]")
    console.print(f"Prompt: {prompt}")
    if image:
        console.print(f"Input image: {image}")
    console.print()

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key.get_secret_value(),
    )

    # Build message content
    if image:
        from interior_designer.utils.image import resize_image_for_api
        image_bytes = resize_image_for_api(image, max_size=512)
        image_b64 = base64.b64encode(image_bytes).decode()
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]
    else:
        content = prompt

    console.print("Sending request...")
    try:
        response = client.chat.completions.create(
            model=image_model,
            messages=[{"role": "user", "content": content}],
            extra_body={"modalities": ["image", "text"]}
        )

        msg = response.choices[0].message
        console.print(f"\n[bold]Message type:[/bold] {type(msg)}")
        console.print(f"[bold]Has images attr:[/bold] {hasattr(msg, 'images')}")

        if hasattr(msg, 'images') and msg.images:
            console.print(f"[green]Found {len(msg.images)} image(s)![/green]")
            session_dir = create_session_dir(settings.ensure_output_dir())
            for i, img in enumerate(msg.images):
                url = img['image_url']['url']
                if url.startswith("data:"):
                    _, data = url.split(",", 1)
                    img_bytes = base64.b64decode(data)
                    out_path = session_dir / "generated" / f"test_{i}.png"
                    out_path.parent.mkdir(exist_ok=True)
                    out_path.write_bytes(img_bytes)
                    console.print(f"[green]Saved:[/green] {out_path}")
        else:
            console.print(f"[yellow]No images found. Content: {msg.content[:200] if msg.content else 'EMPTY'}[/yellow]")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


@app.command(name="test-pdf")
def test_pdf(
    output_format: Annotated[
        str,
        typer.Option("--output-format", "-f", help="Output format: pdf, md"),
    ] = "pdf",
):
    """Test PDF generation with mock data (no API calls)."""
    from datetime import datetime
    from interior_designer.models.schemas import (
        DesignReport, RoomAnalysis, DesignRecommendation
    )
    from interior_designer.utils.markdown import save_report
    from interior_designer.utils.image import create_session_dir

    console.print("[bold]Testing PDF generation with mock data...[/bold]\n")

    settings = get_settings()
    session_dir = create_session_dir(settings.ensure_output_dir())
    session_id = session_dir.name

    # Create mock data with various Unicode characters to test sanitization
    mock_analysis = RoomAnalysis(
        room_type="living room",
        current_style="Contemporary-Transitional with clean lines",
        estimated_dimensions="15' x 20' - approximately 300 sq ft",
        existing_furniture=["Gray sectional sofa", "Light wood coffee table", "Floor lamp"],
        color_palette=["Warm white", "Light gray", "Natural wood tones"],
        lighting_assessment="Good natural light from windows - could use accent lighting",
        strengths=["Open floor plan", "Neutral palette", "Quality flooring"],
        improvement_opportunities=["Add statement lighting", "Layer textures", "Include artwork"],
    )

    mock_recommendations = [
        DesignRecommendation(
            category="lighting",
            priority="high",
            current_state="Room relies on natural light and basic fixtures",
            recommendation="Install a modern pendant light or chandelier as a focal point - consider dimmable options",
            estimated_cost="$200-$500 for quality fixture",
            product_suggestions=["West Elm Mobile Chandelier", "CB2 Sputnik Pendant"],
        ),
        DesignRecommendation(
            category="decor",
            priority="high",
            current_state="Walls are bare with no artwork or visual interest",
            recommendation="Create a gallery wall or add large-scale artwork above the sofa",
            estimated_cost="$150-$400 depending on pieces",
            product_suggestions=["Society6 prints", "Local artist originals"],
        ),
        DesignRecommendation(
            category="textiles",
            priority="medium",
            current_state="Limited soft textures in the space",
            recommendation="Add throw pillows, blankets, and an area rug to layer textures",
            estimated_cost="$300-$600 for complete set",
            product_suggestions=["Ruggable washable rugs", "Pottery Barn throw pillows"],
        ),
    ]

    mock_summary = """This living room analysis reveals a well-maintained space with strong foundational elements.

The room's greatest assets include its open floor plan, neutral color palette, and quality light wood flooring. These create a versatile canvas for design enhancement.

Key recommendations focus on three areas: lighting improvements to create ambiance, wall decor to add visual interest, and textile layering to increase comfort and warmth.

The suggested improvements align with a medium budget and contemporary style preferences, emphasizing quality over quantity for lasting impact."""

    report = DesignReport(
        session_id=session_id,
        room_analyses=[mock_analysis],
        recommendations=mock_recommendations,
        summary=mock_summary,
        generated_images=[],
        original_images=[],
    )

    try:
        output_path = save_report(report, session_dir, output_format)
        console.print(f"[green]Success![/green] Report saved to: {output_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
