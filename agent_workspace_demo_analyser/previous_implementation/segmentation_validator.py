"""Validation of detected circle geometry."""

import math
from segmentation_models import SegmentationResult, ValidationStatus

ALLOWED_ISSUES = (
    "segmentation_failed",
    "zero_radius",
    "pupil_out_of_bounds",
    "iris_out_of_bounds",
    "pupil_larger_than_iris",
)


def validate(
    segmentation_result: SegmentationResult, image_size: tuple[int, int]
) -> ValidationStatus:
    if not segmentation_result.success:
        return ValidationStatus(False, "segmentation_failed")
    width, height = image_size
    pupil, iris = segmentation_result.pupil, segmentation_result.iris
    values = (
        pupil.center_x,
        pupil.center_y,
        pupil.radius,
        iris.center_x,
        iris.center_y,
        iris.radius,
    )
    if (
        any(not math.isfinite(float(v)) for v in values)
        or pupil.radius <= 0
        or iris.radius <= 0
    ):
        return ValidationStatus(False, "zero_radius")

    def outside(circle):
        return (
            circle.center_x - circle.radius < 0
            or circle.center_y - circle.radius < 0
            or circle.center_x + circle.radius > width
            or circle.center_y + circle.radius > height
        )

    if outside(pupil):
        return ValidationStatus(False, "pupil_out_of_bounds")
    if outside(iris):
        return ValidationStatus(False, "iris_out_of_bounds")
    if pupil.radius > iris.radius:
        return ValidationStatus(False, "pupil_larger_than_iris")
    return ValidationStatus(True)
