from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import os

app = FastAPI(title="VPN Control Panel", version="0.1.0")
templates = Jinja2Templates(directory="app/templates")

BILLING_URL = os.getenv("BILLING_URL", "http://billing:8000")
PROVISIONER_URL = os.getenv("PROVISIONER_URL", "http://provisioner:8001")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    async with httpx.AsyncClient() as client:
        tariffs_resp = await client.get(f"{BILLING_URL}/tariffs")
        tariffs_resp.raise_for_status()
        health_resp = await client.get(f"{PROVISIONER_URL}/health")
        health_resp.raise_for_status()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tariffs": tariffs_resp.json(),
            "provisioner": health_resp.json(),
        },
    )
