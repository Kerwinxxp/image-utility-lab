# Image Utility Lab

Measure image quality on **200 images**, plot **utility vs. ε**, and return the raw results to **Kerwinxxp (the project owner)**.

CPU only. No GPU, model downloads, or API keys needed.

```text
Download inputs → Measure MSE / SSIM → Plot curves → Send results
```

## Experiment

| Setting | Value |
|---|---|
| Dataset | 200 im2gps images |
| Protected area | Union of the selected cue masks in each image |
| Methods | Laplace and finite-RGB exponential noise |
| Noise parameter | ε = 2, 4, 6, 8, 10; larger ε means weaker noise |
| Random draw | Saved default draw 0 |
| Metrics | MSE and SSIM, measured over the full image and the protected area |
| Reference | Each image's original version |

Inputs are already generated. Measure the supplied images without adding new noise. Expect **2,200 result rows**: 200 original checks and 1,000 noisy views per method. Lower MSE and higher SSIM indicate better visual fidelity.

## 1. Download

Download the [code ZIP](https://github.com/Kerwinxxp/image-utility-lab/archive/refs/heads/main.zip) and these four files from the [data release](https://github.com/Kerwinxxp/image-utility-lab/releases/tag/data-v1.0):

| File | Contents |
|---|---|
| `im2gps200_base.zip` | 200 originals and 200 masks |
| `im2gps200_laplace_draw0_part1.zip` | 500 Laplace images |
| `im2gps200_laplace_draw0_part2.zip` | 500 more Laplace images |
| `im2gps200_exponential_draw0.zip` | 1,000 exponential-noise images |

Extract all four data ZIPs into the code folder and merge their `data/` folders. Each ZIP extracts independently. Downloads total about 2.9 GB. The final layout should include `run.py` and `data/statue/` in the same project folder.

## 2. Install

Use **Python 3.11–3.13**. Open a terminal in the code folder.

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Replace `-3.13` with `-3.11` or `-3.12` if needed.

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 3. Run

**Windows:**

```powershell
.venv\Scripts\python.exe run.py
```

**macOS / Linux:**

```bash
.venv/bin/python run.py
```

This measures all 200 images, plots the curves, and creates the submission ZIP. To check your setup first, add `--limit-images 3`; pilot results go to `results/check3/`. Run again without that option for the full experiment.

## 4. Send the results

Send **`results/draw0_submission.zip` to Kerwinxxp (the project owner)**. It includes:

- Raw per-image results: CSV and JSONL.
- A summary table and PNG/PDF curves.
- Run settings, environment details, and the code used.

Keep full numerical precision. Your task ends with the curves and raw measurements; Kerwinxxp will handle the analysis. No written analysis report is required.

## Code guide

```text
run.py            Entry point
src/              Measurement, plotting, and packaging
config/           Input list and fixed settings
docs/             Metric definitions and instructions
tests/            Numerical and workflow checks
data/             Downloaded inputs
results/          Generated outputs
```

Start with `run.py`, then `measure_arrays` in [`src/utility_lib.py`](src/utility_lib.py). Edit [`src/plot_utility.py`](src/plot_utility.py) to change the plots.

[Metrics](docs/METRICS.md) · [Commands and troubleshooting](docs/USAGE.md) · [Submission checklist](docs/TASKS.md) · [Validation](docs/VALIDATION.md)

Image rights remain with their owners. Files retain their original bytes and metadata; see the [data card](config/data_card.json).
