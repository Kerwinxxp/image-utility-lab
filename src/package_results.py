"""Package raw utility measurements and figures for return to the supervisor."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from utility_lib import canonical, sha256

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='results/draw0')
    parser.add_argument('--allow-pilot', action='store_true',
                        help='Explicitly export a labeled pilot; default requires all 200 images')
    args = parser.parse_args(argv)
    source = Path(args.results)
    source = source if source.is_absolute() else ROOT / source
    info = json.loads((source / 'run_info.json').read_text(encoding='utf-8'))
    if info.get('status') != 'complete':
        raise ValueError('Only completed runs can be submitted')
    full = info.get('scope') == 'full_200' and info.get('n_images') == 200 and info.get('n_rows') == 2200
    if not full and not args.allow_pilot:
        raise ValueError('Submission requires full_200, 200 images and 2200 rows; use --allow-pilot for a labeled pilot')
    if not full and (info.get('scope') != 'pilot' or not 1 <= info.get('n_images', 0) < 200
                     or info.get('n_rows') != 11 * info['n_images']):
        raise ValueError('Invalid pilot scope or row count')
    for name, expected in info['output_sha256'].items():
        if sha256(source / name) != expected:
            raise ValueError(f'Result hash mismatch: {name}')
    for name, expected in info['code_sha256'].items():
        if sha256(source / 'code_snapshot' / name) != expected:
            raise ValueError(f'Run code snapshot changed: {name}')
    plot_path = source / 'figures' / 'plot_info.json'
    plot_info = json.loads(plot_path.read_text(encoding='utf-8'))
    if plot_info['source_sha256'] != info['output_sha256']['per_image_results.csv']:
        raise ValueError('Figures were generated from a different result file')
    plot_code = plot_info.get('code_sha256', {})
    if set(plot_code) != {'plot_utility.py', 'utility_lib.py'}:
        raise ValueError('Re-run plotting to save the actual plotting code snapshot')
    if plot_code['plot_utility.py'] != plot_info['plot_code_sha256']:
        raise ValueError('Plotting source hash declarations disagree')
    for name, expected in plot_code.items():
        if sha256(source / 'figures' / 'plot_code_snapshot' / name) != expected:
            raise ValueError(f'Actual plotting code snapshot changed: {name}')
    for name, expected in plot_info['files_sha256'].items():
        if sha256(source / 'figures' / name) != expected:
            raise ValueError(f'Figure hash mismatch: {name}')
    names = ['per_image_results.csv', 'per_image_results.jsonl', 'summary.csv',
             'run_info.json', 'input_manifest.jsonl', 'figures/plot_info.json',
             'figures/utility_vs_epsilon.png', 'figures/utility_vs_epsilon.pdf']
    names += [f'code_snapshot/{name}' for name in info['code_sha256']]
    names += [f'figures/plot_code_snapshot/{name}' for name in plot_code]
    output = source.parent / (source.name + '_submission.zip')
    temporary = output.with_suffix('.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in names:
            archive.write(source / name, name)
        archive.writestr('submission_manifest.json', canonical(dict(
            created_utc=datetime.now(timezone.utc).isoformat(), scope=info['scope'],
            n_images=info['n_images'], n_rows=info['n_rows'], draw_index=0,
            files_sha256={name: sha256(source / name) for name in names},
            excludes='Input images and per-view cache are intentionally excluded.')))
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise ValueError('Submission ZIP failed integrity check')
    temporary.replace(output)
    print(f'Send this file to your supervisor: {output}')


if __name__ == '__main__':
    main()
