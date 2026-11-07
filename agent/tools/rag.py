"""
RAG (Retrieval-Augmented Generation) com base vetorial de rotas GTFS.

Conceito:
  1. Indexação — cada rota vira um documento de texto; TF-IDF converte em vetor esparso
  2. Consulta   — a query do usuário também vira vetor; cosine similarity mede relevância
  3. Augmentação — os documentos mais relevantes são retornados para o LLM usar como contexto
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.data.gtfs_loader import carregar_rotas

_vectorizer: TfidfVectorizer | None = None
_matrix = None
_docs: list[dict] | None = None


def _build_index() -> None:
    global _vectorizer, _matrix, _docs
    if _vectorizer is not None:
        return

    rotas = carregar_rotas()
    _docs = [
        {
            "texto": f"Linha {r['nome_curto']}: {r['nome_longo']}",
            "linha": r["nome_curto"],
            "descricao": r["nome_longo"],
        }
        for r in rotas
    ]

    textos = [d["texto"] for d in _docs]
    # char_wb com ngrams captura variações de acento e abreviações (Term., Metrô, etc.)
    _vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
    _matrix = _vectorizer.fit_transform(textos)


def buscar_linhas_por_destino(destino: str, top_k: int = 5) -> dict:
    _build_index()

    query_vec = _vectorizer.transform([destino])
    scores = cosine_similarity(query_vec, _matrix).flatten()
    top_indices = np.argsort(scores)[::-1][:top_k]

    resultados = [
        {
            "linha": _docs[idx]["linha"],
            "descricao": _docs[idx]["descricao"],
            "relevancia": round(float(scores[idx]), 3),
        }
        for idx in top_indices
        if scores[idx] > 0.05
    ]

    if not resultados:
        return {"mensagem": "Nenhuma linha encontrada para esse destino", "resultados": []}

    return {"resultados": resultados}
