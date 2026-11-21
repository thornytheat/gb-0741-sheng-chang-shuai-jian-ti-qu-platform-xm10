from fastapi import APIRouter, Depends

from app.modules.m1_intake.service import load
from app.modules.m3_decay.service import decay
from app.modules.m4_fit.service import fits
from app.store import Store, get_store

router = APIRouter(prefix='/api/fit', tags=['拟合时段'])


@router.get('/{source_id}')
def get_fit(source_id: str, store: Store = Depends(get_store)):
    return fits(decay(load(store, source_id))[0])[0]
