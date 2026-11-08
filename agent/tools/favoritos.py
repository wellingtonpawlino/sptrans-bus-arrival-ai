import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FAVORITOS_PATH = Path("favoritos.json")


def _carregar_todos() -> dict:
    if not FAVORITOS_PATH.exists():
        return {}
    data = json.loads(FAVORITOS_PATH.read_text(encoding="utf-8"))
    # Migração: formato antigo era lista global sem usuário
    if isinstance(data, list):
        return {"default": [f for f in data if isinstance(f, dict)]}
    return data


def _salvar_todos(dados: dict) -> None:
    FAVORITOS_PATH.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _carregar(user_id: str = "default") -> list[dict]:
    return _carregar_todos().get(str(user_id), [])


def _salvar(favoritos: list[dict], user_id: str = "default") -> None:
    todos = _carregar_todos()
    todos[str(user_id)] = favoritos
    _salvar_todos(todos)


def salvar_linha_favorita(numero_linha: str, codigo_linha: int, destino: str, user_id: str = "default") -> dict:
    favoritos = _carregar(user_id)
    if any(f["codigo_linha"] == codigo_linha for f in favoritos):
        return {"mensagem": f"Linha {numero_linha} sentido {destino} já está nos favoritos"}
    favoritos.append({"numero_linha": numero_linha, "codigo_linha": codigo_linha, "destino": destino})
    _salvar(favoritos, user_id)
    return {"mensagem": f"Linha {numero_linha} sentido {destino} adicionada aos favoritos"}


def remover_linha_favorita(numero_linha: str, user_id: str = "default") -> dict:
    favoritos = _carregar(user_id)
    novas = [f for f in favoritos if f["numero_linha"] != numero_linha]
    if len(novas) == len(favoritos):
        return {"mensagem": f"Linha {numero_linha} não está nos favoritos"}
    removidas = len(favoritos) - len(novas)
    _salvar(novas, user_id)
    return {"mensagem": f"{removidas} entrada(s) da linha {numero_linha} removida(s) dos favoritos"}


def listar_linhas_favoritas(user_id: str = "default") -> dict:
    favoritos = _carregar(user_id)
    if not favoritos:
        return {"favoritos": [], "mensagem": "Nenhuma linha favorita salva ainda"}
    return {
        "favoritos": [
            {"numero_linha": f["numero_linha"], "destino": f["destino"], "codigo_linha": f["codigo_linha"]}
            for f in favoritos
        ]
    }


def buscar_favoritas_proximas(lat: float, lon: float, user_id: str = "default") -> dict:
    from agent.tools.arrival import buscar_parada_proxima_com_previsao

    favoritos = _carregar(user_id)
    if not favoritos:
        return {"mensagem": "Nenhuma linha favorita salva", "resultados": []}

    def _buscar(fav: dict) -> dict:
        resultado = buscar_parada_proxima_com_previsao(fav["codigo_linha"], lat, lon)
        return {"numero_linha": fav["numero_linha"], "destino": fav["destino"], **resultado}

    with ThreadPoolExecutor(max_workers=5) as executor:
        resultados = list(executor.map(_buscar, favoritos))

    def _sort_key(r: dict) -> int:
        if "erro" in r:
            return 9999
        try:
            h, m = r.get("previsao_chegada", "99:99").split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return 9999

    resultados.sort(key=_sort_key)
    return {"resultados": resultados}
