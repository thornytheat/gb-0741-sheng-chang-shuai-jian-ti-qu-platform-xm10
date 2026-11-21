from dataclasses import replace
from decimal import Decimal

import pytest

from app.modules.m1_intake.contract import HEADER, InvalidRow, parse
from app.modules.m2_calibration.units import calibrate, factor
from app.records import Calibration


def test_voltage_gain_and_sensitivity_work_on_sample(data):
    band = next(row for row in data.bands if row.hz == 500)
    signal = calibrate(band)
    assert factor(band.calibration) == pytest.approx(.0002)  # TRAP-15
    assert signal.pa[6] == pytest.approx(1.00000002)
    assert signal.pa[7] < 0 < signal.pa[6]


def test_fullwidth_amplitude_is_normalized(data):
    first = next(row for row in data.bands if row.hz == 500).samples[6]
    assert first.raw['amplitude'].startswith('５')  # TRAP-06
    assert first.amplitude == Decimal('5000.0001')


def test_gain_is_removed_in_amplitude_domain():
    pressure = Calibration(1000, 64, 'Pa', Decimal(20), None)
    assert factor(pressure) == pytest.approx(.1)
    assert factor(replace(pressure, unit='mPa', gain_db=Decimal(-20))) == pytest.approx(.01)


def test_negative_peak_uses_absolute_magnitude(data):
    band = next(row for row in data.bands if row.hz == 500)
    inverted = replace(band, samples=[replace(sample, amplitude=-sample.amplitude) for sample in band.samples])
    signal = calibrate(inverted)
    assert signal.peak_index == 6 and signal.pa[6] < 0 and signal.line_numbers[6] == 2207


def test_voltage_requires_positive_sensitivity_under_contract():
    row = dict(zip(HEADER, ['500','0','1000','64','V','0','0','1','']))
    with pytest.raises(InvalidRow, match='CAL_INVALID'):
        parse(2, row)


def test_api_surfaces_unit_rms_and_peak_line(client, source):
    reply = client.get(f'/api/calibration/{source}')
    assert reply.status_code == 200
    report = next(row for row in reply.json()['bands'] if row['band_hz'] == 1000)
    assert (report['input']['unit'], report['peak_index']) == ('mPa', 6)
    assert report['factor_pa'] == pytest.approx(.0005011872)
    assert report['rms_pa'] == pytest.approx(.238938, abs=.002)
