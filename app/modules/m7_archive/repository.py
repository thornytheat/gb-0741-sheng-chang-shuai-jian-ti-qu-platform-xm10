import json

from app.errors import Problem

META = 'id, source_id, version, created_at, elapsed_ms, digest'


def insert(connection, manifest, evidence):
    values = tuple(manifest[key] for key in META.split(', '))
    cursor = connection.execute(f'INSERT INTO runs ({META}, evidence) VALUES (?, ?, ?, ?, ?, ?, ?) '
                                'ON CONFLICT(id) DO NOTHING', (*values, evidence))
    return cursor.rowcount == 1


def read(connection, run_id):
    row = connection.execute(f'SELECT {META}, evidence FROM runs WHERE id=?', (run_id,)).fetchone()
    if row is None:
        raise Problem('RUN_MISSING', '复测归档不存在', 404)
    return {'manifest': {key: row[key] for key in META.split(', ')}, 'result': json.loads(row['evidence'])}


def history(connection, source_id=None):
    rows = connection.execute(f'SELECT {META} FROM runs WHERE (? IS NULL OR source_id=?) '
                              'ORDER BY created_at DESC, id LIMIT 100', (source_id, source_id))
    return [dict(row) for row in rows]
