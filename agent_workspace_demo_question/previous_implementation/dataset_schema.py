"""Shared CSV field contracts for dataset workflows."""

DATASET_FIELDS = (
    "subject_id",
    "eye",
    "image_path",
    "width",
    "height",
    "format",
    "file_size",
)

SEGMENTATION_FIELDS = (
    "subject_id",
    "eye",
    "image_path",
    "pupil_x",
    "pupil_y",
    "pupil_radius",
    "iris_x",
    "iris_y",
    "iris_radius",
)
