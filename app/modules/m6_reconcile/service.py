from collections import Counter

from app.modules.m3_decay.service import decay
from app.modules.m4_fit.service import fits
from app.modules.m6_reconcile.comparison import DISAGREEMENT_LIMIT, compare


def reconcile(data, fitted):
    rows = [compare(row) for row in fitted['bands']]
    rows.extend({**row, 'status': 'ISOLATED', 't20_s': None, 't30_s': None, 'relative_gap': None, 'gap_flag': None}
                for row in data.rejected_bands)
    rows.sort(key=lambda row: row['band_hz'])
    totals = Counter(row['status'] for row in rows)
    declared = len(data.bands) + len(data.rejected_bands)
    row_gap = data.counts['input'] - sum(value for key, value in data.counts.items() if key != 'input')
    band_gap = declared - sum(totals.values())
    expected_bands = {band.hz for band in data.bands} | {row['band_hz'] for row in data.rejected_bands}
    identities_match = expected_bands == {row['band_hz'] for row in rows} and len(rows) == len(expected_bands)
    return {'status': 'MATCHED' if identities_match and band_gap == row_gap == 0 else 'DIFFERENCE',
            'totals': {'bands': declared, 'fitted': totals['FIT'], 'insufficient': totals['INSUFFICIENT'],
                       'isolated': totals['ISOLATED'], 'band_difference': band_gap, 'row_difference': row_gap,
                       'flagged': sum(row['gap_flag'] is not None for row in rows)},
            'disagreement_limit': DISAGREEMENT_LIMIT, 'bands': rows,
            'unassigned_rows': sum(item['band_hz'] is None for item in data.row_issues)}


def evaluate(data):
    curves, calibration, decay_report = decay(data)
    fitted, noise = fits(curves)
    return {'calibration': calibration, 'decay': decay_report, 'fit': fitted, 'noise': noise,
            'reconcile': reconcile(data, fitted)}
