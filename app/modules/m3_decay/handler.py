from fastapi import APIRouter, Depends

from app.modules.m1_intake.service import load
from app.modules.m3_decay.service import decay
from app.store import Store, get_store

router = APIRouter(prefix='/api/decay', tags=['能量衰减'])


@router.get('/{source_id}')
def get_decay(source_id: str, store: Store = Depends(get_store)):
    return decay(load(store, source_id))[2]
