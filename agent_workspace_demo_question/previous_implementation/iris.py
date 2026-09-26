"""CLI entrypoint for scanning, segmentation, and normalization workflows."""

import argparse
from dataclasses import dataclass
from csv_writer import write_anomalies_csv, write_dataset_csv
from dataset_scanner import inspect_subject, scan_dataset
from segmentation_service import segment_dataset, segment_image
from normalization_models import (
    DatasetDirectoryDestination,
    SingleImageDestination,
)
from normalization_service import normalize_dataset, normalize_one
from segmentation_models import Boundary, SegmentationRecord


@dataclass(frozen=True)
class ScanOptions:
    dataset_root: str
    output_path: str | None = None
    anomalies_path: str | None = None


def _print_scan(options: ScanOptions) -> None:
    result = scan_dataset(options.dataset_root)
    both = sum(bool(s.left_images and s.right_images) for s in result.subjects)
    left_only = sum(bool(s.left_images and not s.right_images) for s in result.subjects)
    right_only = sum(
        bool(s.right_images and not s.left_images) for s in result.subjects
    )
    neither = sum(not s.left_images and not s.right_images for s in result.subjects)
    left_count = sum(len(s.left_images) for s in result.subjects)
    right_count = sum(len(s.right_images) for s in result.subjects)
    print(
        f"Dataset root: {options.dataset_root}\n\nSubjects found: {len(result.subjects)}\n- Both eyes present: {both}\n- Left eyes only: {left_only}\n- Right eyes only: {right_only}\n- Neither eye present: {neither}\n\nTotal valid images:\n- Left: {left_count}\n- Right: {right_count}\n\nAnomalies found: {len(result.anomalies)}"
    )
    if options.output_path:
        write_dataset_csv(result.images, options.output_path)
    if options.anomalies_path:
        write_anomalies_csv(result.anomalies, options.anomalies_path)


def _print_eye(label: str, records: list) -> None:
    print(f"{label} eye:")
    if not records:
        print("absent")
        return
    print(f"Images: {len(records)}")
    for record in records:
        print(f"- {record.image_path.rsplit('/', 1)[-1]}")


def _print_subject(dataset_root: str, subject_id: str) -> None:
    subject = inspect_subject(dataset_root, subject_id)
    if subject is None:
        print(f"Subject {subject_id} is not present.")
        return
    print(f"Subject: {subject.subject_id}\n")
    _print_eye("Left", subject.left_images)
    print()
    _print_eye("Right", subject.right_images)


def _print_segment(
    csv_path: str, output: str | None, overlay: str | None, anomalies_path: str | None
) -> None:
    batch = segment_dataset(csv_path, output, overlay, anomalies_path)
    print(
        f"Dataset: {csv_path}\n\nImage processed: {batch.processed_count}\nSuccessful segmentation: {batch.successful_count}\nFailed segmentation: {len(batch.anomalies)}\n\nAnomalies found: {len(batch.anomalies)}"
    )


def _print_segment_one(path: str, output: str | None) -> None:
    result = segment_image(path, overlay_path=output)
    print(f"Image: {path}\n")
    if isinstance(result, SegmentationRecord):
        print(
            f"Pupil: center=({round(result.pupil.center_x)}, {round(result.pupil.center_y)}), radius={round(result.pupil.radius)}"
        )
        print(
            f"Iris: center=({round(result.iris.center_x)}, {round(result.iris.center_y)}), radius={round(result.iris.radius)}\n\nStatus: success"
        )
    else:
        print(f"Status: failed\nReason: {result.issue}")


def _parse_boundary(value: str) -> Boundary:
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("boundary must be x,y,r")
    try:
        return Boundary(float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("boundary must contain numeric x,y,r") from exc


def _print_normalize(
    csv_path: str,
    output_dir: str | None,
    masks_dir: str | None,
    anomalies_path: str | None,
) -> None:
    destination = DatasetDirectoryDestination(output_dir or "normalized", masks_dir)
    batch = normalize_dataset(csv_path, destination, anomalies_path)
    print(
        f"Segmentation data: {csv_path}\n\nImage processed: {batch.processed_count}\nSuccessful normalization: {batch.successful_count}\nFailed normalization: {batch.failed_count}\n\nAnomalies found: {len(batch.anomalies)}"
    )


def _print_normalize_one(
    path: str,
    pupil: Boundary,
    iris: Boundary,
    output: str | None,
    output_mask: str | None,
) -> None:
    destination = SingleImageDestination(output or "normalized.png", output_mask)
    result = normalize_one(path, pupil, iris, destination)
    print(f"Image: {path}\n")
    if hasattr(result, "image"):
        print(
            f"Pupil: center=({round(pupil.center_x)}, {round(pupil.center_y)}), radius={round(pupil.radius)}"
        )
        print(
            f"Iris: center=({round(iris.center_x)}, {round(iris.center_y)}), radius={round(iris.radius)}\n\nStatus: success"
        )
        print(f"Saved image to: {destination.image_path}")
        if destination.mask_path:
            print(f"Saved mask to: {destination.mask_path}")
    else:
        print(f"Status: failed\nReason: {result.issue}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="iris")
    subs = parser.add_subparsers(dest="command", required=True)
    scan = subs.add_parser("scan")
    scan.add_argument("dataset_root")
    scan.add_argument("--output")
    scan.add_argument("--anomalies")
    inspect = subs.add_parser("inspect")
    inspect.add_argument("subject_id")
    inspect.add_argument("--dataset-root", default="data/CASIA-Iris-Interval")
    segment = subs.add_parser("segment")
    segment.add_argument("dataset_csv")
    segment.add_argument("--output")
    segment.add_argument("--overlay")
    segment.add_argument("--anomalies")
    one = subs.add_parser("segment-one")
    one.add_argument("image_path")
    one.add_argument("--output")
    normalize = subs.add_parser("normalize")
    normalize.add_argument("segmentation_csv")
    normalize.add_argument("--output-dir")
    normalize.add_argument("--output-masks-dir", "--mask-dir", dest="masks_dir")
    normalize.add_argument("--anomalies")
    normalize_one_parser = subs.add_parser("normalize-one")
    normalize_one_parser.add_argument("image_path")
    normalize_one_parser.add_argument("--pupil", required=True, type=_parse_boundary)
    normalize_one_parser.add_argument("--iris", required=True, type=_parse_boundary)
    normalize_one_parser.add_argument("--output")
    normalize_one_parser.add_argument("--output-mask")
    args = parser.parse_args(argv)
    if args.command == "scan":
        _print_scan(ScanOptions(args.dataset_root, args.output, args.anomalies))
    elif args.command == "inspect":
        _print_subject(args.dataset_root, args.subject_id)
    elif args.command == "segment":
        _print_segment(args.dataset_csv, args.output, args.overlay, args.anomalies)
    elif args.command == "segment-one":
        _print_segment_one(args.image_path, args.output)
    elif args.command == "normalize":
        _print_normalize(
            args.segmentation_csv, args.output_dir, args.masks_dir, args.anomalies
        )
    else:
        _print_normalize_one(
            args.image_path, args.pupil, args.iris, args.output, args.output_mask
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
