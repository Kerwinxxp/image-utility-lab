"""Measure saved draw-0 images on a CPU. No noise generation or model inference."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import time

for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import numpy as np
import PIL
import scipy
import skimage

from utility_lib import (METRICS, SETTINGS, atomic_bytes, atomic_json, canonical,
                         checked_image, digest, measure_arrays, resolve_input,
                         sha256, summarize, validate_manifest_rows)

ROOT = Path(__file__).resolve().parents[1]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def compute_case(task):
    root, rows, cache_dir, computation = task
    first = rows[0]
    original = checked_image(resolve_input(root, first['original_path']), first['original_sha256'], 'RGB')
    mask_image = checked_image(resolve_input(root, first['mask_path']), first['mask_sha256'], 'L')
    if not np.isin(mask_image, [0, 255]).all():
        raise ValueError(f'Mask is not binary 0/255: {first["case"]}')
    mask = mask_image > 0
    if original.shape[:2] != (first['height'], first['width']) or mask.shape != original.shape[:2]:
        raise ValueError(f'Native size differs from manifest: {first["case"]}')
    results, reused = [], 0
    for row in rows:
        # Hash every input on every run, including when a cached metric is used.
        image = checked_image(resolve_input(root, row['source_path']), row['source_sha256'], 'RGB')
        fingerprint = digest(canonical(dict(input=row, computation=computation)))
        cache_path = Path(cache_dir) / f'{fingerprint}.json'
        result = None
        if cache_path.exists():
            try:
                saved = json.loads(cache_path.read_text(encoding='utf-8'))
                candidate = saved['row']
                if (saved.get('fingerprint') == fingerprint
                        and saved.get('row_sha256') == digest(canonical(candidate))
                        and all(candidate.get(k) == value for k, value in row.items())
                        and all(np.isfinite(candidate[m]) for m in METRICS)):
                    result = candidate
                    reused += 1
            except (ValueError, KeyError, TypeError):
                pass  # A malformed/incomplete cache is safely recomputed.
        if result is None:
            result = dict(row)
            result.update(measure_arrays(original, image, mask))
            atomic_json(cache_path, dict(fingerprint=fingerprint,
                                        row_sha256=digest(canonical(result)), row=result))
        results.append(result)
    return results, reused


def git_identity():
    try:
        commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'],
                                         text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'],
                                            text=True, stderr=subprocess.DEVNULL).strip())
        return dict(commit=commit, working_tree_modified=dirty)
    except (OSError, subprocess.CalledProcessError):
        return dict(commit=None, working_tree_modified=None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', default='config/im2gps200_draw0.jsonl')
    parser.add_argument('--output', default='results/draw0')
    parser.add_argument('--limit-images', type=int, help='Deterministic pilot only; default is all 200')
    parser.add_argument('--workers', type=int, default=2, choices=range(1, 5))
    args = parser.parse_args(argv)
    if args.limit_images is not None and not 1 <= args.limit_images <= 200:
        parser.error('--limit-images must be between 1 and 200')
    manifest_path = resolve_input(ROOT, args.manifest)
    manifest_data = manifest_path.read_bytes()
    all_rows = [json.loads(line) for line in manifest_data.decode('utf-8-sig').splitlines() if line.strip()]
    groups = validate_manifest_rows(all_rows)
    # Validate every source path before dispatching work.
    for row in all_rows:
        for field in ('original_path', 'mask_path', 'source_path'):
            resolve_input(ROOT, row[field])
    image_ids = sorted(groups, key=lambda image_id: (groups[image_id][0]['case'], image_id))
    if args.limit_images is not None:
        image_ids = image_ids[:args.limit_images]
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    versions = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                    Pillow=PIL.__version__, scikit_image=skimage.__version__)
    code_files = ['run.py', 'src/utility_lib.py', 'src/run_utility.py',
                  'src/plot_utility.py', 'src/package_results.py',
                  'requirements.txt', 'tests/test_utility.py']
    code_hashes = {name: sha256(ROOT / name) for name in code_files}
    computation = digest(canonical(dict(settings=SETTINGS, versions=versions,
                                       code={k: code_hashes[k] for k in ['src/utility_lib.py', 'src/run_utility.py']})))
    info = dict(status='running', dataset='im2gps200', default_draw_index=0,
                scope='full_200' if len(image_ids) == 200 else 'pilot',
                n_images=len(image_ids), expected_rows=11 * len(image_ids),
                mechanisms=['original', 'laplace', 'exponential'], epsilons=[2, 4, 6, 8, 10],
                manifest=args.manifest, manifest_sha256=digest(manifest_data),
                metric_settings=SETTINGS, dependency_versions=versions,
                operating_system=platform.system(), git=git_identity(),
                code_sha256=code_hashes, computation_fingerprint=computation,
                workers=args.workers, started_utc=utc_now())
    atomic_json(output / 'run_info.json', info)
    for name in code_files:
        atomic_bytes(output / 'code_snapshot' / name, (ROOT / name).read_bytes())
    atomic_bytes(output / 'input_manifest.jsonl', manifest_data)
    tasks = [(str(ROOT), groups[image_id], str(output / 'cache'), computation) for image_id in image_ids]
    started, results, reused, completed = time.perf_counter(), [], 0, 0
    try:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(compute_case, task) for task in tasks]
            for future in as_completed(futures):
                rows, cached = future.result()
                results.extend(rows)
                reused += cached
                completed += 1
                if completed == 1 or completed % 10 == 0 or completed == len(tasks):
                    print(f'{completed}/{len(tasks)} images; {len(results)} views; {reused} cached', flush=True)
                atomic_json(output / 'progress.json', dict(completed_images=completed,
                            total_images=len(tasks), rows=len(results), reused_rows=reused))
        mechanism_order = dict(original=0, laplace=1, exponential=2)
        results.sort(key=lambda r: (r['case'], str(r['image_id']), mechanism_order[r['mechanism']], r['epsilon'] or 0))
        validate_manifest_rows(results, expected_images=len(image_ids))
        if len(results) != info['expected_rows']:
            raise ValueError('Incomplete output row count')
        atomic_bytes(output / 'per_image_results.jsonl', b''.join(canonical(row) + b'\n' for row in results))
        atomic_bytes(output / 'per_image_results.csv', csv_bytes(results))
        atomic_bytes(output / 'summary.csv', csv_bytes(summarize(results)))
        output_files = ['per_image_results.jsonl', 'per_image_results.csv', 'summary.csv', 'input_manifest.jsonl']
        info.update(status='complete', completed_utc=utc_now(), n_rows=len(results),
                    reused_rows=reused, elapsed_seconds=round(time.perf_counter() - started, 3),
                    output_sha256={name: sha256(output / name) for name in output_files})
        atomic_json(output / 'run_info.json', info)
        print(f'Complete ({info["scope"]}): {len(results)} rows saved to {output}', flush=True)
    except BaseException as error:
        info.update(status='failed', failed_utc=utc_now(), error=str(error),
                    completed_images=completed, elapsed_seconds=round(time.perf_counter() - started, 3))
        atomic_json(output / 'run_info.json', info)
        raise


if __name__ == '__main__':
    main()
