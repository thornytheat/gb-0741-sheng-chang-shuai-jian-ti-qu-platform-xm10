from fastapi import APIRouter, Depends

from app.modules.m1_intake.service import load
from app.modules.m3_decay.service import decay
from app.modules.m5_noise.gate import noise_gate
from app.store import Store, get_store

router = APIRouter(prefix='/api/noise', tags=['噪声判废'])


@router.get('/{source_id}')
def get_noise(source_id: str, store: Store = Depends(get_store)):
    curves, _, _ = decay(load(store, source_id))
    return {'bands': [noise_gate(curve) for curve in curves.values()]}
