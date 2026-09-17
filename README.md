# Image utility lab

Measure image quality after region-level noise on **200 im2gps images**. Compute per-image MSE and SSIM, draw **utility–epsilon curves**, and return the raw results to your supervisor.

This repository provides a portable reference implementation and fixed input images. Your task is to run, verify and document the full measurement on your own computer. You may improve the implementation while preserving the metric definitions. Existing real-image utility answers are not included.

## Scope

| Item | Setting |
|---|---|
| Dataset | 200 fixed im2gps images |
| Protected region | Union of all saved cue masks in each image |
| Mechanisms | Laplace; finite-RGB exponential mechanism |
| Noise parameters | epsilon = 2, 4, 6, 8, 10 |
| Random repetition | Existing default `draw_index=0` for every noisy view |
| Measures | Whole-image and protected-region MSE and SSIM |
| Reference | Exact saved original image |
| Computation | CPU only; Python 3.11–3.13 |
| Required output | Per-image measurements, summary table, utility–epsilon curves, run record |

There are **2,200 measured views**: 200 originals, 1,000 Laplace-noisy images and 1,000 exponential-mechanism images. The 200 masks bring the input file count to 2,400. Larger epsilon means weaker noise. `draw 0` identifies saved image files; it does not mean that every historical image used integer RNG seed zero.

## 1. Download the code and input data

Clone this private repository after your supervisor gives your GitHub account access:

```bash
git clone https://github.com/Kerwinxxp/image-utility-lab.git
cd image-utility-lab
```

Alternatively, use **Code → Download ZIP** while signed in. Then download these three files from [the data-v1.0 release](https://github.com/Kerwinxxp/image-utility-lab/releases/tag/data-v1.0):

- `im2gps200_base.zip`
- `im2gps200_laplace_draw0.zip`
- `im2gps200_exponential_draw0.zip`

Extract all three into the repository root and merge their `data/` folders. For example, the statue inputs should be at `data/statue/`, next to `manifests/`, not inside a second nested repository directory. The input set is approximately 2.71 GiB before compression. Keep enough disk space for both downloads and extraction.

Archive checksums are in `SHA256SUMS.txt` on the release. On Windows, inspect a downloaded archive with `Get-FileHash <filename> -Algorithm SHA256`; on macOS/Linux, use `shasum -a 256 <filename>`. The measurement program also checks every input file against its manifest hash.

## 2. Install the CPU environment

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest -v
```

macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v
```

Use Python 3.11, 3.12 or 3.13. The commands below show Windows paths; on macOS/Linux replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

## 3. Measure all 200 images

From the repository root:

```powershell
.venv\Scripts\python.exe run_utility.py --manifest manifests/im2gps200_draw0.jsonl --output results/draw0 --workers 2
```

The full run covers both mechanisms and all five epsilon values. All source images are already provided; the program measures them without generating new noise. Use `--workers 1` if memory is limited. A short installation check can use `--limit-images 3 --output results/check3`, but the required deliverable is the complete 200-image run.

The output includes raw `per_image_results.csv` and `per_image_results.jsonl`, `summary.csv`, and `run_info.json`. Preserve the full-precision raw files. They allow your supervisor to perform their own analyses without repeating your measurement.

## 4. Draw the utility–epsilon curves

```powershell
.venv\Scripts\python.exe plot_utility.py --results results/draw0/per_image_results.csv --output results/draw0/figures
```

Plot four quantities against epsilon: whole-image SSIM, region SSIM, whole-image MSE and region MSE. Distinguish the two mechanisms. SSIM is higher-is-better; MSE is lower-is-better. The summary weights images equally rather than pooling all pixels across images.

## 5. Return the raw results

```powershell
.venv\Scripts\python.exe package_results.py --results results/draw0
```

Send the generated submission ZIP to your supervisor. It should contain the two raw-result files, summary table, PNG/PDF curves, and run information. Keep the original precision and include any code changes you made. A screenshot alone is not sufficient.

The requested work ends with the utility curves and raw measurements; the supervisor will perform the further analysis.

## Measurement contract

- Use the exact original image specified by the manifest, decoded at its native resolution.
- Convert RGB to float64 and divide by 255 **before** subtraction. MSE uses squared normalized-channel values.
- Whole-image MSE averages all RGB channels; region MSE averages channels inside the union mask.
- SSIM uses an 11×11 Gaussian window, sigma 1.5, `data_range=1`, population covariance, and the average over RGB channels.
- Region SSIM averages the same local SSIM map at valid mask centers after excluding the outer five image pixels. Its windows may include unchanged context. It is not SSIM on a black-filled background or a resized crop.
- Original-versus-original must have MSE 0 and SSIM 1. Pixels outside the mask must be unchanged. Per image, `MSE_full = mask_fraction * MSE_region`.
- Keep negative local/region SSIM values if they occur; do not silently clip metrics or discard difficult images.

See `metric_settings.json`, `data_card.json` and [the task checklist](TASKS.md). All paths in the manifest are relative to this repository. The data retains the exact original bytes and source metadata; image rights remain with the original owners. Access is for this assigned research task, not a new license for redistribution.
