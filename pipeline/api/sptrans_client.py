from pipeline.api.autenticacao import get_session

BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"


def buscar_linhas(termo: str) -> list[dict]:
    session = get_session()
    response = session.get(f"{BASE_URL}/Linha/Buscar", params={"termosBusca": termo})
    if response.status_code != 200:
        return []

    linhas = response.json() or []

    # Se o termo tiver sufixo de tipo (ex: "5119-10"), filtra pelo tl correspondente
    tl_filtro = None
    if "-" in termo:
        partes = termo.rsplit("-", 1)
        if partes[1].isdigit():
            tl_filtro = int(partes[1])

    if tl_filtro is not None:
        linhas = [l for l in linhas if l.get("tl") == tl_filtro]

    return [
        {
            "codigo_linha": l["cl"],
            "letreiro": l["lt"],
            # sl=1: tp→ts, sl=2: ts→tp
            "origem": l["tp"] if l["sl"] == 1 else l["ts"],
            "destino": l["ts"] if l["sl"] == 1 else l["tp"],
            "sentido": l["sl"],
        }
        for l in linhas
    ]


def buscar_previsao_por_linha(codigo_linha: int) -> list[dict]:
    session = get_session()
    response = session.get(f"{BASE_URL}/Previsao/Linha", params={"codigoLinha": codigo_linha})
    if response.status_code != 200:
        return []

    dados = response.json()
    if not dados:
        return []

    return [
        {
            "codigo_parada": p.get("cp"),
            "nome_parada": p.get("np"),
            "latitude": p.get("py"),
            "longitude": p.get("px"),
            "veiculos": [
                {
                    "prefixo": v.get("p"),
                    "previsao_chegada": v.get("t"),
                    "acessivel": v.get("a"),
                }
                for v in p.get("vs", [])
            ],
        }
        for p in dados.get("ps", [])
    ]


def buscar_veiculos_por_linha(codigo_linha: int) -> list[dict]:
    session = get_session()
    response = session.get(f"{BASE_URL}/Posicao/Linha", params={"codigoLinha": codigo_linha})
    if response.status_code != 200:
        return []

    dados = response.json()
    if not dados:
        return []

    return [
        {
            "prefixo": v.get("p"),
            "latitude": v.get("py"),
            "longitude": v.get("px"),
            "acessivel": v.get("a"),
            "horario_atualizacao": v.get("ta"),
        }
        for v in dados.get("vs", [])
    ]
