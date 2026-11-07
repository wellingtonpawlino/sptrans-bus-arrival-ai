import json
from pathlib import Path

FAVORITOS_PATH = Path("favoritos.json")


def _carregar() -> list[str]:
    if not FAVORITOS_PATH.exists():
        return []
    return json.loads(FAVORITOS_PATH.read_text(encoding="utf-8"))


def salvar_linha_favorita(numero_linha: str) -> dict:
    favoritos = _carregar()
    if numero_linha in favoritos:
        return {"mensagem": f"Linha {numero_linha} já está nos favoritos"}
    favoritos.append(numero_linha)
    FAVORITOS_PATH.write_text(json.dumps(favoritos, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"mensagem": f"Linha {numero_linha} adicionada aos favoritos"}


def remover_linha_favorita(numero_linha: str) -> dict:
    favoritos = _carregar()
    if numero_linha not in favoritos:
        return {"mensagem": f"Linha {numero_linha} não está nos favoritos"}
    favoritos.remove(numero_linha)
    FAVORITOS_PATH.write_text(json.dumps(favoritos, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"mensagem": f"Linha {numero_linha} removida dos favoritos"}


def listar_linhas_favoritas() -> dict:
    favoritos = _carregar()
    if not favoritos:
        return {"favoritos": [], "mensagem": "Nenhuma linha favorita salva ainda"}
    return {"favoritos": favoritos}
