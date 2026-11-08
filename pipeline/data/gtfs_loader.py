import csv
import json
from pathlib import Path

GTFS_DIR = Path(__file__).parent / "gtfs"
ROUTE_STOPS_JSON = Path(__file__).parent / "route_stops.json"


def carregar_rotas() -> list[dict]:
    path = GTFS_DIR / "routes.txt"
    rotas = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rotas.append({
                "route_id": row["route_id"].strip('"'),
                "nome_curto": row["route_short_name"].strip('"'),
                "nome_longo": row["route_long_name"].strip('"'),
            })
    return rotas


def carregar_paradas() -> list[dict]:
    path = GTFS_DIR / "stops.txt"
    paradas = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paradas.append({
                "stop_id": row["stop_id"].strip('"'),
                "nome": row["stop_name"].strip('"'),
                "lat": float(row["stop_lat"]),
                "lon": float(row["stop_lon"]),
            })
    return paradas


def carregar_paradas_por_rota() -> dict[str, list[str]]:
    """Retorna {route_id: [stop_name, ...]} via três fontes em ordem de prioridade:
      1. route_stops.json  — índice pré-computado (gerado por preprocess_stops.py)
      2. trips.txt + stop_times.txt — arquivos GTFS completos
      3. {}  — fallback silencioso se nenhuma fonte estiver disponível
    """
    # Prioridade 1: JSON pré-computado (pequeno, comitável no repo)
    if ROUTE_STOPS_JSON.exists():
        with open(ROUTE_STOPS_JSON, encoding="utf-8") as f:
            return json.load(f)

    # Prioridade 2: arquivos GTFS brutos (pesados, não comitados)
    trips_path = GTFS_DIR / "trips.txt"
    stop_times_path = GTFS_DIR / "stop_times.txt"

    if not trips_path.exists() or not stop_times_path.exists():
        return {}

    # trip_id → route_id
    trip_to_route: dict[str, str] = {}
    with open(trips_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            trip_to_route[row["trip_id"].strip('"')] = row["route_id"].strip('"')

    # stop_id → stop_name
    stop_names: dict[str, str] = {}
    for p in carregar_paradas():
        stop_names[p["stop_id"]] = p["nome"]

    # route_id → set de nomes de paradas (sem duplicatas)
    paradas_por_rota: dict[str, set] = {}
    with open(stop_times_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            trip_id = row["trip_id"].strip('"')
            stop_id = row["stop_id"].strip('"')
            route_id = trip_to_route.get(trip_id)
            if route_id and stop_id in stop_names:
                paradas_por_rota.setdefault(route_id, set()).add(stop_names[stop_id])

    return {route_id: list(nomes) for route_id, nomes in paradas_por_rota.items()}
