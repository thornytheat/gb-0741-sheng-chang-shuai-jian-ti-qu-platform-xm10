import pytest

from app.modules.m3_decay.integral import Curve
from app.modules.m4_fit.regression import least_squares
from app.modules.m4_fit.windows import crossing, fit_window


def test_regression_recovers_exact_rt60():
    fit = least_squares([(t, -80*t + 5) for t in range(1, 10)])
    assert (fit['slope_db_s'], fit['rt60_s'], fit['r2']) == (-80, .75, 1)


def test_threshold_crossing_interpolates_and_has_exclusive_stop():
    levels = [0., -4., -8., -23., -25., -35.]
    assert crossing(levels, -5, 5) == (2, 1.25)  # TRAP-23
    assert crossing(levels, -25, 4) == (4, 4.0)
    assert crossing(levels, -35, 4) is None


def test_hall_500_matches_synthetic_reference_and_cites_window(report):
    five = next(row for row in report['fit']['bands'] if row['band_hz'] == 500)
    assert [five[name]['rt60_s'] for name in ('t20', 't30')] == pytest.approx([.72, .72], abs=2e-5)
    assert (five['t20']['window']['point_count'], five['t30']['window']['point_count']) == (240, 360)
    assert (five['t20']['window']['start_line'], five['t20']['window']['end_line']) == (2269, 2509)


def test_zero_regression_variance_and_nondecay_refused():
    assert least_squares([(0, -3), (1, -3), (2, -3)]) is None
    assert least_squares([(0, -4), (1, -3), (2, -2)]) is None


def test_low_point_count_returns_window_without_rt(signal):
    curve = Curve(signal([1]*50), (1,) * 50, [0, -5, -15, -25, -35] + [-50] * 45, 40, 0, None, 1)
    gate = {'error': None, 'usable_depth_db': 50, 'usable_index': 30}
    fit = fit_window(curve, gate, 25)
    assert fit['rt60_s'] is None and fit['error']['code'] == 'WINDOW_TOO_SHORT'
    assert fit['window']['point_count'] == 2


def test_low_linearity_preserves_diagnostic_without_publishing_rt(signal):
    levels = [0, -5] + [-6] * 15 + [-23] * 15 + [-25, -40] + [-41] * 10
    curve = Curve(signal([1]*len(levels)), (1,) * len(levels), levels, 40, 0, None, 1)
    fit = fit_window(curve, {'error': None, 'usable_depth_db': 40, 'usable_index': 36}, 25)
    assert fit['error']['code'] == 'LOW_LINEARITY' and fit['rt60_s'] is None
    assert fit['regression']['r2'] < .96 and 'rt60_s' not in fit['regression']
