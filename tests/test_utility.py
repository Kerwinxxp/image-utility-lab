"""Synthetic tests; no real-image utility answers are distributed."""
import csv
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity

from utility_lib import measure_arrays, resolve_input, sha256, validate_manifest_rows


class UtilityTests(unittest.TestCase):
    def test_identity_and_rgb_channels(self):
        rng = np.random.default_rng(13)
        x = rng.integers(0, 256, (31, 33, 3), dtype=np.uint8)
        mask = np.zeros(x.shape[:2], dtype=bool)
        mask[8:23, 9:25] = True
        identity = measure_arrays(x, x, mask)
        self.assertEqual(identity['mse_full'], 0)
        self.assertEqual(identity['ssim_full'], 1)
        self.assertEqual(identity['ssim_mask'], 1)
        y = x.copy()
        y[mask] = 90
        measured = measure_arrays(x, y, mask)
        per_channel = [structural_similarity(
            x[..., c].astype(float) / 255, y[..., c].astype(float) / 255,
            data_range=1, win_size=11, gaussian_weights=True, sigma=1.5,
            use_sample_covariance=False) for c in range(3)]
        self.assertAlmostEqual(measured['ssim_full'], np.mean(per_channel), places=13)

    def test_known_mse_and_no_uint8_subtraction(self):
        x = np.full((25, 25, 3), 255, dtype=np.uint8)
        mask = np.zeros((25, 25), dtype=bool)
        mask[6:19, 6:19] = True
        y = x.copy()
        y[mask] = 0
        measured = measure_arrays(x, y, mask)
        self.assertEqual(measured['mse_mask'], 1.0)
        self.assertAlmostEqual(measured['mse_full'], 169 / 625, places=14)
        self.assertAlmostEqual(measured['mse_full'], measured['mask_fraction'] * measured['mse_mask'])

    def test_changed_exterior_rejected(self):
        x = np.zeros((21, 21, 3), dtype=np.uint8)
        mask = np.zeros((21, 21), dtype=bool)
        mask[7:14, 7:14] = True
        y = x.copy()
        y[0, 0] = 1
        with self.assertRaisesRegex(ValueError, 'outside'):
            measure_arrays(x, y, mask)

    def test_relative_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(resolve_input(root, 'data/image.png'), root / 'data/image.png')
            for path in ('../secret', '/tmp/file', 'C:/Users/file', r'..\secret', r'\\server\file'):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    resolve_input(root, path)

    def test_manifest_rejects_duplicate_and_nondefault_draw(self):
        base = dict(image_id='a', case='case_a', draw_index=0,
                    original_path='data/a.png', mask_path='data/m.png',
                    original_sha256='a'*64, mask_sha256='b'*64,
                    source_sha256='c'*64, width=21, height=21)
        rows = [dict(base, mechanism='original', epsilon=None, condition='original', source_path='data/a.png')]
        for mechanism in ('laplace', 'exponential'):
            for epsilon in (2, 4, 6, 8, 10):
                rows.append(dict(base, mechanism=mechanism, epsilon=epsilon,
                                 condition=f'{mechanism}_{epsilon}', source_path=f'data/{mechanism}_{epsilon}.png'))
        self.assertEqual(len(validate_manifest_rows(rows, expected_images=1)), 1)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            validate_manifest_rows(rows + [rows[-1]], expected_images=1)
        rows[3] = dict(rows[3], draw_index=1)
        with self.assertRaisesRegex(ValueError, 'draw'):
            validate_manifest_rows(rows, expected_images=1)

    def test_resume_checks_code_fingerprint_and_actual_input_hash(self):
        from run_utility import compute_case
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = np.full((21, 21, 3), 150, dtype=np.uint8)
            mask = np.zeros((21, 21), dtype=np.uint8)
            mask[7:14, 7:14] = 255
            perturbed = original.copy()
            perturbed[mask > 0] = 30
            for name, data in [('original.png', original), ('mask.png', mask), ('view.png', perturbed)]:
                Image.fromarray(data).save(root / name)
            row = dict(image_id='test', case='test', mechanism='laplace', epsilon=2,
                       draw_index=0, condition='laplace2', width=21, height=21,
                       original_path='original.png', mask_path='mask.png', source_path='view.png',
                       original_sha256=sha256(root / 'original.png'),
                       mask_sha256=sha256(root / 'mask.png'), source_sha256=sha256(root / 'view.png'))
            task = (str(root), [row], str(root / 'cache'), 'code-version-a')
            first, reused = compute_case(task)
            self.assertEqual(reused, 0)
            second, reused = compute_case(task)
            self.assertEqual(reused, 1)
            self.assertEqual(first, second)
            _, reused = compute_case((*task[:3], 'code-version-b'))
            self.assertEqual(reused, 0)
            Image.fromarray(original).save(root / 'view.png')
            with self.assertRaisesRegex(ValueError, 'SHA256 mismatch'):
                compute_case(task)

    def test_submission_includes_plot_code_edited_after_measurement(self):
        """The submitted plotting source must be the version that made the plot."""
        repo = REPO / 'src'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'results' / 'pilot'
            snapshot = output / 'code_snapshot'
            snapshot.mkdir(parents=True)
            for name in ('plot_utility.py', 'package_results.py', 'utility_lib.py'):
                shutil.copyfile(repo / name, root / name)
            shutil.copyfile(root / 'plot_utility.py', snapshot / 'plot_utility.py')
            old_hash = sha256(snapshot / 'plot_utility.py')
            with (root / 'plot_utility.py').open('a', encoding='utf-8') as stream:
                stream.write('\n# Student changed the plotting implementation after measurement.\n')
            new_hash = sha256(root / 'plot_utility.py')
            self.assertNotEqual(old_hash, new_hash)
            rows = [dict(mechanism='original', epsilon=None, ssim_full=1, ssim_mask=1, mse_full=0, mse_mask=0)]
            for mechanism in ('laplace', 'exponential'):
                for epsilon in (2, 4, 6, 8, 10):
                    rows.append(dict(mechanism=mechanism, epsilon=epsilon,
                                     ssim_full=.75, ssim_mask=.25, mse_full=.02, mse_mask=.1))
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            (output / 'per_image_results.csv').write_text(stream.getvalue(), encoding='utf-8')
            for name in ('per_image_results.jsonl', 'summary.csv', 'input_manifest.jsonl'):
                (output / name).write_text('synthetic test fixture\n', encoding='utf-8')
            names = ('per_image_results.csv', 'per_image_results.jsonl', 'summary.csv', 'input_manifest.jsonl')
            info = dict(status='complete', scope='pilot', n_images=1, n_rows=11,
                        output_sha256={name: sha256(output / name) for name in names},
                        code_sha256={'plot_utility.py': old_hash})
            (output / 'run_info.json').write_text(json.dumps(info), encoding='utf-8')
            subprocess.run([sys.executable, str(root / 'plot_utility.py'),
                            '--results', str(output / 'per_image_results.csv'),
                            '--output', str(output / 'figures')], check=True,
                           capture_output=True, text=True)
            rejected = subprocess.run([sys.executable, str(root / 'package_results.py'),
                                       '--results', str(output)], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('--allow-pilot', rejected.stderr)
            subprocess.run([sys.executable, str(root / 'package_results.py'),
                            '--results', str(output), '--allow-pilot'], check=True, capture_output=True, text=True)
            with zipfile.ZipFile(output.parent / 'pilot_submission.zip') as archive:
                new_bytes = archive.read('figures/plot_code_snapshot/plot_utility.py')
                self.assertEqual(hashlib.sha256(new_bytes).hexdigest(), new_hash)
                self.assertEqual(hashlib.sha256(archive.read('code_snapshot/plot_utility.py')).hexdigest(), old_hash)
                library = archive.read('figures/plot_code_snapshot/utility_lib.py')
                self.assertEqual(hashlib.sha256(library).hexdigest(), sha256(root / 'utility_lib.py'))

    def test_student_entrypoint_runs_and_labels_a_pilot_from_another_directory(self):
        """One command must measure, plot, and export without using real inputs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'lab'
            for name in ('run.py', 'requirements.txt', 'src/utility_lib.py', 'src/run_utility.py',
                         'src/plot_utility.py', 'src/package_results.py', 'tests/test_utility.py'):
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / name, destination)
            original = np.full((21, 21, 3), 180, dtype=np.uint8)
            mask = np.zeros((21, 21), dtype=np.uint8)
            mask[7:14, 7:14] = 255
            perturbed = original.copy()
            perturbed[mask > 0] = 60
            (root / 'data').mkdir()
            for name, values in (('original.png', original), ('mask.png', mask), ('view.png', perturbed)):
                Image.fromarray(values).save(root / 'data' / name)
            rows = []
            for image_id in range(200):
                base = dict(image_id=str(image_id), case=f'case_{image_id:03}', draw_index=0,
                            width=21, height=21, original_path='data/original.png', mask_path='data/mask.png',
                            original_sha256=sha256(root / 'data/original.png'),
                            mask_sha256=sha256(root / 'data/mask.png'))
                rows.append(dict(base, mechanism='original', epsilon=None, condition='original',
                                 source_path='data/original.png', source_sha256=base['original_sha256']))
                for mechanism in ('laplace', 'exponential'):
                    for epsilon in (2, 4, 6, 8, 10):
                        rows.append(dict(base, mechanism=mechanism, epsilon=epsilon,
                                         condition=f'{mechanism}_{epsilon}', source_path='data/view.png',
                                         source_sha256=sha256(root / 'data/view.png')))
            (root / 'config').mkdir()
            (root / 'config/im2gps200_draw0.jsonl').write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            completed = subprocess.run([sys.executable, str(root / 'run.py'), '--limit-images', '3', '--workers', '1'],
                                       cwd=tmp, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn('PILOT CHECK', completed.stdout)
            output = root / 'results/check3'
            self.assertFalse((root / 'results/draw0').exists())
            info = json.loads((output / 'run_info.json').read_text(encoding='utf-8'))
            self.assertEqual((info['scope'], info['n_images'], info['n_rows']), ('pilot', 3, 33))
            self.assertIn('run.py', info['code_sha256'])
            self.assertIn('src/run_utility.py', info['code_sha256'])
            with zipfile.ZipFile(root / 'results/check3_submission.zip') as archive:
                inventory = json.loads(archive.read('submission_manifest.json'))
                self.assertEqual(inventory['scope'], 'pilot')
                for name, expected in inventory['files_sha256'].items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), expected)
                self.assertIn('code_snapshot/run.py', archive.namelist())
                self.assertIn('code_snapshot/src/run_utility.py', archive.namelist())
                self.assertFalse(any(name.startswith(('data/', 'cache/')) for name in archive.namelist()))


if __name__ == '__main__':
    unittest.main()
