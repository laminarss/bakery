from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.bills import router as billing_router
from app.api.products import router as products_router
from app.config import get_settings
from app.db import create_tables

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()
@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def billing_page(request: Request):
    return templates.TemplateResponse(request=request, name="billing.html")


@app.get("/bills/{bill_id}", response_class=HTMLResponse)
def bill_page(request: Request, bill_id: int):
    return templates.TemplateResponse(request=request, name="bill.html", context={"bill_id": bill_id})


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(request=request, name="history.html")


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request):
    return templates.TemplateResponse(request=request, name="products.html")


app.include_router(products_router)
app.include_router(billing_router)
