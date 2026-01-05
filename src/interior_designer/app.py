"""Streamlit web interface for the interior designer."""

import streamlit as st
from pathlib import Path
import tempfile

from interior_designer.config import get_settings
from interior_designer.models.schemas import DesignPreferences
from interior_designer.pipeline import DesignPipeline
from interior_designer.utils.image import save_uploaded_image, create_session_dir


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Interior Design AI",
        page_icon="🏠",
        layout="wide",
    )

    st.title("🏠 Interior Design AI Assistant")
    st.markdown("Upload room photos and get AI-powered design recommendations")

    # Initialize settings
    settings = get_settings()

    # Sidebar for preferences
    with st.sidebar:
        st.header("Design Preferences")

        style = st.selectbox(
            "Preferred Style",
            [
                "Auto-detect",
                "Modern",
                "Minimalist",
                "Scandinavian",
                "Industrial",
                "Rustic",
                "Traditional",
                "Bohemian",
                "Mid-Century Modern",
                "Contemporary",
            ],
        )

        budget = st.select_slider(
            "Budget Level",
            options=["low", "medium", "high"],
            value="medium",
        )

        specific_needs = st.text_area(
            "Specific Requirements",
            placeholder="e.g., Need more storage, better lighting, pet-friendly furniture...",
            height=100,
        )

        generate_images = st.checkbox(
            "Generate AI room visualizations",
            value=True,
            help="Uses OpenRouter API to generate images (requires API key)",
        )

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "This app uses Claude AI to analyze your room photos and "
            "provide personalized design recommendations."
        )

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📷 Upload Room Photos")

        uploaded_files = st.file_uploader(
            "Choose images",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            help="Upload one or more photos of the room(s) you want to redesign",
        )

        if uploaded_files:
            st.subheader("Uploaded Images")
            for file in uploaded_files:
                st.image(file, caption=file.name, width="stretch")

    with col2:
        st.header("📋 Analysis & Recommendations")

        if st.button(
            "🔍 Analyze Rooms",
            type="primary",
            disabled=not uploaded_files,
            width="stretch",
        ):
            if not uploaded_files:
                st.error("Please upload at least one room photo.")
                return

            # Create a temporary session directory
            session_dir = create_session_dir(settings.ensure_output_dir())

            # Save uploaded files
            image_paths = []
            for file in uploaded_files:
                path = save_uploaded_image(file, session_dir)
                image_paths.append(path)

            # Create preferences
            preferences = DesignPreferences(
                style=None if style == "Auto-detect" else style.lower(),
                budget=budget,
                specific_needs=specific_needs or None,
            )

            # Run the pipeline with progress
            progress_text = st.empty()
            progress_bar = st.progress(0)

            steps = ["Creating session", "Analyzing rooms", "Generating recommendations", "Generating visualizations", "Creating report", "Complete"]
            current_step = 0

            def update_progress(message: str):
                nonlocal current_step
                progress_text.text(message)
                # Find which step we're on
                for i, step in enumerate(steps):
                    if step.lower() in message.lower():
                        current_step = i
                        break
                progress_bar.progress((current_step + 1) / len(steps))

            try:
                pipeline = DesignPipeline()
                report = pipeline.run(
                    image_paths=image_paths,
                    preferences=preferences,
                    generate_images=generate_images,
                    progress_callback=update_progress,
                )

                progress_bar.progress(1.0)
                progress_text.text("Analysis complete!")

                st.success("✅ Analysis complete!")

                # Display results
                st.markdown("---")

                # Room Analysis
                st.subheader("🔍 Room Analysis")
                for i, analysis in enumerate(report.room_analyses):
                    with st.expander(f"📍 {analysis.room_type.title()}", expanded=True):
                        col_a, col_b = st.columns(2)

                        with col_a:
                            st.markdown(f"**Current Style:** {analysis.current_style}")
                            st.markdown(f"**Lighting:** {analysis.lighting_assessment}")

                            if analysis.existing_furniture:
                                st.markdown("**Existing Furniture:**")
                                for item in analysis.existing_furniture[:5]:
                                    st.markdown(f"- {item}")

                        with col_b:
                            if analysis.color_palette:
                                st.markdown(f"**Colors:** {', '.join(analysis.color_palette)}")

                            if analysis.strengths:
                                st.markdown("**Strengths:**")
                                for s in analysis.strengths[:3]:
                                    st.markdown(f"- ✓ {s}")

                            if analysis.improvement_opportunities:
                                st.markdown("**Opportunities:**")
                                for o in analysis.improvement_opportunities[:3]:
                                    st.markdown(f"- → {o}")

                # Recommendations
                st.subheader("💡 Design Recommendations")
                for rec in report.recommendations:
                    priority_color = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢",
                    }
                    with st.expander(
                        f"{priority_color.get(rec.priority, '⚪')} {rec.category.title()} - {rec.priority.upper()} priority"
                    ):
                        st.markdown(f"**Current:** {rec.current_state}")
                        st.markdown(f"**Recommendation:** {rec.recommendation}")

                        if rec.estimated_cost:
                            st.markdown(f"**Estimated Cost:** {rec.estimated_cost}")

                        if rec.product_suggestions:
                            st.markdown("**Suggested Products:**")
                            for product in rec.product_suggestions:
                                st.markdown(f"- {product}")

                # Generated Images
                if report.generated_images:
                    st.subheader("🖼️ AI-Generated Visualizations")
                    for gen_img in report.generated_images:
                        if gen_img.path.exists():
                            st.image(
                                str(gen_img.path),
                                caption=gen_img.description,
                                width="stretch",
                            )

                # Summary
                st.subheader("📝 Summary")
                st.markdown(report.summary)

                # Download report
                st.markdown("---")
                report_path = session_dir / "report.md"
                if report_path.exists():
                    st.download_button(
                        "📥 Download Full Report",
                        report_path.read_text(),
                        file_name=f"design_report_{report.session_id}.md",
                        mime="text/markdown",
                        width="stretch",
                    )

            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")
                st.exception(e)


if __name__ == "__main__":
    main()
