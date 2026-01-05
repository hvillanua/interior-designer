"""Image generation service using OpenRouter."""

import base64
import httpx
from pathlib import Path

from openai import OpenAI

from ..config import get_settings
from ..models.schemas import GeneratedImage


class ImageGenService:
    """Service for generating room visualizations using OpenRouter."""

    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            base_url=self.settings.openrouter_base_url,
            api_key=self.settings.openrouter_api_key.get_secret_value(),
            default_headers={
                "HTTP-Referer": "https://interior-designer.local",
                "X-Title": "Interior Designer AI",
            },
        )

    def _encode_image(self, image_path: Path) -> str:
        """Encode an image file to base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_image_mime_type(self, image_path: Path) -> str:
        """Get MIME type for an image file."""
        suffix = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return mime_types.get(suffix, "image/jpeg")

    def _extract_image_from_response(self, response) -> bytes | None:
        """Extract image bytes from OpenRouter response."""
        for choice in response.choices:
            message = choice.message

            # Check for images array (OpenRouter format)
            if hasattr(message, "images") and message.images:
                for img in message.images:
                    if hasattr(img, "image_url"):
                        url = img.image_url.get("url", "") if isinstance(img.image_url, dict) else str(img.image_url)
                        if url.startswith("data:"):
                            _, data = url.split(",", 1)
                            return base64.b64decode(data)

            # Check content array
            if hasattr(message, "content"):
                content = message.content
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            # Check for image_url type
                            if item.get("type") == "image_url":
                                url = item.get("image_url", {}).get("url", "")
                                if url.startswith("data:"):
                                    _, data = url.split(",", 1)
                                    return base64.b64decode(data)
                            # Check for b64_json type
                            if item.get("type") == "image" and "b64_json" in item:
                                return base64.b64decode(item["b64_json"])

        return None

    def generate_room_variation(
        self,
        original_image: Path,
        prompt: str,
        output_dir: Path,
        description: str = "Room visualization",
    ) -> GeneratedImage:
        """Generate a room variation based on the original image and prompt.

        Args:
            original_image: Path to the original room image
            prompt: The edit instruction for the image
            output_dir: Directory to save the generated image
            description: Description of the generated image

        Returns:
            GeneratedImage with path to the generated image
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Encode the original image
        image_data = self._encode_image(original_image)
        mime_type = self._get_image_mime_type(original_image)

        # Create the prompt for image editing
        full_prompt = f"""Edit this room image according to the following instructions.
Keep the room structure, walls, windows, and floor exactly the same.
Only modify what is specifically requested:

{prompt}

Maintain photorealistic quality and natural lighting."""

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openrouter_image_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": full_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                },
                            },
                        ],
                    }
                ],
                extra_body={"modalities": ["image", "text"]},
            )

            # Extract image from response
            image_bytes = self._extract_image_from_response(response)

            if image_bytes:
                output_path = output_dir / f"generated_{original_image.stem}.png"
                output_path.write_bytes(image_bytes)
                return GeneratedImage(
                    path=output_path,
                    prompt_used=prompt,
                    description=description,
                )

            # Log response for debugging
            import json
            response_data = {
                "model": response.model,
                "choices": [
                    {
                        "message": {
                            "content": str(c.message.content) if c.message else None,
                            "role": c.message.role if c.message else None,
                        }
                    }
                    for c in response.choices
                ],
            }
            raise ValueError(
                f"Could not extract image from response. "
                f"Model: {self.settings.openrouter_image_model}. "
                f"Response structure: {json.dumps(response_data, indent=2)[:500]}"
            )

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {e}")

    def is_available(self) -> bool:
        """Check if the image generation service is configured and available."""
        api_key = self.settings.openrouter_api_key.get_secret_value()
        return bool(api_key and api_key != "sk-or-...")
