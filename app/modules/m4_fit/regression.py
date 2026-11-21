from math import fsum, isfinite


def least_squares(points):
    count = len(points)
    mean_x = fsum(x for x, _ in points) / count
    mean_y = fsum(y for _, y in points) / count
    xx = fsum((x - mean_x) ** 2 for x, _ in points)
    yy = fsum((y - mean_y) ** 2 for _, y in points)
    xy = fsum((x - mean_x) * (y - mean_y) for x, y in points)
    if not xx or not yy:
        return None
    slope = xy / xx
    intercept = mean_y - slope * mean_x
    residual = fsum((y - (slope * x + intercept)) ** 2 for x, y in points)
    if slope >= 0 or not isfinite(-60 / slope):
        return None
    return {'slope_db_s': slope, 'intercept_db': intercept, 'r2': max(0.0, 1.0 - residual / yy),
            'rt60_s': -60 / slope, 'rmse_db': (residual / count) ** 0.5}
