import re
import unicodedata
from decimal import Decimal, InvalidOperation

from app.config import BAND_CENTRES
from app.records import Calibration, Sample

HEADER = ('band_hz', 'sample_index', 'rate_hz', 'expected_samples', 'unit', 'gain_db', 'pa_per_v', 'amplitude', 'note')
NA = {'', '-', 'N/A', 'NULL', '未知'}
INTEGER = re.compile(r'[0-9]{1,6}')
UNITS = {'Pa', 'mPa', 'V', 'mV'}


class InvalidRow(ValueError):
    pass


def integer(text):
    value = text.strip()
    if not INTEGER.fullmatch(value):
        raise ValueError
    return int(value)


def decimal(text):
    value = unicodedata.normalize('NFKC', text).strip()
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?', value) or len(value) > 40:
        raise ValueError
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError from exc


def band_hz(text):
    try:
        value = integer(text)
    except ValueError:
        return None
    return value if value in BAND_CENTRES else None


def parse(line, raw):
    try:
        index = integer(raw['sample_index'])
    except ValueError as exc:
        raise InvalidRow('SAMPLE_INVALID') from exc
    unit = raw['unit'].strip()
    if unit not in UNITS:
        raise InvalidRow('UNIT_INVALID')
    try:
        rate, expected = (integer(raw[key]) for key in ('rate_hz', 'expected_samples'))
        gain = decimal(raw['gain_db'])
        sensitivity = decimal(raw['pa_per_v']) if unit in {'V', 'mV'} else None
        unused_sensitivity = sensitivity is None and raw['pa_per_v'].strip() != ''
        if not (1000 <= rate <= 192000 and 64 <= expected <= 80000 and -60 <= gain <= 100):
            raise ValueError
        if unused_sensitivity or (sensitivity is not None and not Decimal('0.0001') <= sensitivity <= 10_000):
            raise ValueError
    except ValueError as exc:
        raise InvalidRow('CAL_INVALID') from exc
    if unicodedata.normalize('NFKC', raw['amplitude']).strip().upper() in NA:
        raise InvalidRow('AMPLITUDE_MISSING')
    try:
        amplitude = decimal(raw['amplitude'])
        if abs(amplitude) > 1_000_000 or (amplitude and amplitude.adjusted() < -40):
            raise ValueError
    except ValueError as exc:
        raise InvalidRow('AMPLITUDE_INVALID') from exc
    return Calibration(rate, expected, unit, gain, sensitivity), Sample(line, index, amplitude, raw)
