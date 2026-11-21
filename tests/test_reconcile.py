from copy import deepcopy

import pytest

from app.config import SAMPLES
from app.modules.m1_intake.reader import read
from app.modules.m6_reconcile.comparison import compare
from app.modules.m6_reconcile.service import evaluate, reconcile


def test_dirty_sample_conserves_both_counts(report):
    result = report['reconcile']
    assert result['status'] == 'MATCHED'
    assert result['totals'] == {'bands': 8, 'fitted': 4, 'insufficient': 1, 'isolated': 3, 'band_difference': 0, 'row_difference': 0, 'flagged': 1}
    assert result['unassigned_rows'] == 1


def test_two_slope_band_gets_disagreement_flag(report):
    row = next(item for item in report['reconcile']['bands'] if item['band_hz'] == 8000)
    assert (row['t20_s'], row['t30_s']) == pytest.approx((.79543, 1.02319), abs=.0001)
    assert row['gap_flag']['code'] == 'T_DISAGREEMENT' and row['relative_gap'] == pytest.approx(.2226, abs=.0001)


def test_one_fit_preserves_valid_band_but_has_no_two_fit_comparison(report):
    row = next(item for item in report['reconcile']['bands'] if item['band_hz'] == 4000)
    assert row['status'] == 'FIT' and row['t30_s'] is None
    assert row['gap_flag'] is None and row['relative_gap'] is None


def test_independent_frequency_identity_detects_duplicate_even_with_equal_count(data, report):
    wrong = deepcopy(report['fit'])
    wrong['bands'][0]['band_hz'] = wrong['bands'][1]['band_hz']
    result = reconcile(data, wrong)
    assert result['totals']['band_difference'] == 0 and result['status'] == 'DIFFERENCE'


def test_reference_clean_recording_has_two_valid_bands():
    output = evaluate(read(SAMPLES['reference'].read_bytes()))['reconcile']
    assert [row['t30_s'] for row in output['bands']] == pytest.approx([.60, .90], abs=.001)
    assert (output['totals']['fitted'], output['totals']['isolated'], output['totals']['flagged']) == (2, 0, 0)


def test_high_threshold_equal_case_and_invalid_fits_partition():
    def values(a, b):
        return {'band_hz': 63, 't20': {'rt60_s': a, 'error': None}, 't30': {'rt60_s': b, 'error': None}}
    assert compare(values(.85, 1))['relative_gap'] == pytest.approx(.15)
    assert compare(values(.85, 1))['gap_flag'] is None
    assert compare(values(.86, 1))['gap_flag'] is None
    assert compare(values(.84, 1))['gap_flag']['code'] == 'T_DISAGREEMENT'
