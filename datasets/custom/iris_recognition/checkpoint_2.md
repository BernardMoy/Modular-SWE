# Part 2: Pupil and Iris Localization

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building a segmentation layer that locates the pupil and iris in an image.

## Dataset csv format

| column     | description                                         |
| ---------- | --------------------------------------------------- |
| subject_id | the subject name / subfolder name                   |
| eye        | "L" or "R"                                          |
| image_path | path to the iris image relative to the dataset root |
| width      | image width in pixels                               |
| height     | image height in pixels                              |
| format     | format of the image, e.g. "JPEG"                    |
| file_size  | file size of the image in bytes                     |

## Command

```
iris segment <dataset_csv> [--output segmentation.csv] [--overlay overlay/] [--anomalies anomalies.csv]
iris segment-one <image_path> [--output output.png]
```

## Requirements

## Iris localization rules

- Each iris image consists of two boundaries: The pupil boundary (between the pupil and iris) and the iris boundary (between the iris and sclera). They are not concentric.
- The two boundaries are estimated independently as (center_x, center_y, radius).
- Iris localization must be done using a classical deterministic, not learned algorithm. Examples of allowed algorithms are circular hough transform, Daugman's integrodifferential operator. Examples of algorithms not permitted are pre-trained CNN models or libraries that requires training.

## `segment` command

- This command should accept a dataset csv in the above format specified. An error should be thrown if the csv format does not match exactly.
- It should always print a summary in the form of:

```
Dataset: dataset.csv

Image processed: 1000
Successful segmentation: 600
Failed segmentation: 400

Anomalies found: 5
```

- If the `--output` path is present, write a segmentation csv in the following format:
  | column | description |
  |--------------|-----------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R" |
  | image_path | path to the iris image relative to the dataset root |
  | pupil_x | x-coordinate of the pupil center |
  | pupil_y | y-coordinate of the pupil center |
  | pupil_radius | radius of the pupil |
  | iris_x | x-coordinate of the iris center |
  | iris_y | y-coordinate of the iris center |
  | iris_radius | radius of the iris |

- If the `--overlay` folder path is present, write to it following the dataset's image folder structure, showing overlay images for each successful segmentation. Each overlay is the original image with the detected pupil circle and iris circle in two distinct colors.

- If the `--anomalies` path is present, anomalies csv file should be writtrn to the anomalies path in the following format:
  | column | description |
  |--------------|-----------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R" |
  | image_path | path to the iris image relative to the dataset root |
  | issue | Either: "segmentation_failed", "zero_radius", "pupil_out_of_bounds", "iris_out_of_bounds", "pupil_larger_than_iris" |

## `segment-one` command

- This command should accept an image path, and if the output path is present, write to the output path the image overlay of the detected pupil and iris.
- The overlay should follow the same rule as the `segment` command.

- Always print a summary in the following format for success and fail respectively:

```
Image: data/CASIA-iris-interval/001/L/S1001L01.jpg

Pupil: center=(160, 142), radius=42
Iris: center=(158, 140), radius=110

Status: success
```

```
Image: data/CASIA-iris-interval/001/L/S1001L01.jpg

Status: failed
Reason: [Either: "segmentation_failed", "zero_radius", "pupil_out_of_bounds", "iris_out_of_bounds", "pupil_larger_than_iris"]
```

## Tech stack

Implement your solution using Python.
