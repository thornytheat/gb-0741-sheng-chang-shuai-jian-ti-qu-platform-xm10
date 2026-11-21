from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import APP_DIR, SAMPLES, database_path
from app.errors import Problem, response
from app.modules.m1_intake.handler import router as intake
from app.modules.m1_intake.service import save_source
from app.modules.m2_calibration.handler import router as calibration
from app.modules.m3_decay.handler import router as decay
from app.modules.m4_fit.handler import router as fit
from app.modules.m5_noise.handler import router as noise
from app.modules.m6_reconcile.handler import router as reconcile
from app.modules.m7_archive.handler import router as archive
from app.store import Store
from app.web import router as web


def create_app(path=None):
    @asynccontextmanager
    async def lifespan(application):
        application.state.store = Store(path or database_path())
        for path_to_sample in SAMPLES.values():
            save_source(application.state.store, path_to_sample.read_bytes())
        yield

    application = FastAPI(title='声场衰减提取台', lifespan=lifespan)
    application.add_exception_handler(Problem, response)
    for router in (intake, calibration, decay, fit, noise, reconcile, archive, web):
        application.include_router(router)
    application.mount('/static', StaticFiles(directory=APP_DIR / 'static'), name='static')
    return application


app = create_app()
