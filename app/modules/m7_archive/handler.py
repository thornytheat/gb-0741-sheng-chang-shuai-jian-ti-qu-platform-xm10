from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.errors import Problem
from app.modules.m1_intake.service import sample_source
from app.modules.m7_archive import repository, service
from app.modules.m7_archive.export import attachment
from app.store import Store, get_store

router = APIRouter(prefix='/api/runs', tags=['复测归档'])


class RunInput(BaseModel):
    sample: str | None = None
    source_id: str | None = None


@router.post('')
def create(spec: RunInput, store: Store = Depends(get_store)):
    if bool(spec.sample) == bool(spec.source_id):
        raise Problem('CHOOSE_SOURCE', '请选择一个样例或一个收件来源')
    source_id = spec.source_id or sample_source(store, spec.sample)['source_id']
    return service.run(store, source_id)


@router.get('')
def list_runs(source_id: str | None = None, store: Store = Depends(get_store)):
    with store.connect() as connection:
        return {'runs': repository.history(connection, source_id)}


@router.get('/{run_id}')
def record(run_id: str, store: Store = Depends(get_store)):
    return service.record(store, run_id)


@router.post('/{run_id}/rerun')
def rerun(run_id: str, store: Store = Depends(get_store)):
    return service.repeat(store, run_id)


@router.get('/{run_id}/export')
def export(run_id: str, store: Store = Depends(get_store)):
    return attachment(store, run_id)
