"""CSV writers for segmentation outputs."""

import csv
from segmentation_models import SegmentationAnomaly, SegmentationRecord

SEGMENTATION_FIELDS = [
    "subject_id",
    "eye",
    "image_path",
    "pupil_x",
    "pupil_y",
    "pupil_radius",
    "iris_x",
    "iris_y",
    "iris_radius",
]
ANOMALY_FIELDS = ["subject_id", "eye", "image_path", "issue"]


def write_segmentation_csv(records: list[SegmentationRecord], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=SEGMENTATION_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    "subject_id": r.subject_id,
                    "eye": r.eye,
                    "image_path": r.image_path,
                    "pupil_x": r.pupil.center_x,
                    "pupil_y": r.pupil.center_y,
                    "pupil_radius": r.pupil.radius,
                    "iris_x": r.iris.center_x,
                    "iris_y": r.iris.center_y,
                    "iris_radius": r.iris.radius,
                }
            )


def write_anomalies_csv(anomalies: list[SegmentationAnomaly], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=ANOMALY_FIELDS)
        writer.writeheader()
        writer.writerows({f: getattr(a, f) for f in ANOMALY_FIELDS} for a in anomalies)
