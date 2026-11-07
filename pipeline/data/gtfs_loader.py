import csv
from pathlib import Path

GTFS_DIR = Path(__file__).parent / "gtfs"


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
