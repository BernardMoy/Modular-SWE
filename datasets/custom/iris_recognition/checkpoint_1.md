# Part 1: Data Discovery

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building a dataset access layer that will be used later.

## Command

```
iris scan <dataset_root> [--output dataset.csv] [--anomalies anomalies.csv]
iris inspect <subject_id>
```

## The data

The CASIA-Iris-Interval dataset follows this structure:

```
<dataset_root>/
├── 001/
│   ├── L/
│   │   ├── S1001L01.jpg
│   │   ├── S1001L02.jpg
│   │   └── ...
│   ├── R/
│   │   ├── S1001R01.jpg
│   │   ├── S1001R02.jpg
│   │   └── ...
```

- Not every subject has both L and R eye images.
- Subject names should be treated as a string ID instead of an integer.

## Requirements

### `scan` command

- This command should identify the L/ and R/ folders under each subject. It should always print a summary in the following human-readable format (numbers are arbitrary):

```
Dataset root: /data/CASIA-iris-interval

Subjects found: 250
- Both eyes present: 200
- Left eyes only: 10
- Right eyes only: 40
- Neither eye present: 0

Total valid images:
- Left: 700
- Right: 720

Anomalies found: 3
```

- If the `--output` path is present, a dataset csv file should be written to the output_path following the format below. Ignore files that are not of image format.
  | column | description |
  |------------|-----------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R" |
  | image_path | path to the iris image relative to the dataset root |
  | width | image width in pixels |
  | height | image height in pixels |
  | format | format of the image, e.g. "JPEG" |
  | file_size | file size of the image in bytes |

- If the `--anomalies` path is present, anomalies csv file should be written to the anomalies_path following the format below.
  | column | description |
  |------------|--------------------------------------------------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R". Not present if the issue is "missing_both_eyes". |
  | image_path | path to the iris image relative to the dataset root. Not present if the issue is "missing_both_eyes". |
  | issue | Either: "corrupted_image", "invalid_format", "zero_dimension_image", "missing_both_eyes" |

Anomalies are explained below:

- corrupted_image: The image is corrupted and cannot be viewed.
- invalid_format: The image is not in one of the following formats: .jpg, .jpeg, .png
- zero_dimension_image: The image has width and height both equal to zero.
- missing_both_eyes: The subject is missing both the L/ and R/ folders, or the folders are present but both are empty.

### `inspect` command

- This command inspect the data available for a particular subject id. It should print a summary in the following format:

```
Subject: 001

Left eye:
Images: 3
- S1001L01.jpg
- S1001L02.jpg
- S1001L03.jpg

Right eye:
Images: 4
- S1001R01.jpg
- S1001R02.jpg
- S1001R03.jpg
- S1001R04.jpg
```

- If the subject id is not present, print "Subject <subject_id> is not present."
- If an eye is not present (either the folder does not exist or the folder is empty), return in that part "absent". For example if the right eye is absent, return in the following format:

```
Subject: 001

Left eye:
Images: 3
- S1001L01.jpg
- S1001L02.jpg
- S1001L03.jpg

Right eye:
absent
```

## Tech stack

Implement your solution using Python.
