from math import fsum, log10

from app.reasons import reason

MARGIN_DB = 10


def noise_gate(curve):
    signal = curve.signal
    block = max(4, round(signal.rate * 0.01))
    usable_limit = min(len(curve.power) - 1, curve.tail_from - 1)
    threshold = curve.noise_power * (10 ** (MARGIN_DB / 10))
    if threshold > 0:
        first_low = None
        for start in range(0, curve.tail_from - block + 1, block):
            mean = fsum(curve.power[start:start + block]) / block
            if mean < threshold:
                if first_low is not None:
                    usable_limit = first_low - 1
                    break
                first_low = start
            else:
                first_low = None
    depth_at = next((index for index in range(usable_limit, -1, -1) if curve.db[index] is not None), None)
    depth = -curve.db[depth_at] if depth_at is not None else 0.0
    snr = 10 * log10(max(curve.power) / curve.noise_power) if max(curve.power) and curve.noise_power else None
    error = curve.error or (reason('DYNAMIC_RANGE') if depth < 25.0 else None)
    return {'band_hz': signal.hz, 'noise_power_pa2': curve.noise_power, 'floor_db': curve.floor_db,
            'peak_to_noise_db': snr, 'required_margin_db': MARGIN_DB, 'usable_depth_db': depth,
            'usable_index': usable_limit, 'usable_until_s': usable_limit / signal.rate if usable_limit >= 0 else None,
            'noise_from_s': curve.tail_from / signal.rate, 'supports_t20': error is None and depth >= 25.0,
            'supports_t30': error is None and depth >= 35.0, 'error': error}
