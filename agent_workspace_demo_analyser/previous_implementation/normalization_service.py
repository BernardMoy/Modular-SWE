"""Workflow orchestration for iris normalization."""

import csv
from pathlib import Path

from PIL import Image

from dataset_schema import SEGMENTATION_FIELDS
from iris_normalization import normalize
from normalization_csv_writer import write_anomalies_csv
from normalization_mask import build_mask
from normalization_models import (
    DatasetDirectoryDestination,
    NormalizationAnomaly,
    NormalizationBatch,
    NormalizationDestination,
    NormalizedResult,
)
from normalization_writer import write_result
from path_identity import identity_from_path
from segmentation_models import Boundary, SegmentationRecord


def _source_path(csv_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    return csv_path.parent / candidate


def _record(row: dict[str, str]) -> SegmentationRecord:
    def number(name: str) -> float:
        return float(row[name])

    return SegmentationRecord(
        row["subject_id"],
        row["eye"],
        row["image_path"],
        Boundary(number("pupil_x"), number("pupil_y"), number("pupil_radius")),
        Boundary(number("iris_x"), number("iris_y"), number("iris_radius")),
    )


def _valid_geometry(pupil: Boundary, iris: Boundary) -> bool:
    values = (
        pupil.center_x,
        pupil.center_y,
        pupil.radius,
        iris.center_x,
        iris.center_y,
        iris.radius,
    )
    return (
        all(float(value) == float(value) for value in values)
        and pupil.radius > 0
        and iris.radius > 0
        and pupil.radius <= iris.radius
    )


def _normalize_image(
    image_path: str,
    record: SegmentationRecord,
    relative_image_path: str,
) -> NormalizedResult | NormalizationAnomaly:
    image_opened = False
    try:
        with Image.open(image_path) as image:
            image_opened = True
            if not _valid_geometry(record.pupil, record.iris):
                raise ValueError("invalid geometry")
            normalized = normalize(image, record)
            mask = build_mask(image, record, normalized)
            return NormalizedResult(normalized, mask, relative_image_path)
    except (OSError, SyntaxError, ValueError, TypeError, OverflowError):
        issue = "failed_normalization" if image_opened else "image_load_failed"
        return NormalizationAnomaly(
            record.subject_id, record.eye, relative_image_path, issue
        )


def normalize_one(
    image_path: str,
    pupil: Boundary,
    iris: Boundary,
    destination: NormalizationDestination,
) -> NormalizedResult | NormalizationAnomaly:
    subject_id, eye = identity_from_path(image_path)
    relative = image_path
    record = SegmentationRecord(subject_id, eye, relative, pupil, iris)
    result = _normalize_image(image_path, record, relative)
    if isinstance(result, NormalizedResult):
        write_result(result, destination)
    return result


def normalize_dataset(
    segmentation_csv_path: str,
    destination: NormalizationDestination,
    anomalies_path: str | None = None,
) -> NormalizationBatch:
    if not isinstance(destination, DatasetDirectoryDestination):
        raise ValueError(
            "dataset normalization requires a dataset_directory destination"
        )
    records: list[NormalizedResult] = []
    anomalies: list[NormalizationAnomaly] = []
    csv_path = Path(segmentation_csv_path)
    with csv_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != SEGMENTATION_FIELDS:
            raise ValueError(
                "Segmentation CSV header does not match the required format exactly"
            )
        for row in reader:
            relative = row["image_path"]
            try:
                record = _record(row)
                image_path = _source_path(csv_path, relative)
                result = _normalize_image(str(image_path), record, relative)
                if isinstance(result, NormalizedResult):
                    write_result(result, destination)
                    records.append(result)
                else:
                    anomalies.append(result)
            except (OSError, SyntaxError):
                subject, eye = row.get("subject_id", ""), row.get("eye", "")
                anomalies.append(
                    NormalizationAnomaly(subject, eye, relative, "image_load_failed")
                )
            except (KeyError, ValueError, TypeError, OverflowError):
                subject, eye = row.get("subject_id", ""), row.get("eye", "")
                anomalies.append(
                    NormalizationAnomaly(subject, eye, relative, "failed_normalization")
                )
    if anomalies_path:
        write_anomalies_csv(anomalies, anomalies_path)
    return NormalizationBatch(
        processed_count=len(records) + len(anomalies),
        successful_count=len(records),
        failed_count=len(anomalies),
        anomalies=anomalies,
        results=records,
    )
