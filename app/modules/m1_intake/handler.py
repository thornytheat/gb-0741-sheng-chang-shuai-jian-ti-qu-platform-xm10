from fastapi import APIRouter, Depends, File, UploadFile

from app.config import MAX_BYTES
from app.modules.m1_intake.service import load, sample_source, save_source, summary
from app.store import Store, get_store

router = APIRouter(prefix='/api/intake', tags=['脉冲响应收件'])


@router.get('/sample/{key}')
def sample(key: str, store: Store = Depends(get_store)):
    return sample_source(store, key)


@router.get('/{source_id}')
def intake(source_id: str, store: Store = Depends(get_store)):
    return summary(source_id, load(store, source_id))


@router.post('')
def upload(file: UploadFile = File(...), store: Store = Depends(get_store)):
    return save_source(store, file.file.read(MAX_BYTES + 1))
