import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from telegram import Update

from agent.assistant import chat
from agent.tools.favoritos import (
    buscar_favoritas_proximas,
    listar_linhas_favoritas,
    remover_linha_favorita,
    salvar_linha_favorita,
)
from telegram_bot import build_application

app = FastAPI(title="SPTrans Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_bot_app = None


@app.on_event("startup")
async def startup():
    global _bot_app
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        _bot_app = build_application(token)
        await _bot_app.initialize()


class ChatRequest(BaseModel):
    messages: list[dict]


class ArrivalRequest(BaseModel):
    lat: float
    lon: float


class FavoritoRequest(BaseModel):
    numero_linha: str
    codigo_linha: int
    destino: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def conversar(req: ChatRequest):
    return {"response": chat(req.messages)}


@app.get("/favoritos")
def listar():
    return listar_linhas_favoritas()


@app.post("/favoritos/proximos")
def proximos(req: ArrivalRequest):
    return buscar_favoritas_proximas(req.lat, req.lon)


@app.post("/favoritos")
def salvar(req: FavoritoRequest):
    return salvar_linha_favorita(req.numero_linha, req.codigo_linha, req.destino)


@app.delete("/favoritos/{numero_linha}")
def remover(numero_linha: str):
    return remover_linha_favorita(numero_linha)


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if not _bot_app:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not configured"}
    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)
    await _bot_app.process_update(update)
    return {"ok": True}


@app.get("/telegram/setup")
async def telegram_setup():
    if not _bot_app:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not configured"}
    base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")
    webhook_url = f"{base_url}/telegram/webhook"
    await _bot_app.bot.set_webhook(webhook_url)
    return {"ok": True, "webhook_url": webhook_url}
