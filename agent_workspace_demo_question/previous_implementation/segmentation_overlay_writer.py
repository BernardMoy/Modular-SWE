"""Draw segmentation boundaries on source images."""

from pathlib import Path
from PIL import Image, ImageDraw
from segmentation_models import SegmentationRecord


def _render(record: SegmentationRecord, source_path: str, destination: Path) -> None:
    source = Path(source_path)
    with Image.open(source) as image:
        canvas = image.convert("RGB")
        draw = ImageDraw.Draw(canvas)
        for boundary, color in (
            (record.pupil, (255, 40, 40)),
            (record.iris, (40, 255, 40)),
        ):
            box = (
                boundary.center_x - boundary.radius,
                boundary.center_y - boundary.radius,
                boundary.center_x + boundary.radius,
                boundary.center_y + boundary.radius,
            )
            draw.ellipse(
                box, outline=color, width=max(1, round(min(canvas.size) / 300))
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(destination)


def write_overlay(
    record: SegmentationRecord, overlay_directory: str, source_path: str | None = None
) -> None:
    """Write an overlay while preserving the record's relative image path.

    ``source_path`` lets callers resolve dataset-relative paths explicitly;
    the fallback preserves compatibility for callers with an already-resolved
    record path.
    """
    _render(
        record,
        source_path or record.image_path,
        Path(overlay_directory) / Path(record.image_path),
    )


def write_overlay_to_path(record: SegmentationRecord, output_path: str) -> None:
    """Write one overlay to an explicitly named output file."""
    _render(record, record.image_path, Path(output_path))
