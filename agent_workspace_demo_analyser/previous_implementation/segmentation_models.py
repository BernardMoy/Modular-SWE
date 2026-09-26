"""Data contracts used by the segmentation layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Boundary:
    center_x: float
    center_y: float
    radius: float


@dataclass(frozen=True)
class SegmentationResult:
    pupil: Boundary
    iris: Boundary
    success: bool


@dataclass(frozen=True)
class ValidationStatus:
    valid: bool
    issue: str | None = None


@dataclass(frozen=True)
class SegmentationRecord:
    subject_id: str
    eye: str
    image_path: str
    pupil: Boundary
    iris: Boundary


@dataclass(frozen=True)
class SegmentationAnomaly:
    subject_id: str
    eye: str
    image_path: str
    issue: str


@dataclass
class SegmentationBatch:
    results: list[SegmentationRecord]
    anomalies: list[SegmentationAnomaly]
    processed_count: int
    successful_count: int

    @property
    def records(self) -> list[SegmentationRecord]:
        return self.results
