"""Filesystem traversal for the iris dataset."""

from pathlib import Path

from dataset_models import AnomalyRecord, ImageRecord, ScanResult, SubjectSummary
from image_metadata import SUPPORTED_SUFFIXES, read_metadata

# Files with these suffixes are image candidates even when unsupported by the
# project. Other files (metadata and operating-system artifacts) are ignored.
IMAGE_LIKE_SUFFIXES = SUPPORTED_SUFFIXES | {
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
    ".webp",
    ".avif",
    ".ico",
    ".ppm",
    ".pgm",
}


def _scan_subject(
    root: Path, subject_path: Path
) -> tuple[SubjectSummary, list[AnomalyRecord]]:
    subject_id = subject_path.name
    eye_records: dict[str, list[ImageRecord]] = {"L": [], "R": []}
    anomalies: list[AnomalyRecord] = []

    for eye in ("L", "R"):
        records, eye_anomalies = _scan_eye(root, subject_path, subject_id, eye)
        eye_records[eye].extend(records)
        anomalies.extend(eye_anomalies)

    return SubjectSummary(subject_id, eye_records["L"], eye_records["R"]), anomalies


def _collect_image_files(eye_path: Path) -> list[Path]:
    """Return sorted image-like files from an eye directory."""
    if not eye_path.is_dir():
        return []
    try:
        return sorted(
            (
                entry
                for entry in eye_path.iterdir()
                if entry.is_file() and entry.suffix.lower() in IMAGE_LIKE_SUFFIXES
            ),
            key=lambda path: path.name,
        )
    except OSError:
        return []


def _convert_image_entry(
    root: Path, entry: Path, subject_id: str, eye: str
) -> ImageRecord | AnomalyRecord:
    """Convert an image-like file into a valid record or an anomaly."""
    metadata = read_metadata(str(entry))
    relative = entry.relative_to(root).as_posix()
    if not metadata.is_valid:
        return AnomalyRecord(
            subject_id, eye, relative, metadata.issue or "corrupted_image"
        )
    return ImageRecord(
        subject_id,
        eye,
        relative,
        metadata.width or 0,
        metadata.height or 0,
        metadata.format or "",
        metadata.file_size,
    )


def _scan_eye(
    root: Path, subject_path: Path, subject_id: str, eye: str
) -> tuple[list[ImageRecord], list[AnomalyRecord]]:
    """Collect valid image records and anomalies for one subject eye."""
    records: list[ImageRecord] = []
    anomalies: list[AnomalyRecord] = []
    for entry in _collect_image_files(subject_path / eye):
        result = _convert_image_entry(root, entry, subject_id, eye)
        if isinstance(result, ImageRecord):
            records.append(result)
        else:
            anomalies.append(result)
    return records, anomalies


def scan_dataset(dataset_root: str) -> ScanResult:
    root = Path(dataset_root)
    subjects: list[SubjectSummary] = []
    images: list[ImageRecord] = []
    anomalies: list[AnomalyRecord] = []
    entries = sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)
    for subject_path in entries:
        subject, subject_anomalies = _scan_subject(root, subject_path)
        if not subject.left_images and not subject.right_images:
            anomalies.append(
                AnomalyRecord(subject.subject_id, None, None, "missing_both_eyes")
            )
        subjects.append(subject)
        images.extend(subject.left_images)
        images.extend(subject.right_images)
        anomalies.extend(subject_anomalies)
    return ScanResult(str(root), subjects, images, anomalies)


def inspect_subject(dataset_root: str, subject_id: str) -> SubjectSummary | None:
    root = Path(dataset_root)
    subject_path = root / subject_id
    if not subject_path.is_dir():
        return None
    subject, _ = _scan_subject(root, subject_path)
    return subject
