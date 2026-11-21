from fastapi import APIRouter, Depends

from app.modules.m1_intake.service import load, summary
from app.modules.m6_reconcile.service import evaluate
from app.store import Store, get_store

router = APIRouter(prefix='/api/reconcile', tags=['频段勾稽'])


@router.get('/{source_id}')
def get_reconcile(source_id: str, store: Store = Depends(get_store)):
    return evaluate(load(store, source_id))['reconcile']


@router.get('/{source_id}/preview')
def preview(source_id: str, store: Store = Depends(get_store)):
    data = load(store, source_id)
    return {'intake': summary(source_id, data), **evaluate(data)}
