"""Main orchestration pipeline for the interior designer."""

from datetime import datetime
from pathlib import Path

from .config import get_settings
from .models.schemas import (
    DesignPreferences,
    DesignReport,
    RoomAnalysis,
    DesignRecommendation,
    GeneratedImage,
)
from .services.claude_code import ClaudeCodeService
from .services.image_gen import ImageGenService
from .utils.image import create_session_dir
from .utils.markdown import save_report


class DesignPipeline:
    """Orchestrates the interior design analysis pipeline."""

    def __init__(self):
        self.claude_service = ClaudeCodeService()
        self.image_service = ImageGenService()
        self.settings = get_settings()

    def run(
        self,
        image_paths: list[Path],
        preferences: DesignPreferences,
        generate_images: bool = True,
        progress_callback=None,
    ) -> DesignReport:
        """Run the full design analysis pipeline.

        Args:
            image_paths: List of paths to room images
            preferences: User's design preferences
            generate_images: Whether to generate AI visualizations
            progress_callback: Optional callback for progress updates

        Returns:
            DesignReport with analysis and recommendations
        """
        def update_progress(message: str):
            if progress_callback:
                progress_callback(message)

        # Create session directory
        update_progress("Creating session...")
        session_dir = create_session_dir(self.settings.ensure_output_dir())
        session_id = session_dir.name

        # Analyze each room
        room_analyses: list[RoomAnalysis] = []
        for i, image_path in enumerate(image_paths):
            update_progress(f"Analyzing room {i + 1} of {len(image_paths)}...")
            analysis = self.claude_service.analyze_room(
                image_path=image_path,
                style=preferences.style,
                budget=preferences.budget,
                specific_needs=preferences.specific_needs,
            )
            room_analyses.append(analysis)

        # Generate recommendations for each room
        all_recommendations: list[DesignRecommendation] = []
        for i, analysis in enumerate(room_analyses):
            update_progress(f"Generating recommendations for room {i + 1}...")
            recommendations = self.claude_service.generate_recommendations(
                room_analysis=analysis,
                style=preferences.style,
                budget=preferences.budget,
                specific_needs=preferences.specific_needs,
            )
            all_recommendations.extend(recommendations)

        # Generate visualizations if requested and service is available
        generated_images: list[GeneratedImage] = []
        if generate_images and self.image_service.is_available():
            update_progress("Generating room visualizations...")
            generated_dir = session_dir / "generated"

            # Generate images for high-priority recommendations with image prompts
            for rec in all_recommendations:
                if rec.priority == "high" and rec.image_edit_prompt:
                    try:
                        # Use the first image as the base
                        base_image = image_paths[0]
                        gen_image = self.image_service.generate_room_variation(
                            original_image=base_image,
                            prompt=rec.image_edit_prompt,
                            output_dir=generated_dir,
                            description=f"{rec.category.title()} - {rec.recommendation[:50]}...",
                        )
                        generated_images.append(gen_image)
                    except Exception as e:
                        # Log but don't fail the whole pipeline
                        print(f"Warning: Image generation failed: {e}")

        # Generate summary
        update_progress("Generating summary...")
        # Use the first room analysis for the summary
        summary = self.claude_service.generate_summary(
            room_analysis=room_analyses[0] if room_analyses else RoomAnalysis(
                room_type="unknown",
                current_style="unknown",
                lighting_assessment="unknown",
            ),
            recommendations=all_recommendations,
            style=preferences.style,
            budget=preferences.budget,
            specific_needs=preferences.specific_needs,
        )

        # Create the report
        report = DesignReport(
            session_id=session_id,
            original_images=image_paths,
            room_analyses=room_analyses,
            recommendations=all_recommendations,
            generated_images=generated_images,
            summary=summary,
        )

        # Save the report
        update_progress("Saving report...")
        save_report(report, session_dir)

        update_progress("Complete!")
        return report
