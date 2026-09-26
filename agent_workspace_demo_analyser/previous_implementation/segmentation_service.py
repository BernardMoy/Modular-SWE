"""Segmentation orchestration for CSV rows and individual images."""

import csv
from pathlib import Path
from PIL import Image
from iris_segmentation import localize
from dataset_schema import DATASET_FIELDS
from path_identity import identity_from_path
from segmentation_models import (
    SegmentationAnomaly,
    SegmentationBatch,
    SegmentationRecord,
    ValidationStatus,
)
from segmentation_validator import validate
from segmentation_csv_writer import write_anomalies_csv, write_segmentation_csv
from segmentation_overlay_writer import write_overlay, write_overlay_to_path


def _segment(
    path: str, subject: str, eye: str, relative: str
) -> SegmentationRecord | SegmentationAnomaly:
    try:
        with Image.open(path) as image:
            size = image.size
        result = localize(path)
        status = validate(result, size)
    except (OSError, ValueError, SyntaxError):
        status = ValidationStatus(False, "segmentation_failed")
        result = None
    if not status.valid:
        return SegmentationAnomaly(
            subject, eye, relative, status.issue or "segmentation_failed"
        )
    return SegmentationRecord(subject, eye, relative, result.pupil, result.iris)


def segment_image(
    image_path: str,
    output_path: str | None = None,
    overlay_path: str | None = None,
) -> SegmentationRecord | SegmentationAnomaly:
    subject, eye = identity_from_path(image_path)
    outcome = _segment(image_path, subject, eye, image_path)
    if isinstance(outcome, SegmentationRecord):
        if output_path:
            write_segmentation_csv([outcome], output_path)
        if overlay_path:
            write_overlay_to_path(outcome, overlay_path)
    elif output_path:
        write_anomalies_csv([outcome], output_path)
    return outcome


def segment_dataset(
    dataset_csv_path: str,
    output_path: str | None = None,
    overlay_directory: str | None = None,
    anomalies_path: str | None = None,
) -> SegmentationBatch:
    csv_path = Path(dataset_csv_path)
    with csv_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != DATASET_FIELDS:
            raise ValueError(
                "Dataset CSV header does not match the required format exactly"
            )
        records, anomalies = [], []
        for row in reader:
            relative = row["image_path"]
            source_path = Path(relative)
            if not source_path.is_absolute():
                source_path = csv_path.parent / source_path
            outcome = _segment(
                str(source_path), row["subject_id"], row["eye"], relative
            )
            (records if isinstance(outcome, SegmentationRecord) else anomalies).append(
                outcome
            )
    batch = SegmentationBatch(
        records, anomalies, len(records) + len(anomalies), len(records)
    )
    if output_path:
        write_segmentation_csv(batch.records, output_path)
    if anomalies_path:
        write_anomalies_csv(batch.anomalies, anomalies_path)
    if overlay_directory:
        for record in batch.records:
            source_path = csv_path.parent / record.image_path
            write_overlay(record, overlay_directory, str(source_path))
    return batch
