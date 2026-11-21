import pytest

from app.modules.m3_decay.integral import Curve, integrate
from app.modules.m5_noise.gate import noise_gate


def test_both_fits_refused_when_noise_compresses_range(report):
    gate = next(row for row in report['noise']['bands'] if row['band_hz'] == 125)
    assert gate['usable_depth_db'] == pytest.approx(13.89, abs=.02)
    assert gate['error']['code'] == 'DYNAMIC_RANGE'
    assert not gate['supports_t20'] and not gate['supports_t30']


def test_between_25_and_35_db_only_t20_allowed(report):
    gate = next(row for row in report['noise']['bands'] if row['band_hz'] == 4000)
    fit = next(row for row in report['fit']['bands'] if row['band_hz'] == 4000)
    assert 25 < gate['usable_depth_db'] < 35 and gate['supports_t20'] and not gate['supports_t30']
    assert fit['t20']['rt60_s'] == pytest.approx(.63, abs=.001)
    assert fit['t30']['rt60_s'] is None and fit['t30']['error']['code'] == 'DYNAMIC_RANGE'


def test_consecutive_low_blocks_cut_at_first_block(signal):
    power = tuple([100] * 10 + [1] * 10 + [100] * 10 + [1] * 30)
    curve = Curve(signal([1] * 60), power, [-index for index in range(60)], 55, 1, -20, 1)
    quality = noise_gate(curve)
    assert quality['usable_index'] == 29  # TRAP-19
    assert (quality['supports_t20'], quality['supports_t30']) == (True, False)


def test_tail_peak_gets_short_tail_reason(signal):
    curve = integrate(signal([0] * 96 + [2, 1, .2, 0], peak=96))
    quality = noise_gate(curve)
    assert quality['error']['code'] == 'TAIL_TOO_SHORT' and quality['usable_until_s'] is None


def test_zero_noise_has_no_infinite_log(signal):
    curve = integrate(signal([2, 1] + [0] * 98))
    quality = noise_gate(curve)
    assert quality['peak_to_noise_db'] is None and quality['floor_db'] is None
    assert quality['usable_depth_db'] == pytest.approx(6.98970004336)


def test_quality_api_returns_source_dependent_cutoff(client, source):
    reply = client.get(f'/api/noise/{source}')
    band = next(item for item in reply.json()['bands'] if item['band_hz'] == 500)
    assert reply.status_code == 200 and band['required_margin_db'] == 10
    assert band['usable_until_s'] == pytest.approx(.769)
    assert band['noise_from_s'] == pytest.approx(.93)
