import json
from pipeline.api.sptrans_client import buscar_linhas, buscar_veiculos_por_linha
from agent.tools.geo import calcular_distancia
from agent.tools.geocoding import geocodificar_endereco
from agent.tools.arrival import buscar_parada_proxima_com_previsao

TOOLS = [
    {
        "name": "geocodificar_endereco",
        "description": "Converte um endereço em coordenadas geográficas (latitude e longitude). Use sempre que o usuário informar sua localização por texto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "endereco": {
                    "type": "string",
                    "description": "Endereço completo ou parcial. Ex: 'Av. Paulista, 1000', 'Metrô Vila Madalena', 'Rua Augusta'",
                }
            },
            "required": ["endereco"],
        },
    },
    {
        "name": "buscar_linhas",
        "description": "Busca linhas de ônibus pelo número. Retorna o código identificador necessário para as demais ferramentas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "termo": {
                    "type": "string",
                    "description": "Número da linha. Ex: '5178', '8012'",
                }
            },
            "required": ["termo"],
        },
    },
    {
        "name": "buscar_parada_proxima_com_previsao",
        "description": "Encontra a parada mais próxima do usuário com previsão real de chegada do ônibus. Use esta ferramenta como principal para responder 'meu ônibus está chegando?'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo_linha": {
                    "type": "integer",
                    "description": "Código numérico da linha, obtido via buscar_linhas",
                },
                "lat": {
                    "type": "number",
                    "description": "Latitude do usuário, obtida via geocodificar_endereco",
                },
                "lon": {
                    "type": "number",
                    "description": "Longitude do usuário, obtida via geocodificar_endereco",
                },
            },
            "required": ["codigo_linha", "lat", "lon"],
        },
    },
    {
        "name": "buscar_veiculos_por_linha",
        "description": "Retorna a posição em tempo real dos veículos de uma linha. Use como fallback se buscar_parada_proxima_com_previsao não retornar resultados.",
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo_linha": {
                    "type": "integer",
                    "description": "Código numérico da linha, obtido via buscar_linhas",
                }
            },
            "required": ["codigo_linha"],
        },
    },
    {
        "name": "calcular_distancia",
        "description": "Calcula a distância em metros entre dois pontos geográficos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat1": {"type": "number", "description": "Latitude do ponto de origem"},
                "lon1": {"type": "number", "description": "Longitude do ponto de origem"},
                "lat2": {"type": "number", "description": "Latitude do ponto de destino"},
                "lon2": {"type": "number", "description": "Longitude do ponto de destino"},
            },
            "required": ["lat1", "lon1", "lat2", "lon2"],
        },
    },
]


def executar_ferramenta(nome: str, args: dict) -> str:
    if nome == "geocodificar_endereco":
        resultado = geocodificar_endereco(args["endereco"])
    elif nome == "buscar_linhas":
        resultado = buscar_linhas(args["termo"])
    elif nome == "buscar_parada_proxima_com_previsao":
        resultado = buscar_parada_proxima_com_previsao(
            args["codigo_linha"], args["lat"], args["lon"]
        )
    elif nome == "buscar_veiculos_por_linha":
        resultado = buscar_veiculos_por_linha(args["codigo_linha"])
    elif nome == "calcular_distancia":
        resultado = calcular_distancia(args["lat1"], args["lon1"], args["lat2"], args["lon2"])
    else:
        resultado = {"erro": f"Ferramenta desconhecida: {nome}"}

    return json.dumps(resultado, ensure_ascii=False)
