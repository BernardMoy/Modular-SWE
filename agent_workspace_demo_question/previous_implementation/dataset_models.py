"""Data contracts returned by dataset scanning workflows."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageRecord:
    subject_id: str
    eye: str
    image_path: str
    width: int
    height: int
    format: str
    file_size: int


@dataclass(frozen=True)
class AnomalyRecord:
    subject_id: str
    eye: str | None
    image_path: str | None
    issue: str


@dataclass
class SubjectSummary:
    subject_id: str
    left_images: list[ImageRecord]
    right_images: list[ImageRecord]


@dataclass
class ScanResult:
    dataset_root: str
    subjects: list[SubjectSummary]
    images: list[ImageRecord]
    anomalies: list[AnomalyRecord]
