from app.config import SAMPLES
from app.errors import Problem
from app.evidence import sha256
from app.modules.m1_intake.reader import read


def summary(source_id, data):
    return {'source_id': source_id, 'encoding': data.encoding, 'counts': data.counts,
            'bands': [{'band_hz': band.hz, 'calibration': band.calibration.public(),
                       'first_line': band.samples[0].line, 'last_line': band.samples[-1].line} for band in data.bands],
            'isolated_bands': data.rejected_bands, 'row_issues': data.row_issues}


def save_source(store, content):
    data = read(content)
    source_id = sha256(content)
    with store.connect() as connection:
        connection.execute('INSERT OR IGNORE INTO source VALUES (?, ?)', (source_id, content))
    return summary(source_id, data)


def sample_source(store, key):
    if key not in SAMPLES:
        raise Problem('SAMPLE_UNKNOWN', '请选择有效样例', 404)
    source_id = sha256(SAMPLES[key].read_bytes())
    return summary(source_id, load(store, source_id))


def load(store, source_id):
    with store.connect() as connection:
        row = connection.execute('SELECT content FROM source WHERE id=?', (source_id,)).fetchone()
    if row is None:
        raise Problem('SOURCE_MISSING', '收件记录不存在', 404)
    return read(row['content'])
