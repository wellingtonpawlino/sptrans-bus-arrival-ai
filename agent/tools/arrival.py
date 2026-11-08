import math
from pipeline.api.sptrans_client import buscar_previsao_por_linha


def buscar_parada_proxima_com_previsao(codigo_linha: int, lat: float, lon: float) -> dict:
    paradas = buscar_previsao_por_linha(codigo_linha)

    if not paradas:
        return {"erro": "Nenhuma previsão disponível para esta linha no momento"}

    melhor = None
    melhor_distancia = float("inf")

    for parada in paradas:
        if not parada["veiculos"]:
            continue

        R = 6371000
        phi1, phi2 = math.radians(lat), math.radians(parada["latitude"])
        dphi = math.radians(parada["latitude"] - lat)
        dlambda = math.radians(parada["longitude"] - lon)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        distancia = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        if distancia < melhor_distancia:
            melhor_distancia = distancia
            melhor = parada

    if not melhor:
        return {"erro": "Nenhum veículo com previsão encontrado para esta linha"}

    veiculo = melhor["veiculos"][0]
    return {
        "parada": melhor["nome_parada"],
        "parada_lat": melhor["latitude"],
        "parada_lon": melhor["longitude"],
        "distancia_metros_ate_parada": round(melhor_distancia),
        "previsao_chegada": veiculo["previsao_chegada"],
        "prefixo_veiculo": veiculo["prefixo"],
        "acessivel": veiculo["acessivel"],
    }
