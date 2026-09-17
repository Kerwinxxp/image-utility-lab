# Validation record

Environment: Windows, a clean Python 3.13 CPU environment, and the pinned dependencies in `requirements.txt`.

## Current entry point

- 8 numeric and workflow tests passed, covering launch from another directory, pilot labels, and code snapshots in the ZIP.
- A 3-image run completed measurement, plotting, and packaging: 33 result rows.
- The metric library is byte-for-byte unchanged from before the folder cleanup.

## Initial full validation

- Measured all 200 images: 2,200 unique records.
- All four metrics matched the original implementation within `1e-12` absolute error, across both methods and every ε.
- Checked input hashes, native dimensions, and unchanged pixels outside masks. Generated raw results, summaries, plots, and a submission ZIP.
- A fresh GitHub clone passed a 3-image measurement and export check in a clean environment.

Submission ZIPs include full-precision values, input identities, the run environment, and snapshots of the measurement and plotting code actually used.

The data release includes archive hashes. Each input file was checked against the manifest before upload.

The repository provides inputs and code. Students generate and submit their own measurement results.
