from pipeline.api.autenticacao import get_session

BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"


def buscar_linhas(termo: str) -> list[dict]:
    session = get_session()
    response = session.get(f"{BASE_URL}/Linha/Buscar", params={"termosBusca": termo})
    if response.status_code != 200:
        return []

    linhas = response.json() or []
    return [
        {
            "codigo_linha": l["cl"],
            "letreiro": l["lt"],
            "origem": l["tp"],
            "destino": l["ts"],
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
