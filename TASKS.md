# Student task: utility versus epsilon

## Required work

1. Install the CPU dependencies and pass the synthetic numerical tests.
2. Read the metric definitions and check that all input images and masks are correctly matched.
3. Measure **all 200 images** at epsilon **2, 4, 6, 8, 10**, for **Laplace and the finite-RGB exponential mechanism**, using saved **draw 0**.
4. Save one full-precision row per view. Include the image ID, mechanism, epsilon, draw index, whole-image/region MSE and SSIM, mask fraction, and provenance fields.
5. Plot utility versus epsilon for the four metrics, showing both methods clearly.
6. Send the submission ZIP to the supervisor, including the raw CSV/JSONL, summary, figures, run metadata and the code used.

The supervisor will perform the further analysis. No mPL calculation, privacy–utility plot, new dataset, additional random draw, model inference or written interpretation report is required for this assignment.

## Completion checklist

- 200 unique image IDs.
- 2,200 unique view rows: 200 original checks plus 1,000 rows per mechanism.
- Exactly one draw index: 0.
- Finite noise settings are exactly 2, 4, 6, 8 and 10.
- Original identity, image dimensions, file hashes and unchanged mask exteriors pass checks.
- No resizing, conversion to a different JPEG, alternative reference image, resampling or missing-case substitution.
- Whole-image and region metrics are kept separate.
- The saved numbers retain full precision, even when figure labels are rounded.
- The final run metadata identifies a complete full-data run and records the environment.
- PNG/PDF utility curves and raw data are both included in the submission.

If a check fails, save the error and affected image ID and investigate the input or implementation. Do not adjust values to force an expected trend. Any changes to metric settings should be discussed with the supervisor before the final run.
