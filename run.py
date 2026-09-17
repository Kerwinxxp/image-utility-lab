"""Student entry point: measure utility, draw curves, and package the results."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Measure the 200-image dataset and prepare your result ZIP.',
        epilog='First try: python run.py --limit-images 3. Full experiment: python run.py.')
    parser.add_argument('--step', choices=('all', 'measure', 'plot', 'package'), default='all',
                        help='Run all three steps, or repeat one step (default: all)')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2,
                        help='CPU workers for measurement (default: 2)')
    parser.add_argument('--output', help='Result folder; default: results/draw0 or results/checkN for a pilot')
    parser.add_argument('--limit-images', type=int, metavar='N',
                        help='Run a labeled N-image pilot instead of the full experiment')
    parser.add_argument('--manifest', default='config/im2gps200_draw0.jsonl',
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.limit_images is not None and not 1 <= args.limit_images <= 200:
        parser.error('--limit-images must be between 1 and 200')
    pilot = args.limit_images is not None and args.limit_images < 200
    output = Path(args.output or (f'results/check{args.limit_images}' if pilot else 'results/draw0'))
    output = (output if output.is_absolute() else ROOT / output).resolve()
    steps = ('measure', 'plot', 'package') if args.step == 'all' else (args.step,)

    needed = ('numpy', 'scipy', 'PIL', 'skimage') + (('matplotlib',) if 'plot' in steps else ())
    missing = [name for name in needed if importlib.util.find_spec(name) is None]
    if missing:
        print('Setup needed: install the dependencies first.\n'
              'Run: python -m pip install -r requirements.txt\n'
              f'Missing modules: {", ".join(missing)}', file=sys.stderr)
        return 1

    if 'measure' in steps:
        manifest = ROOT / args.manifest
        if not manifest.is_file():
            print(f'Missing input list: {manifest}\nDownload the complete repository first.', file=sys.stderr)
            return 1
        try:
            rows = [json.loads(line) for line in manifest.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            paths = {row[key] for row in rows for key in ('original_path', 'mask_path', 'source_path')}
        except (ValueError, KeyError) as error:
            print(f'Cannot read the input list: {error}', file=sys.stderr)
            return 1
        absent = sorted(path for path in paths if not (ROOT / path).is_file())
        if absent:
            print(f'Data setup needed: {len(absent)} input files are missing.\n'
                  'Download and extract all four data ZIPs into this repository, as shown in README.md.\n'
                  f'First missing file: {absent[0]}', file=sys.stderr)
            return 1

    print('PILOT: these results are for checking setup only.' if pilot else 'Full 200-image experiment.', flush=True)
    print(f'Results: {output}', flush=True)
    commands = {
        'measure': ['src/run_utility.py', '--manifest', args.manifest,
                    '--output', str(output), '--workers', str(args.workers)],
        'plot': ['src/plot_utility.py', '--results', str(output / 'per_image_results.csv'),
                 '--output', str(output / 'figures')],
        'package': ['src/package_results.py', '--results', str(output)],
    }
    if args.limit_images is not None:
        commands['measure'] += ['--limit-images', str(args.limit_images)]
    if pilot:
        commands['package'].append('--allow-pilot')
    titles = {'measure': 'Measure MSE and SSIM', 'plot': 'Draw utility-versus-epsilon curves',
              'package': 'Save raw results, curves, and run records in one ZIP'}
    for index, step in enumerate(steps, 1):
        print(f'\n[{index}/{len(steps)}] {titles[step]}', flush=True)
        command = commands[step]
        try:
            subprocess.run([sys.executable, str(ROOT / command[0]), *command[1:]], cwd=ROOT, check=True)
        except subprocess.CalledProcessError:
            print(f'\nThe {step} step stopped. See the error above; completed measurements are cached.\n'
                  'Correct the problem and repeat the same command.', file=sys.stderr)
            return 1
        except OSError as error:
            print(f'Could not start the {step} step: {error}', file=sys.stderr)
            return 1
    if 'package' in steps:
        archive = output.parent / (output.name + '_submission.zip')
        print(f'\n{"PILOT CHECK" if pilot else "READY TO SEND"}: {archive}', flush=True)
        if pilot:
            print('For the assigned 200-image experiment, run: python run.py', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
