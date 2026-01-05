"""Claude Code subprocess wrapper for LLM interactions."""

import json
import subprocess
import re
from pathlib import Path

from ..config import get_settings
from ..models.schemas import RoomAnalysis, DesignRecommendation
from ..prompts import ROOM_ANALYSIS_PROMPT, DESIGN_RECOMMENDATIONS_PROMPT, SUMMARY_PROMPT


class ClaudeCodeService:
    """Service for interacting with Claude via Claude Code CLI."""

    def __init__(self):
        self.settings = get_settings()

    def _run_claude(self, prompt: str) -> str:
        """Run Claude Code with a prompt and return the response."""
        cmd = [
            "claude",
            "-p", prompt,
            "--model", self.settings.claude_model,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for image analysis
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude Code timed out after 5 minutes")

        # Check for errors - claude may return 0 but have errors in output
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            error_msg = stderr or output or "Unknown error"
            raise RuntimeError(f"Claude Code failed (exit {result.returncode}): {error_msg}")

        # Check for API errors in output
        if "API Error:" in output or "Error:" in output:
            raise RuntimeError(f"Claude Code API error: {output}")

        return output

    def _extract_json(self, text: str) -> str:
        """Extract JSON from Claude's response."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            return json_match.group(1).strip()

        # Try to find raw JSON (array or object)
        json_match = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", text)
        if json_match:
            return json_match.group(1).strip()

        return text

    def analyze_room(
        self,
        image_path: Path,
        style: str | None = None,
        budget: str | None = None,
        specific_needs: str | None = None,
    ) -> RoomAnalysis:
        """Analyze a room image and return structured analysis."""
        prompt = f"""Read the image file at {image_path} and analyze it.

{ROOM_ANALYSIS_PROMPT.format(
    style=style or "not specified",
    budget=budget or "not specified",
    specific_needs=specific_needs or "not specified",
)}

Important: Return ONLY the JSON object, no additional text."""

        response = self._run_claude(prompt)
        json_str = self._extract_json(response)

        try:
            data = json.loads(json_str)
            return RoomAnalysis.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            raise ValueError(f"Failed to parse room analysis: {e}\nResponse: {response}")

    def generate_recommendations(
        self,
        room_analysis: RoomAnalysis,
        style: str | None = None,
        budget: str | None = None,
        specific_needs: str | None = None,
    ) -> list[DesignRecommendation]:
        """Generate design recommendations based on room analysis."""
        prompt = DESIGN_RECOMMENDATIONS_PROMPT.format(
            room_analysis=room_analysis.model_dump_json(indent=2),
            style=style or "not specified",
            budget=budget or "not specified",
            specific_needs=specific_needs or "not specified",
        )

        prompt += "\n\nImportant: Return ONLY the JSON array, no additional text."

        response = self._run_claude(prompt)
        json_str = self._extract_json(response)

        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "recommendations" in data:
                data = data["recommendations"]
            return [DesignRecommendation.model_validate(r) for r in data]
        except (json.JSONDecodeError, Exception) as e:
            raise ValueError(f"Failed to parse recommendations: {e}\nResponse: {response}")

    def generate_summary(
        self,
        room_analysis: RoomAnalysis,
        recommendations: list[DesignRecommendation],
        style: str | None = None,
        budget: str | None = None,
        specific_needs: str | None = None,
    ) -> str:
        """Generate an executive summary of the design plan."""
        recs_json = json.dumps([r.model_dump() for r in recommendations], indent=2)

        prompt = SUMMARY_PROMPT.format(
            room_analysis=room_analysis.model_dump_json(indent=2),
            recommendations=recs_json,
            style=style or "not specified",
            budget=budget or "not specified",
            specific_needs=specific_needs or "not specified",
        )

        return self._run_claude(prompt)
