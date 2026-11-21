import pytest

from app.modules.m3_decay.integral import integrate, reverse_energy, tail_power
from app.modules.m3_decay.service import render_curve


def test_reverse_integral_is_energy_after_index():
    assert reverse_energy([9, 4, 1], 0) == [14, 5, 1]
    assert reverse_energy([9, 4, 1], 1) == [11, 3, 0]


def test_noise_residual_cannot_make_curve_rise_again():
    assert reverse_energy([10, 0, 8, 2], 3) == [8, 4, 4, 0]


def test_tail_uses_median_block_power_not_single_spike():
    start, power = tail_power([9] * 85 + [4] * 14 + [1e12])
    assert start == 85 and power == 4


def test_alignment_starts_at_peak_and_energy_integrates_sample_interval(signal):
    curve = integrate(signal([.01, .01, 4, 2, 1] + [0] * 90, peak=2))
    output = render_curve(curve)
    assert output['points'][0] == {'t': 0, 'db': 0, 'source_line': 4}
    assert output['initial_energy_pa2_s'] == pytest.approx(.021)
    assert output['points'][1]['db'] == pytest.approx(-6.232492903979004)


def test_sample_curve_is_monotone_and_sign_is_squared(report):
    curve = next(row for row in report['decay']['bands'] if row['band_hz'] == 500)
    levels = [point['db'] for point in curve['points'] if point['db'] is not None]
    assert levels == sorted(levels, reverse=True) and levels[0] == 0
    assert curve['points'][1]['db'] == pytest.approx(-1/6, abs=1e-6)
    assert curve['full_points'] == 1094 and len(curve['points']) < curve['full_points']
    assert curve['points'][-1]['t'] == 1.093


def test_zero_energy_has_null_curve_and_explicit_reason(signal):
    curve = integrate(signal([0] * 100))
    assert curve.error['code'] == 'NO_ENERGY'
    assert set(curve.db) == {None} and curve.floor_db is None
