"""Draw utility-versus-epsilon curves from a completed student's raw results."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

import utility_lib
from utility_lib import EPSILONS, METRICS, atomic_bytes, atomic_json, digest, sha256, summarize

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='results/draw0/per_image_results.csv')
    parser.add_argument('--output', default='results/draw0/figures')
    args = parser.parse_args(argv)
    plot_sources = {'plot_utility.py': Path(__file__).read_bytes(),
                    'utility_lib.py': Path(utility_lib.__file__).read_bytes()}
    source = Path(args.results)
    source = source if source.is_absolute() else ROOT / source
    output = Path(args.output)
    output = output if output.is_absolute() else ROOT / output
    info = json.loads((source.parent / 'run_info.json').read_text(encoding='utf-8'))
    if info.get('status') != 'complete' or sha256(source) != info['output_sha256'].get(source.name):
        raise ValueError('Raw results are incomplete or differ from the completed run')
    with source.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row['epsilon'] = float(row['epsilon']) if row['epsilon'] else None
        for metric in METRICS:
            row[metric] = float(row[metric])
    if len(rows) != info['n_rows']:
        raise ValueError('Unexpected raw-result row count')
    summary = summarize(rows)
    lookup = {(r['mechanism'], r['epsilon']): r for r in summary}
    output.mkdir(parents=True, exist_ok=True)
    for name, source_bytes in plot_sources.items():
        atomic_bytes(output / 'plot_code_snapshot' / name, source_bytes)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.labelcolor': '#263a45', 'text.color': '#263a45',
                         'axes.edgecolor': '#b2bac0', 'xtick.color': '#53626d',
                         'ytick.color': '#53626d', 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.4), sharex=True)
    styles = [('laplace', 'Laplace', '#C47535', 'o'),
              ('exponential', 'Exponential', '#188B8F', 's')]
    panel_settings = [('ssim_full', 'Whole image', 'SSIM (higher = closer to original)'),
                      ('ssim_mask', 'Protected region', 'SSIM (higher = closer to original)'),
                      ('mse_full', 'Whole image', 'MSE (lower = closer to original)'),
                      ('mse_mask', 'Protected region', 'MSE (lower = closer to original)')]
    for ax, (metric, title, ylabel) in zip(axes.flat, panel_settings):
        for mechanism, label, color, marker in styles:
            values = [lookup[(mechanism, epsilon)][metric + '_mean'] for epsilon in EPSILONS]
            ax.plot(EPSILONS, values, color=color, marker=marker, linewidth=2.6,
                    markersize=6.5, label=label)
        ax.set_title(title, fontsize=14, fontweight='bold', pad=13)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_xticks(EPSILONS)
        ax.set_xlim(1.65, 10.35)
        ax.grid(axis='y', color='#e5e9ec', linewidth=.8)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        if metric.startswith('ssim'):
            ax.set_ylim(-.04, 1.06)
            ax.axhline(1, color='#9ba8b0', linewidth=1.1, linestyle='--')
            ax.text(.02, .97, 'Original = 1', transform=ax.transAxes, fontsize=10,
                    va='top', color='#778792')
        else:
            ax.set_ylim(bottom=0)
            ax.text(.98, .97, 'Original = 0', transform=ax.transAxes, fontsize=10,
                    ha='right', va='top', color='#778792')
    for ax in axes[1]:
        ax.set_xlabel('Noise parameter ε  →  weaker noise', labelpad=10)
    fig.suptitle('Image utility as noise decreases', fontsize=21, fontweight='bold', y=.975)
    scope = 'PILOT · ' if info['scope'] != 'full_200' else ''
    fig.text(.5, .924, f'{scope}{info["n_images"]} images · saved draw 0 · equal weight per image',
             ha='center', fontsize=12, color='#637781')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(.5, .906),
               ncol=2, frameon=False, handlelength=2.6, columnspacing=3)
    fig.text(.5, .025,
             'Reference: original image. MSE uses RGB / 255. SSIM in the region uses windows centered inside the mask.',
             ha='center', fontsize=10, color='#637781')
    fig.subplots_adjust(left=.105, right=.975, bottom=.13, top=.817, hspace=.40, wspace=.29)
    for extension in ('png', 'pdf'):
        fig.savefig(output / f'utility_vs_epsilon.{extension}', dpi=200, facecolor='white')
    plt.close(fig)
    atomic_json(output / 'plot_info.json', dict(created_utc=datetime.now(timezone.utc).isoformat(),
                source_sha256=sha256(source), n_images=info['n_images'], scope=info['scope'],
                aggregation='arithmetic mean with equal weight per image',
                uncertainty='none; curves show means from one saved draw',
                matplotlib_version=matplotlib.__version__,
                plot_code_sha256=digest(plot_sources['plot_utility.py']),
                code_sha256={name: digest(data) for name, data in plot_sources.items()},
                files_sha256={p.name: sha256(p) for p in sorted(output.glob('utility_vs_epsilon.*'))}))
    print(f'Saved PNG and PDF curves to {output}')


if __name__ == '__main__':
    main()
