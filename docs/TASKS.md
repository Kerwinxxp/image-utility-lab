# Your task

Measure utility for **200 images** and plot utility–ε curves. Kerwinxxp (the project owner) will analyze the results.

## Steps

1. Download the code and all data. Install the dependencies.
2. Read [Metrics](METRICS.md).
3. Run `.venv\Scripts\python.exe run.py` on Windows, or `.venv/bin/python run.py` on macOS / Linux.
4. Check the four metric plots, including methods, ε values, and axis labels.
5. **Send `results/draw0_submission.zip` to Kerwinxxp (the project owner).**

You may improve the plot style or code. Keep the metric definitions fixed; discuss any setting changes with Kerwinxxp first.

## Before sending

- [ ] 200 unique image IDs and 2,200 raw-result rows.
- [ ] Both methods: Laplace and the exponential mechanism.
- [ ] ε = 2, 4, 6, 8, 10 for each method; draw index = 0.
- [ ] Original-image self-checks: MSE = 0 and SSIM = 1.
- [ ] Whole-image and masked-area metrics saved separately.
- [ ] ZIP contains raw CSV/JSONL, summaries, PNG/PDF plots, and run records.
- [ ] Full results, not the `check3` pilot.
- [ ] Full numeric precision and snapshots of the code actually used.

If a check fails, record the error and image ID, then inspect the data or code. Do not drop unexpected results or force a trend.

No new noise generation, attacker runs, mPL calculation, extra seeds, or analysis report are required.
