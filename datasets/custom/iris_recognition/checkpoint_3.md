# Part 3: Iris Normalization

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building a normalization layer that unwraps the iris region bounded by 2 circles into a rectangular representation (Daugman's rubber sheet model).

## Segmentation csv format

| column       | description                                         |
| ------------ | --------------------------------------------------- |
| subject_id   | the subject name / subfolder name                   |
| eye          | "L" or "R"                                          |
| image_path   | path to the iris image relative to the dataset root |
| pupil_x      | x-coordinate of the pupil center                    |
| pupil_y      | y-coordinate of the pupil center                    |
| pupil_radius | radius of the pupil                                 |
| iris_x       | x-coordinate of the iris center                     |
| iris_y       | y-coordinate of the iris center                     |
| iris_radius  | radius of the iris                                  |

## Command

```
iris normalize <segmentation_csv> [--output-dir normalized/] [--mask-dir masks/] [--anomalies anomalies.csv]
iris normalize-one <image_path> --pupil <x,y,r> --iris <x,y,r> [--output output.png] [--output-mask mask.png]
```

## Requirements

### Rubber sheet model

- Each pixel is represented by r and theta. r=0 for the pupil boundary, r=1 for the iris boundary. theta is from 0 to 360 degrees.
- r is the height and theta is the width of the output image.
- The source pixel is calculated from the rectangular representation using bilinear interpolation:

```
pupil_edge_x = pupil_center_x + pupil_radius * cos(θ)
pupil_edge_y = pupil_center_y + pupil_radius * sin(θ)
iris_edge_x  = iris_center_x  + iris_radius  * cos(θ)
iris_edge_y  = iris_center_y  + iris_radius  * sin(θ)

source_x = (1 - r) * pupil_edge_x + r * iris_edge_x
source_y = (1 - r) * pupil_edge_y + r * iris_edge_y
```

### Output dimensions

- The default output size is 64 (Height, radial) \* 512 (Width, angular).

### Validity mask

For every normalized image, the system should also generate abinary validity mask as a png image:
255 = valid iris pixel, 0 = invalid pixel.

Invalid pixel includes when the source coordinate falls outside the source image.

### `normalize` command

- This command should accept a segmentation csv in the above format specified. An error should be thrown if the csv format does not match exactly.
- It should always print a summary in the form of:

```
Segmentation data: segmentation.csv

Image processed: 1000
Successful normalization: 600
Failed normalization: 400

Anomalies found: 5
```

- If the `--output-dir` folder path is present, write to it following the dataset's image folder structure and names, showing normalized png in the specified default output dimensions.
- If the `--mask-dir` folder path is present, write to it following dataset's image folder structure and names, showing the masks.
- If the `--anomalies` path is present, anomalies csv file should be writtrn to the anomalies path in the following format:
  | column | description |
  |--------------|-----------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R" |
  | image_path | path to the iris image relative to the dataset root |
  | issue | Either: "failed_normalization", "image_load_failed" |

### `normalize-one` command

- This command should accept an image path, pupil x,y,r and iris x,y,r, and if the output path is present, write to the output path the normalized png image in the default output dimensions. If the mask path is present then write the mask png to it.

- Always print a summary in the following format for success and fail respectively:

```
Image: data/CASIA-iris-interval/001/L/S1001L01.jpg

Pupil: center=(160, 142), radius=42
Iris: center=(158, 140), radius=110

Status: success
Saved image to: normalized.png
Saved mask to: mask.png
```

```
Image: data/CASIA-iris-interval/001/L/S1001L01.jpg

Status: failed
Reason: [Either: "failed_normalization", "image_load_failed"]
```
