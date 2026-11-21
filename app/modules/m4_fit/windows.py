from app.modules.m4_fit.regression import least_squares
from app.reasons import reason

MIN_POINTS = 8
MIN_R2 = 0.96


def crossing(db, threshold, limit):
    for index in range(1, min(len(db), limit + 1)):
        before, after = db[index - 1], db[index]
        if before is not None and after is not None and before > threshold >= after:
            return index, index - 1 + (before - threshold) / (before - after)
    return None


def fit_window(curve, noise, depth):
    signal = curve.signal
    result = {'from_db': -5, 'to_db': -depth, 'rt60_s': None, 'window': None}
    if noise['error'] or noise['usable_depth_db'] < depth:
        return {**result, 'error': noise['error'] or reason('DYNAMIC_RANGE')}
    start = crossing(curve.db, -5, noise['usable_index'])
    stop = crossing(curve.db, -depth, noise['usable_index'])
    if start is None or stop is None:
        return {**result, 'error': reason('DYNAMIC_RANGE')}
    i, begin = start
    j, end = stop
    rate = signal.rate
    points = [(index / rate, curve.db[index]) for index in range(i, j) if curve.db[index] is not None]
    window = {'start_s': begin / rate, 'end_s': end / rate, 'point_count': len(points),
              'start_line': signal.line_numbers[signal.peak_index + i], 'end_line': signal.line_numbers[signal.peak_index + j]}
    result['window'] = window
    if len(points) < MIN_POINTS:
        return {**result, 'error': reason('WINDOW_TOO_SHORT')}
    regression = least_squares(points)
    if regression is None:
        return {**result, 'error': reason('NON_DECAYING')}
    if regression['r2'] < MIN_R2:
        return {**result, 'regression': {key: value for key, value in regression.items() if key != 'rt60_s'},
                'error': reason('LOW_LINEARITY')}
    return {**result, **regression, 'error': None}
