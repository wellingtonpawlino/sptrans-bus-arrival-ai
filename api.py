from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.assistant import chat
from agent.tools.favoritos import (
    listar_linhas_favoritas,
    buscar_favoritas_proximas,
    salvar_linha_favorita,
    remover_linha_favorita,
)

app = FastAPI(title="SPTrans Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
