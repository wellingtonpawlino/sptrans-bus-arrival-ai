import requests

def geocodificar_endereco(endereco: str) -> dict:
    headers = {"User-Agent": "sptrans-bus-arrival-ai/1.0"}
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": f"{endereco}, São Paulo, Brasil", "format": "json", "limit": 1},
        headers=headers,
        timeout=10,
    )
    if response.status_code != 200 or not response.json():
        return {"erro": f"Endereço não encontrado: {endereco}"}

    result = response.json()[0]
    return {
        "endereco_encontrado": result.get("display_name"),
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }
