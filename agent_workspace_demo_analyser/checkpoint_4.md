# Part 4: Feature Encoding

## Introduction

You will be building a CLI tool for recognition of the user from iris images.
Across the project you will be working with the CASIA-Iris-Interval dataset available under data/.
In this checkpoint you are building an encoding layer that converts normalized image into iris code using 2D Gabor wavelet filters.

## Normalized and masks directory format

The normalized and masks directory have the same format as the data/CASIA-Iris-Interval.
Each image is a 64 (Height, radial) \* 512 (Width, angular) png file of normalized iris.

## Command

```
iris encode <normalized_dir> <masks_dir> [--output-dir encoded/] [--output-masks-dir encoded-masks/] [--anomalies anomalies.csv]
iris encode-one <normalized_image_path> <mask_image_path> [--output code.bin] [--output-mask mask.bin]
```

## Requirements

### 2D Gabor Wavelet

The 2D Gabor Wavelet is defined as:

```
x' =  x * cos(θ) + y * sin(θ)
y' = -x * sin(θ) + y * cos(θ)

G(x, y) = exp( -(x'^2 + γ^2 * y'^2) / (2 * σ^2) ) * exp( i * 2π * x' / λ )
```

σ (sigma) is the Gaussian envelope's standard deviation, controlling the spatial extent of the filter
γ (gamma) is the spatial aspect ratio (commonly 0.5)
λ (lambda / --wavelength) is the wavelength of the sinusoidal carrier
θ (theta) is the filter's orientation

This produces a complex valued filter: convolving the normalized image with the filter at a given (θ, λ) produces a complex response at every pixel.

### Filter bank

A bank of filters is built by sweeping:
`scales` wavelengths, derived from the base --wavelength by doubling at each scale:
λ_s = wavelength \* 2^s for s = 0, 1, ..., scales - 1. With the defaults (wavelength=8.0, scales=3),
this gives λ = 8, 16, 32 pixels.

`orientations` evenly spaced angles from 0 to π: θ_o = o \* π / orientations for o = 0, 1, ..., orientations - 1.
With the default (orientations=4), this gives θ = 0°, 45°, 90°, 135°.

## Phase quantization

For the filter's complex response at each sampled location, quantize them into 2 bits:

| Re sign | Im sign | 2 bit code |
| ------- | ------- | ---------- |
| +       | +       | 00         |
| -       | +       | 01         |
| +       | -       | 10         |
| -       | -       | 11         |

## Sampling grid

Responses are sampled on a coarser grid spaced by `grid-step` (Default: 8) pixels in both the height and width directions instead of at every pixel:

```
grid_rows = floor(height / grid_step)
grid_cols = floor(width  / grid_step)
code_length = scales * orientations * grid_rows * grid_cols * 2
```

## Bit packing format

- Bits are packed 8 per byte, most significant bit first
- If the total number of bits is not a multiple of 8, the final byte is zero padded on the lower end

## Requirements

### `encode` command

- This command should accept a normalized image directory.
- For each image, apply the filter bank, sampling responses and quantize each into 2 bits, flattened into the iris code.\
- For each grid sampling location, look for the pixel value in the mask at that same coordinate space. If the pixel is 0, set both code bits to 0 in the mask. If the pixel is 255, set to 1.
- Always print a summary in the following format:

```
Normalized input: normalized/

Image processed: 1000
Successfully encoded: 600
Failed to encode: 400

Anomalies found: 5
```

- If the `--output-dir` folder path is present, write to it following the dataset's image folder structure, showing masked bin files in the same file names. Same for `--output-masks-dir`.

- If the `--anomalies` path is present, anomalies csv file should be writtrn to the anomalies path in the following format:
  | column | description |
  |--------------|-----------------------------------------------------|
  | subject_id | the subject name / subfolder name |
  | eye | "L" or "R" |
  | image_path | path to the iris image relative to the dataset root |
  | issue | Either: "failed_to_encode", "image_load_failed", "mask_load_failed" |

### `encode-one` command

- This command should accept a normalized image path, and if the output path is present, write to the output path the iris code bin file. Same for the mask.

- Always print a summary in the following format for success and fail respectively:

```
Image: normalized/001/L/S1001L01.png
Mask: masks/001_L_S1001L01.png
Status: success
Saved to: code.bin
Mask saved to: mask.bin
```

```
Image: normalized/001/L/S1001L01.jpg
Mask: masks/001_L_S1001L01.png
Status: failed
Reason: [Either: "failed_to_encode", "image_load_failed", "mask_load_failed"]
```

## Tech stack

Implement your solution using Python.

## Entrypoint file

The CLI entrypoint file must be named `iris.py`.
