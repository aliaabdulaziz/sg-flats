"""Integration guard: held-out price/category values must not affect EDA outputs."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('eda', ROOT / 'analysis/run_training_eda.py')
eda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eda)


class TrainingEdaTest(unittest.TestCase):
    def test_heldout_mutations_do_not_change_reports(self):
        def hashes():
            return {p.relative_to(eda.OUT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in eda.OUT.rglob('*') if p.is_file()}
        with contextlib.redirect_stdout(io.StringIO()):
            eda.main()
        expected = hashes()
        original = eda.pd.read_csv

        def altered(*args, **kwargs):
            frame = original(*args, **kwargs)
            heldout = frame.split.ne('train')
            frame.loc[heldout, 'resale_price'] = -999999
            frame.loc[heldout, 'town'] = 'HELDOUT_SENTINEL'
            frame.loc[heldout, 'nearest_mrt_distance_m'] = -999999
            return frame

        with patch.object(eda.pd, 'read_csv', side_effect=altered):
            with contextlib.redirect_stdout(io.StringIO()):
                eda.main()
        self.assertEqual(expected, hashes())


if __name__ == '__main__':
    unittest.main()
