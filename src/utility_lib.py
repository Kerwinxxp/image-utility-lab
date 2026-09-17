"""Shared, native-resolution RGB utility definitions and input validation."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

EPSILONS = (2, 4, 6, 8, 10)
METRICS = ('ssim_full', 'ssim_mask', 'mse_full', 'mse_mask')
SETTINGS = dict(rgb_range=[0, 1], dtype='float64', win_size=11,
                gaussian_weights=True, sigma=1.5, use_sample_covariance=False,
                data_range=1.0, channel_average='arithmetic RGB',
                spatial_border_excluded=5,
                mask_ssim='RGB-averaged map; valid window centers inside mask',
                mask_decode='L > 0, requiring binary 0/255',
                resize=False, resample_noise=False)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha256(path):
    return digest(Path(path).read_bytes())


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f'.{os.getpid()}.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def atomic_json(path, value):
    atomic_bytes(path, json.dumps(value, ensure_ascii=False, indent=2,
                                 allow_nan=False).encode('utf-8'))


def resolve_input(root, relative):
    """Only portable relative paths, resolved against the repository root."""
    if not isinstance(relative, str) or not relative:
        raise ValueError('Input path must be a nonempty relative string')
    portable = relative.replace('\\', '/')
    if (PureWindowsPath(relative).drive or PureWindowsPath(relative).root
            or PurePosixPath(portable).is_absolute()
            or '..' in PurePosixPath(portable).parts):
        raise ValueError(f'Input path must stay inside the repository: {relative}')
    root = Path(root).resolve()
    result = (root / portable).resolve()
    if result == root or root not in result.parents:
        raise ValueError(f'Input path escapes the repository: {relative}')
    return result


def validate_manifest_rows(rows, expected_images=200):
    groups, cases, seen = {}, {}, set()
    required = ('image_id', 'case', 'mechanism', 'epsilon', 'draw_index', 'condition',
                'original_path', 'mask_path', 'source_path', 'original_sha256',
                'mask_sha256', 'source_sha256', 'width', 'height')
    for row in rows:
        if any(key not in row for key in required):
            raise ValueError('Manifest row has missing required fields')
        if row['draw_index'] != 0:
            raise ValueError('Only the saved default draw_index=0 is accepted')
        mechanism, epsilon = row['mechanism'], row['epsilon']
        if mechanism == 'original':
            if epsilon is not None:
                raise ValueError('Original must have epsilon=null')
        elif mechanism not in ('laplace', 'exponential') or epsilon not in EPSILONS:
            raise ValueError('Expected Laplace/exponential epsilon 2,4,6,8,10')
        key = (str(row['image_id']), mechanism, epsilon)
        if key in seen:
            raise ValueError(f'Duplicate manifest view: {key}')
        seen.add(key)
        image_id = str(row['image_id'])
        if row['case'] in cases and cases[row['case']] != image_id:
            raise ValueError('A case maps to more than one image_id')
        cases[row['case']] = image_id
        if row['width'] < 11 or row['height'] < 11:
            raise ValueError('SSIM requires native dimensions at least 11x11')
        for field in ('original_sha256', 'mask_sha256', 'source_sha256'):
            value = row[field]
            if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError(f'Invalid SHA256 field: {field}')
        groups.setdefault(image_id, []).append(row)
    if len(groups) != expected_images:
        raise ValueError(f'Expected {expected_images} images; manifest has {len(groups)}')
    expected = {('original', None)} | {(m, e) for m in ('laplace', 'exponential') for e in EPSILONS}
    for image_id, views in groups.items():
        if {(r['mechanism'], r['epsilon']) for r in views} != expected:
            raise ValueError(f'Incomplete 11-view set: {image_id}')
        first = views[0]
        for row in views[1:]:
            for field in ('case', 'original_path', 'mask_path', 'original_sha256', 'mask_sha256', 'width', 'height'):
                if row[field] != first[field]:
                    raise ValueError(f'Inconsistent {field}: {image_id}')
    return groups


def checked_image(path, expected_hash, mode):
    data = Path(path).read_bytes()
    if digest(data) != expected_hash:
        raise ValueError(f'Input SHA256 mismatch: {path}')
    with Image.open(io.BytesIO(data)) as image:
        return np.asarray(image.convert(mode)).copy()


def measure_arrays(original, perturbed, mask):
    if original.shape != perturbed.shape or original.ndim != 3 or original.shape[-1] != 3:
        raise ValueError('Native RGB shapes must match')
    if original.dtype != np.uint8 or perturbed.dtype != np.uint8:
        raise ValueError('Expected decoded uint8 RGB data')
    if mask.shape != original.shape[:2] or mask.dtype != bool:
        raise ValueError('Mask must be native-resolution bool H x W')
    if min(mask.shape) < 11 or not mask.any():
        raise ValueError('Need a nonempty mask and image dimensions >=11')
    if not np.array_equal(original[~mask], perturbed[~mask]):
        raise ValueError('Pixels outside the protected mask changed')
    valid_mask = mask[5:-5, 5:-5]
    if not valid_mask.any():
        raise ValueError('No mask centers have a full 11x11 SSIM window')
    x = original.astype(np.float64) / 255.0
    y = perturbed.astype(np.float64) / 255.0
    squared = np.square(y - x)
    mse_full = float(squared.mean(dtype=np.float64))
    mse_mask = float(squared[mask].mean(dtype=np.float64))
    fraction = float(mask.mean(dtype=np.float64))
    error = abs(mse_full - fraction * mse_mask)
    if error > 1e-13:
        raise ValueError('MSE area decomposition failed')
    ssim_full, maps = structural_similarity(
        x, y, data_range=1.0, win_size=11, gaussian_weights=True,
        sigma=1.5, use_sample_covariance=False, channel_axis=-1, full=True)
    valid_map = maps.mean(axis=-1, dtype=np.float64)[5:-5, 5:-5]
    if not np.isclose(ssim_full, valid_map.mean(), atol=1e-13, rtol=0):
        raise ValueError('RGB SSIM map and scalar disagree')
    return dict(width=int(mask.shape[1]), height=int(mask.shape[0]),
                mask_pixels=int(mask.sum()), mask_fraction=fraction,
                ssim_valid_mask_pixels=int(valid_mask.sum()),
                mse_full=mse_full, mse_mask=mse_mask,
                ssim_full=float(ssim_full), ssim_mask=float(valid_map[valid_mask].mean()),
                exterior_pixels_unchanged=True, mse_area_identity_error=float(error))


def summarize(rows):
    summary = []
    for mechanism in ('original', 'laplace', 'exponential'):
        for epsilon in ([None] if mechanism == 'original' else EPSILONS):
            selected = [r for r in rows if r['mechanism'] == mechanism and r['epsilon'] == epsilon]
            if not selected:
                continue
            item = dict(mechanism=mechanism, epsilon=epsilon, draw_index=0, n_images=len(selected))
            for metric in METRICS:
                values = np.asarray([r[metric] for r in selected], dtype=float)
                if not np.isfinite(values).all():
                    raise ValueError(f'Nonfinite {metric}')
                item.update({f'{metric}_mean': float(values.mean()),
                             f'{metric}_median': float(np.median(values)),
                             f'{metric}_std': float(values.std(ddof=1)) if len(values) > 1 else 0.0})
            summary.append(item)
    return summary
