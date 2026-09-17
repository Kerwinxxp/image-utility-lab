# Run guide

Run commands from the repository root. On macOS / Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

## Commands

Full run:

```powershell
.venv\Scripts\python.exe run.py
```

Run one step:

```powershell
.venv\Scripts\python.exe run.py --step measure
.venv\Scripts\python.exe run.py --step plot
.venv\Scripts\python.exe run.py --step package
```

After editing plot styles, rerun `plot`, then `package`. For options, use `.venv\Scripts\python.exe run.py --help`.

## Common questions

**Missing images or `data/`?**

Extract all four data ZIPs. The `data/` folder must sit beside `run.py`, with `statue/` inside it. Avoid an extra nested `image-utility-lab-main/` folder.

**High memory use?**

The default is two images at a time. Use one:

```powershell
.venv\Scripts\python.exe run.py --workers 1
```

**Interrupted run?**

Rerun the same command. Completed results are reused after data, code, and settings checks. Keep inputs and metric definitions unchanged during the run.

**Try three images first?**

```powershell
.venv\Scripts\python.exe run.py --limit-images 3
```

This saves to `results/check3/`. Then run the full command to create `results/draw0_submission.zip`.

**Run code checks?**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**Verify a download?**

Compare each ZIP's SHA256 hash with `SHA256SUMS.txt` in the data release. On Windows:

```powershell
Get-FileHash im2gps200_base.zip -Algorithm SHA256
```

The measurement code also checks every image and mask hash.

**Send screenshots only?**

Send the full `results/draw0_submission.zip` to **Kerwinxxp (the project owner)**. The raw CSV/JSONL values are needed for analysis.
