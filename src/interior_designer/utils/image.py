"""Image utilities."""

import shutil
from pathlib import Path
from datetime import datetime


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
