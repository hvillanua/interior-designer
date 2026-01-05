"""PDF report generation using FPDF2."""

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from ..models.schemas import DesignReport


def sanitize_text(text: str) -> str:
    """Replace Unicode characters not supported by basic PDF fonts."""
    replacements = {
        "—": "-",  # em dash
        "–": "-",  # en dash
        "'": "'",  # smart quote
        "'": "'",  # smart quote
        """: '"',  # smart quote
        """: '"',  # smart quote
        "…": "...",  # ellipsis
        "•": "*",  # bullet
        "→": "->",  # arrow
        "←": "<-",  # arrow
        "×": "x",  # multiplication
        "÷": "/",  # division
        "°": " deg",  # degree
        "™": "(TM)",  # trademark
        "©": "(c)",  # copyright
        "®": "(R)",  # registered
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class DesignReportPDF(FPDF):
    """Custom PDF class for design reports."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """Add header to each page."""
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Interior Design AI Report", align="L")
        self.ln(5)

    def footer(self):
        """Add footer with page number."""
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self, session_id: str):
        """Create title page."""
        self.add_page()
        self.set_font("helvetica", "B", 28)
        self.set_text_color(0, 0, 0)
        self.ln(60)
        self.cell(0, 20, "Interior Design Report", align="C", ln=True)

        self.set_font("helvetica", "", 14)
        self.set_text_color(80, 80, 80)
        self.ln(10)
        self.cell(0, 10, f"Session: {session_id}", align="C", ln=True)
        self.cell(0, 10, f"Generated: {datetime.now().strftime('%B %d, %Y')}", align="C", ln=True)

        self.ln(40)
        self.set_font("helvetica", "I", 10)
        self.cell(0, 10, "Powered by Claude AI", align="C", ln=True)

    def section_header(self, title: str):
        """Add a section header."""
        self.set_font("helvetica", "B", 16)
        self.set_text_color(0, 51, 102)
        self.ln(5)
        self.cell(0, 10, title, ln=True)
        self.set_draw_color(0, 51, 102)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def subsection_header(self, title: str):
        """Add a subsection header."""
        self.set_font("helvetica", "B", 12)
        self.set_text_color(51, 51, 51)
        self.ln(3)
        self.cell(0, 8, title, ln=True)

    def body_text(self, text: str):
        """Add body text."""
        self.set_font("helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, sanitize_text(text))
        self.ln(2)

    def bullet_point(self, text: str):
        """Add a bullet point."""
        self.set_font("helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        # Reset x to left margin before adding bullet
        self.set_x(self.l_margin)
        self.multi_cell(0, 5, f"    - {sanitize_text(text)}")

    def priority_badge(self, priority: str):
        """Add a priority badge."""
        colors = {
            "high": (220, 53, 69),    # Red
            "medium": (255, 193, 7),   # Yellow
            "low": (40, 167, 69),      # Green
        }
        r, g, b = colors.get(priority, (128, 128, 128))
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", "B", 8)
        self.cell(25, 6, priority.upper(), fill=True, align="C", ln=True)
        self.set_text_color(0, 0, 0)

    def add_image_safe(self, image_path: Path, width: int = 80):
        """Add an image if it exists."""
        if image_path.exists():
            try:
                # Center the image
                x = (210 - width) / 2
                self.image(str(image_path), x=x, w=width)
                self.ln(5)
                return True
            except Exception:
                return False
        return False


def generate_pdf_report(report: DesignReport, output_path: Path, original_images: list[Path] | None = None) -> Path:
    """Generate a PDF report from a DesignReport.

    Args:
        report: The design report to convert
        output_path: Path to save the PDF
        original_images: Optional list of original image paths to include

    Returns:
        Path to the generated PDF
    """
    pdf = DesignReportPDF()
    pdf.alias_nb_pages()

    # Title page
    pdf.title_page(report.session_id)

    # Executive Summary
    pdf.add_page()
    pdf.section_header("Executive Summary")
    pdf.body_text(report.summary)

    # Room Analysis
    if report.room_analyses:
        pdf.add_page()
        pdf.section_header("Room Analysis")

        for i, analysis in enumerate(report.room_analyses, 1):
            pdf.subsection_header(f"Room {i}: {analysis.room_type.title()}")

            # Add original image if available
            if original_images and i <= len(original_images):
                pdf.add_image_safe(original_images[i - 1], width=100)

            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, "Current Style:", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 5, sanitize_text(analysis.current_style))

            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, "Lighting:", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 5, sanitize_text(analysis.lighting_assessment))

            if analysis.color_palette:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Colors:", ln=True)
                pdf.set_font("helvetica", "", 10)
                pdf.multi_cell(0, 5, sanitize_text(", ".join(analysis.color_palette)))

            if analysis.existing_furniture:
                pdf.ln(3)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Existing Furniture:", ln=True)
                for item in analysis.existing_furniture[:6]:
                    pdf.bullet_point(item)

            if analysis.strengths:
                pdf.ln(3)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Strengths:", ln=True)
                for s in analysis.strengths[:4]:
                    pdf.bullet_point(s)

            if analysis.improvement_opportunities:
                pdf.ln(3)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Improvement Opportunities:", ln=True)
                for opp in analysis.improvement_opportunities[:4]:
                    pdf.bullet_point(opp)

            pdf.ln(10)

    # Design Recommendations
    if report.recommendations:
        pdf.add_page()
        pdf.section_header("Design Recommendations")

        for i, rec in enumerate(report.recommendations, 1):
            pdf.subsection_header(f"{i}. {rec.category.title()}")
            pdf.priority_badge(rec.priority)
            pdf.ln(8)

            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, "Current State:", ln=True)
            pdf.body_text(rec.current_state)

            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, "Recommendation:", ln=True)
            pdf.body_text(rec.recommendation)

            if rec.estimated_cost:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Estimated Cost:", ln=True)
                pdf.set_font("helvetica", "", 10)
                pdf.multi_cell(0, 5, sanitize_text(rec.estimated_cost))

            if rec.product_suggestions:
                pdf.ln(2)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Suggested Products:", ln=True)
                for product in rec.product_suggestions[:4]:
                    pdf.bullet_point(product)

            pdf.ln(8)

    # Generated Visualizations
    if report.generated_images:
        pdf.add_page()
        pdf.section_header("AI-Generated Visualizations")

        for gen_img in report.generated_images:
            if gen_img.path.exists():
                pdf.subsection_header(sanitize_text(gen_img.description))
                pdf.add_image_safe(gen_img.path, width=150)
                pdf.set_font("helvetica", "I", 8)
                pdf.set_text_color(100, 100, 100)
                pdf.multi_cell(0, 4, sanitize_text(f"Prompt: {gen_img.prompt_used[:200]}..."))
                pdf.set_text_color(0, 0, 0)
                pdf.ln(10)

    # Save PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
