# Part 5: Hamming Distance Comparison

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building an encoding layer that converts normalized image into iris code using 2D Gabor wavelet filters.

## Constants for the encoded and masks files

wavelength = 8.0
scales = 3
orientations = 4
grid_step = 8
height = 64
width = 512
max_shift = 8

## Normalized and masks directory format

The normalized and masks directory have the same format as the data/CASIA-Iris-Interval.
Each image is a 64 (Height, radial) \* 512 (Width, angular) png file of normalized iris.

## Command

```
iris match-one <encoded_a.bin> <mask_a.bin> <encoded_b.bin> <mask_b.bin> [--threshold 0.32]
```

## Requirements

- For each shift k in range (-max_shift, max_shift+1): circularly shift code B and mask B along the grid cols by k.
- A bit is only considered when it is valid in both images: `mask_a & mask_b`.
- Calculate the masked hamming distance.

### `match-one` command

- Given the encoded bin file (iriscode) and the mask bin file, compute the best hamming distance and valid bit count for each shift.
- A hamming distance less than or equal to threshold is considered a match.
- Print a summary in the following format for success and fail respectively.

```
Code A: codes/001/L/encoded.bin
Code B: codes/001/L/encoded.bin
Max shift: 8

Best shift: +2
Hamming distance: 0.081
Valid bit count: 10944/12288
Match: True

Status: success
```

```
Code A: codes/001/L/encoded.bin
Code B: codes/001/L/encoded.bin
Max shift: 8

Status: failed
Reason: [Either: "files_not_found", "code_load_failed", "mask_load_failed"]
```

## Tech stack

Implement your solution using Python.

## Entrypoint file

The CLI entrypoint file must be named `iris.py`.
