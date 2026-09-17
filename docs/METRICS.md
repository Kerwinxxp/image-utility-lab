# Utility metrics

Compare each noisy image with its original. The mask marks the protected area: white is inside, black is outside.

## MSE: pixel differences

Mean Squared Error (MSE) averages squared RGB differences. Lower is better; identical images have MSE = 0.

For a channel that changes from 100 to 120, the squared difference is `(120 / 255 - 100 / 255) ** 2`.

- **Whole-image MSE:** average over all pixels and RGB channels.
- **Masked-area MSE:** average only over masked pixels and RGB channels.

Convert to `float64` and divide by 255 before subtraction. Subtracting `uint8` values can cause integer wraparound.

## SSIM: local structure

The Structural Similarity Index (SSIM) compares local brightness, contrast, and structure. Higher usually means more similar; identical images have SSIM = 1.

- **Whole-image SSIM:** average over all valid window centers.
- **Masked-area SSIM:** use the same SSIM map, averaging only valid centers inside the mask.

Windows centered inside the mask may include surrounding pixels. Do not black out the background or resize a crop. Keep negative SSIM values.

## Fixed settings

| Setting | Value |
|---|---|
| Images | Native resolution, RGB; no resizing or re-encoding |
| Values | `float64`, RGB divided by 255, `data_range=1` |
| SSIM window | 11 × 11, Gaussian weights, sigma = 1.5 |
| Covariance | Population: `use_sample_covariance=False` |
| RGB reduction | Arithmetic mean across three channels |
| Valid centers | Exclude the outer 5 pixels |
| Dataset summary | Equal weight per image |

See [settings](../config/metric_settings.json) and [implementation](../src/utility_lib.py).

Keep all four metrics separate. Whole-image scores include unchanged areas; masked-area scores focus on the protected region. These measure visual fidelity, not location accuracy or privacy leakage.

## Data and repeats

Use the saved default `draw_index=0`. This identifies the first historical repeat; it does not mean every image was generated with integer seed 0.

Each image has 11 records: one original-image self-check and five ε values for each of two methods. The full run has **200 images and 2,200 rows**. Larger ε means weaker noise. Plot the measured values.

The [manifest](../config/im2gps200_draw0.jsonl) lists inputs and SHA256 hashes.
