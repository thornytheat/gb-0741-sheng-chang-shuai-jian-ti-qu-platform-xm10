from app.records import Signal

SCALE = {'Pa': 1.0, 'mPa': 0.001, 'V': 1.0, 'mV': 0.001}


def factor(config):
    gain = 10 ** (float(config.gain_db) / 20.0)
    sensor = float(config.pa_per_v) if config.pa_per_v is not None else 1.0
    return SCALE[config.unit] * sensor / gain


def calibrate(band):
    multiplier = factor(band.calibration)
    pressures = tuple(float(sample.amplitude) * multiplier for sample in band.samples)
    peak = max(range(len(pressures)), key=lambda index: abs(pressures[index]))
    return Signal(band.hz, band.calibration.rate, peak, pressures, tuple(sample.line for sample in band.samples))
