from fastapi import APIRouter, Depends

from app.modules.m1_intake.service import load
from app.modules.m2_calibration.service import calibration
from app.store import Store, get_store

router = APIRouter(prefix='/api/calibration', tags=['量纲校准'])


@router.get('/{source_id}')
def get_calibration(source_id: str, store: Store = Depends(get_store)):
    return calibration(load(store, source_id))[1]
