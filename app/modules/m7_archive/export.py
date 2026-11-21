from fastapi.responses import Response

from app.evidence import canonical
from app.modules.m7_archive.service import record


def attachment(store, run_id):
    body = canonical(record(store, run_id))
    return Response(body, media_type='application/json', headers={
        'Content-Disposition': f'attachment; filename="hall-decay-{run_id[:12]}.json"',
    })
