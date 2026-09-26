"""Data contracts for iris normalization and its outputs."""

from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class NormalizedImage:
    data: np.ndarray
    source_path: str | None = None

    @property
    def pixels(self) -> np.ndarray:
        return self.data

    @property
    def array(self) -> np.ndarray:
        return self.data

    @property
    def width(self) -> int:
        return int(self.data.shape[1])

    @property
    def height(self) -> int:
        return int(self.data.shape[0])


@dataclass(frozen=True)
class ValidityMask:
    data: np.ndarray

    @property
    def pixels(self) -> np.ndarray:
        return self.data

    @property
    def array(self) -> np.ndarray:
        return self.data

    @property
    def mask(self) -> np.ndarray:
        return self.data


@dataclass(frozen=True)
class DatasetDirectoryDestination:
    image_directory: str
    mask_directory: str | None = None


@dataclass(frozen=True)
class SingleImageDestination:
    image_path: str
    mask_path: str | None = None


NormalizationDestination = DatasetDirectoryDestination | SingleImageDestination


@dataclass(frozen=True)
class NormalizationAnomaly:
    subject_id: str
    eye: str
    image_path: str
    issue: str


@dataclass(frozen=True)
class NormalizedResult:
    image: NormalizedImage
    mask: ValidityMask
    relative_image_path: str


@dataclass(frozen=True)
class SavedNormalizationPaths:
    image_path: str | None
    mask_path: str | None


@dataclass
class NormalizationBatch:
    processed_count: int
    successful_count: int
    failed_count: int
    anomalies: list[NormalizationAnomaly]
    results: list[NormalizedResult] | None = None
