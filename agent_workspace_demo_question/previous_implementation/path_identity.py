"""Shared conversion from image paths to subject and eye identifiers."""

from pathlib import Path


def identity_from_path(path: str) -> tuple[str, str]:
    """Return the subject and eye encoded by an image path."""
    image_path = Path(path)
    if image_path.parent.name in {"L", "R"}:
        return image_path.parent.parent.name, image_path.parent.name
    return image_path.parent.name, ""
