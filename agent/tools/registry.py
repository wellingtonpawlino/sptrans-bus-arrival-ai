import json
from pipeline.api.sptrans_client import buscar_linhas, buscar_veiculos_por_linha
from agent.tools.geo import calcular_distancia
from agent.tools.geocoding import geocodificar_endereco
from agent.tools.arrival import buscar_parada_proxima_com_previsao
from agent.tools.favoritos import (
    salvar_linha_favorita,
    remover_linha_favorita,
    listar_linhas_favoritas,
    buscar_favoritas_proximas,
)
from agent.tools.rag import buscar_linhas_por_destino

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
    {
        "name": "salvar_linha_favorita",
        "description": "Salva uma linha de ônibus com sentido específico nos favoritos do usuário. Sempre chame buscar_linhas antes para obter o codigo_linha e destino corretos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "numero_linha": {
                    "type": "string",
                    "description": "Número da linha. Ex: '5178', '8012'",
                },
                "codigo_linha": {
                    "type": "integer",
                    "description": "Código identificador único da linha por sentido, obtido via buscar_linhas",
                },
                "destino": {
                    "type": "string",
                    "description": "Terminal de destino da linha neste sentido, obtido via buscar_linhas. Ex: 'TERMINAL LAPA', 'PCA.RAMOS DE AZEVEDO'",
                },
            },
            "required": ["numero_linha", "codigo_linha", "destino"],
        },
    },
    {
        "name": "remover_linha_favorita",
        "description": "Remove uma linha de ônibus dos favoritos do usuário.",
        "input_schema": {
            "type": "object",
            "properties": {
                "numero_linha": {
                    "type": "string",
                    "description": "Número da linha a remover. Ex: '5178'",
                }
            },
            "required": ["numero_linha"],
        },
    },
    {
        "name": "listar_linhas_favoritas",
        "description": "Lista todas as linhas de ônibus salvas nos favoritos do usuário.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "buscar_favoritas_proximas",
        "description": "Busca previsão de chegada de todas as linhas favoritas do usuário em paralelo e retorna um ranking por horário de chegada. Use quando o usuário perguntar 'meu ônibus está chegando?' e tiver favoritos salvos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lat": {
                    "type": "number",
                    "description": "Latitude do usuário, obtida via geocodificar_endereco",
                },
                "lon": {
                    "type": "number",
                    "description": "Longitude do usuário, obtida via geocodificar_endereco",
                },
            },
            "required": ["lat", "lon"],
        },
    },
    {
        "name": "buscar_linhas_por_destino",
        "description": "Busca linhas de ônibus na base estática GTFS pelo nome do destino ou trecho. Use quando o usuário não sabe o número da linha e pergunta 'tem ônibus que vai para X?' ou 'qual linha passa pela Y?'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "destino": {
                    "type": "string",
                    "description": "Nome do destino, bairro ou ponto de referência. Ex: 'Paulista', 'Metrô Consolação', 'Pinheiros'",
                }
            },
            "required": ["destino"],
        },
    },
]


_TOOL_NAMES = {t["name"]: t for t in TOOLS}

MOBILITY_TOOLS = [_TOOL_NAMES[n] for n in [
    "geocodificar_endereco", "buscar_linhas", "buscar_parada_proxima_com_previsao",
    "buscar_veiculos_por_linha", "calcular_distancia", "buscar_favoritas_proximas",
    "listar_linhas_favoritas",
]]

FAVORITES_TOOLS = [_TOOL_NAMES[n] for n in [
    "buscar_linhas", "salvar_linha_favorita", "remover_linha_favorita", "listar_linhas_favoritas",
]]

DISCOVERY_TOOLS = [_TOOL_NAMES[n] for n in [
    "buscar_linhas_por_destino", "geocodificar_endereco", "buscar_parada_proxima_com_previsao",
]]


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
    elif nome == "salvar_linha_favorita":
        resultado = salvar_linha_favorita(args["numero_linha"], args["codigo_linha"], args["destino"])
    elif nome == "buscar_favoritas_proximas":
        resultado = buscar_favoritas_proximas(args["lat"], args["lon"])
    elif nome == "remover_linha_favorita":
        resultado = remover_linha_favorita(args["numero_linha"])
    elif nome == "listar_linhas_favoritas":
        resultado = listar_linhas_favoritas()
    elif nome == "buscar_linhas_por_destino":
        resultado = buscar_linhas_por_destino(args["destino"])
    else:
        resultado = {"erro": f"Ferramenta desconhecida: {nome}"}

    return json.dumps(resultado, ensure_ascii=False)
