"""Persistence for normalization anomalies."""

import csv
from pathlib import Path

from normalization_models import NormalizationAnomaly

ANOMALY_FIELDS = ["subject_id", "eye", "image_path", "issue"]
ALLOWED_ISSUES = {"failed_normalization", "image_load_failed"}


def write_anomalies_csv(
    anomalies: list[NormalizationAnomaly], output_path: str
) -> None:
    if any(anomaly.issue not in ALLOWED_ISSUES for anomaly in anomalies):
        raise ValueError("normalization anomalies must use an allowed issue")
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=ANOMALY_FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: getattr(anomaly, field) for field in ANOMALY_FIELDS}
            for anomaly in anomalies
        )
