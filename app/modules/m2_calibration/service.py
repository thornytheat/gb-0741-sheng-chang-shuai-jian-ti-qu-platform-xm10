from math import fsum, sqrt

from app.modules.m2_calibration.units import calibrate, factor


def calibration(data):
    signals, evidence = {}, []
    for band in data.bands:
        signal = calibrate(band)
        signals[band.hz] = signal
        evidence.append({'band_hz': band.hz, 'input': band.calibration.public(), 'factor_pa': factor(band.calibration),
                         'sample_count': len(signal.pa), 'peak_index': signal.peak_index,
                         'peak_line': signal.line_numbers[signal.peak_index], 'peak_pa': abs(signal.pa[signal.peak_index]),
                         'rms_pa': sqrt(fsum(value * value for value in signal.pa) / len(signal.pa))})
    return signals, {'bands': evidence, 'isolated_bands': [row['band_hz'] for row in data.rejected_bands]}
