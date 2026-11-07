import os
import requests

_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = _autenticar()
    return _session


def _autenticar() -> requests.Session:
    token = os.getenv("SPTRANS_TOKEN")
    if not token:
        raise RuntimeError("SPTRANS_TOKEN não definido no .env")

    session = requests.Session()
    url = f"https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar?token={token}"
    response = session.post(url)

    if response.status_code == 200 and response.text.lower() == "true":
        return session

    raise RuntimeError(f"Falha na autenticação SPTrans: {response.status_code} - {response.text}")
