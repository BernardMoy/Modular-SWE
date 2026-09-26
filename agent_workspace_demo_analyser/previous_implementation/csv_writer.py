"""CSV persistence for scanner results."""

import csv

from dataset_models import AnomalyRecord, ImageRecord
from dataset_schema import DATASET_FIELDS

ANOMALY_FIELDS = ["subject_id", "eye", "image_path", "issue"]


def write_dataset_csv(records: list[ImageRecord], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=DATASET_FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: getattr(record, field) for field in DATASET_FIELDS}
            for record in records
        )


def write_anomalies_csv(anomalies: list[AnomalyRecord], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=ANOMALY_FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: getattr(anomaly, field) or "" for field in ANOMALY_FIELDS}
            for anomaly in anomalies
        )
