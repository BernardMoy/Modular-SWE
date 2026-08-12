# Part 6: User Identification

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building the final part of the application by identifying the subject from eye images.

## Encoded and encoded-masks directory format

The encoded and encoded-masks directories have the same format as the data/CASIA-Iris-Interval.
Each stores .bin files for the encoded iriscode and the encoded mask respectively.

## Command

```
iris identify <image> <encoded-dir> <encoded-masks-dir> [--threshold 0.32]
```

## Requirements

- For each (subject_id, eye) under the encoded and encoded-masks directories, call existing commands on the image to process it to encoded bin and mask bin files, and finally the `match-one` command to get the hamming distance, best_shift and valid_bit_count.
- The top ranked candidate is the identification result only when its hamming distance <= threshold: If the top ranked candidate does not meet this condition then there is no match.
- Print a summary in the following format for success and fail respectively:

```
Code: codes/001/L/encoded.bin

Closest subject: 001, L
Hamming distance: 0.081
Match: True

Status: success
```

```
Code: codes/001/L/encoded.bin

Status: fail
Reason: [Either: "files_not_found", "code_load_failed", "mask_load_failed"]
```

## Tech stack

Implement your solution using Python.

## Entrypoint file

The CLI entrypoint file must be named `iris.py`.
