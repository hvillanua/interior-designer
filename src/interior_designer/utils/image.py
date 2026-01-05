"""Image utilities."""

import shutil
from pathlib import Path
from datetime import datetime
from io import BytesIO

from PIL import Image


def resize_image_for_api(image_path: Path, max_size: int = 1024) -> bytes:
    """Resize image to fit within max_size while maintaining aspect ratio.

    Args:
        image_path: Path to image file
        max_size: Maximum dimension (width or height) in pixels

    Returns:
        JPEG bytes of resized image
    """
    with Image.open(image_path) as img:
        # Convert to RGB if necessary (handles RGBA, P mode, etc.)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Calculate new size maintaining aspect ratio
        width, height = img.size
        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()


def create_session_dir(base_dir: Path) -> Path:
    """Create a new session directory with timestamp."""
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = base_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "original").mkdir(exist_ok=True)
    (session_dir / "generated").mkdir(exist_ok=True)
    return session_dir


def save_uploaded_image(uploaded_file, session_dir: Path) -> Path:
    """Save an uploaded image to the session directory.

    Args:
        uploaded_file: Streamlit UploadedFile object
        session_dir: Path to session directory

    Returns:
        Path to the saved image
    """
    original_dir = session_dir / "original"
    original_dir.mkdir(exist_ok=True)

    # Save the file
    file_path = original_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    return file_path


def get_image_path(session_dir: Path, filename: str) -> Path:
    """Get path to an image in the session directory."""
    return session_dir / "original" / filename


def copy_image(src: Path, dst_dir: Path) -> Path:
    """Copy an image to a directory."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return dst
