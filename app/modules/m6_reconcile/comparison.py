from math import isclose

from app.reasons import reason

DISAGREEMENT_LIMIT = 0.15


def compare(row):
    t20, t30 = row['t20']['rt60_s'], row['t30']['rt60_s']
    discrepancy = abs(t20 - t30) / t30 if t20 is not None and t30 is not None else None
    failures = [value['error'] for key, value in row.items() if key in ('t20', 't30') and value['error']]
    if t20 is not None or t30 is not None:
        category = 'FIT'
    elif any(item['code'] in {'NO_ENERGY', 'TAIL_TOO_SHORT', 'NON_DECAYING', 'LOW_LINEARITY', 'WINDOW_TOO_SHORT'} for item in failures):
        category = 'ISOLATED'
    else:
        category = 'INSUFFICIENT'
    flagged = (discrepancy is not None and discrepancy > DISAGREEMENT_LIMIT
               and not isclose(discrepancy, DISAGREEMENT_LIMIT, rel_tol=0, abs_tol=1e-12))
    return {'band_hz': row['band_hz'], 'status': category, 't20_s': t20, 't30_s': t30, 'relative_gap': discrepancy,
            'gap_flag': reason('T_DISAGREEMENT') if flagged else None,
            'findings': failures}
