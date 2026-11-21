import sqlite3
from datetime import datetime, timezone
from time import perf_counter_ns

from app.config import RULE_VERSION
from app.errors import Problem
from app.evidence import canonical, sha256
from app.modules.m1_intake.service import load, summary
from app.modules.m6_reconcile.service import evaluate
from app.modules.m7_archive import repository


def key(source_id):
    return sha256(canonical({'source_id': source_id, 'version': RULE_VERSION}))


def record(store, run_id):
    with store.connect() as connection:
        archive = repository.read(connection, run_id)
    if sha256(canonical(archive['result'])) != archive['manifest']['digest']:
        raise Problem('EVIDENCE_CHANGED', '归档与证据摘要不符', 409)
    return archive


def run(store, source_id):
    start = perf_counter_ns()
    data = load(store, source_id)
    result = {'intake': summary(source_id, data), **evaluate(data)}
    if result['reconcile']['status'] != 'MATCHED':
        raise Problem('UNBALANCED', '频带或数据行存在差额', 409)
    payload = canonical(result)
    manifest = {'id': key(source_id), 'source_id': source_id, 'version': RULE_VERSION,
                'created_at': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                'elapsed_ms': (perf_counter_ns() - start) // 1_000_000, 'digest': sha256(payload)}
    try:
        with store.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            added = repository.insert(connection, manifest, payload)
            archived = repository.read(connection, manifest['id'])
            if (archived['manifest']['digest'] != manifest['digest'] or
                    sha256(canonical(archived['result'])) != manifest['digest']):
                raise Problem('EVIDENCE_CHANGED', '重算结果与归档证据不符', 409)
    except sqlite3.Error as error:
        raise Problem('ARCHIVE_FAILED', '归档写入失败，请重跑', 503) from error
    return {'id': manifest['id'], 'reused': not added, 'manifest': archived['manifest'], 'result': result}


def repeat(store, run_id):
    archive = record(store, run_id)
    manifest = archive['manifest']
    if manifest['version'] != RULE_VERSION:
        raise Problem('VERSION_CHANGED', '当前规则版本与归档不同', 409)
    if key(manifest['source_id']) != run_id:
        raise Problem('EVIDENCE_CHANGED', '归档来源与编号不符', 409)
    return run(store, manifest['source_id'])
