from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import APP_DIR, RULE_VERSION

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=APP_DIR / 'templates')


@router.get('/', response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name='workbench.html', context={'version': RULE_VERSION})
