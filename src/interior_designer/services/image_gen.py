"""Image generation service using OpenRouter."""

import base64
from pathlib import Path

from openai import OpenAI

from ..config import get_settings
from ..models.schemas import GeneratedImage
from ..utils.image import resize_image_for_api


class ImageGenService:
    """Service for generating room visualizations using OpenRouter."""

    def __init__(self, model_override: str | None = None):
        self.settings = get_settings()
        self.model = model_override or self.settings.openrouter_image_model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.settings.openrouter_api_key.get_secret_value(),
        )

    def _encode_image(self, image_path: Path, max_size: int = 1024) -> str:
        """Encode and resize an image file to base64.

        Args:
            image_path: Path to image file
            max_size: Maximum dimension for resizing (default 1024px)

        Returns:
            Base64-encoded JPEG string
        """
        # Resize image to avoid API payload limits
        image_bytes = resize_image_for_api(image_path, max_size=max_size)
        return base64.b64encode(image_bytes).decode("utf-8")

    def generate_room_variation(
        self,
        original_image: Path,
        prompt: str,
        output_dir: Path,
        description: str = "Room visualization",
        index: int = 0,
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

        # Encode and resize the original image (always JPEG after resize)
        image_data = self._encode_image(original_image, max_size=512)

        # Create the prompt for image editing
        full_prompt = f"""Edit this room image according to the following instructions.
Keep the room structure, walls, windows, and floor exactly the same.
Only modify what is specifically requested:

{prompt}

Maintain photorealistic quality and natural lighting."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": full_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                            },
                        ],
                    }
                ],
                extra_body={"modalities": ["image", "text"]},
            )

            msg = response.choices[0].message

            # Extract image from response.images (OpenRouter format)
            if hasattr(msg, 'images') and msg.images:
                img = msg.images[0]
                url = img['image_url']['url']
                if url.startswith("data:"):
                    _, data = url.split(",", 1)
                    image_bytes = base64.b64decode(data)

                    output_path = output_dir / f"generated_{original_image.stem}_{index}.png"
                    output_path.write_bytes(image_bytes)
                    return GeneratedImage(
                        path=output_path,
                        prompt_used=prompt,
                        description=description,
                    )

            raise ValueError(
                f"No image in response. Model: {self.model}. "
                f"Content: {msg.content[:200] if msg.content else 'EMPTY'}"
            )

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {e}")

    def is_available(self) -> bool:
        """Check if the image generation service is configured and available."""
        api_key = self.settings.openrouter_api_key.get_secret_value()
        return bool(api_key and api_key != "sk-or-...")
