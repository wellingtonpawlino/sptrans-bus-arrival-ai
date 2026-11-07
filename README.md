# SPTrans Bus Arrival AI

Assistente inteligente de mobilidade urbana para São Paulo. Responde em linguagem natural quando o próximo ônibus vai chegar, usando dados em tempo real da API OlhoVivo (SPTrans) e dados estáticos GTFS.

---

## Stack

| Camada | Tecnologia |
|---|---|
| LLM | Claude Haiku 4.5 (Anthropic SDK) |
| Frontend | Streamlit |
| API de transporte | SPTrans OlhoVivo v2.1 |
| Geocodificação | Nominatim (OpenStreetMap) |
| RAG | TF-IDF + cosine similarity (scikit-learn) |
| Base vetorial | GTFS routes.txt em memória |
| Persistência | JSON local (favoritos) |

---

## Arquitetura

```
sptrans-bus-arrival-ai/
├── streamlit_app.py          # UI: chat input/output + session state
├── agent/
│   ├── assistant.py          # Loop principal: LLM → tool call → LLM
│   ├── prompts/
│   │   └── system.py         # System prompt com instruções de roteamento
│   └── tools/
│       ├── registry.py       # Definição das 9 tools + dispatcher
│       ├── arrival.py        # Parada mais próxima com previsão real
│       ├── favoritos.py      # CRUD de linhas favoritas (favoritos.json)
│       ├── geo.py            # Distância Haversine entre dois pontos
│       ├── geocoding.py      # Endereço → lat/lon via Nominatim
│       └── rag.py            # TF-IDF sobre GTFS para busca por destino
└── pipeline/
    ├── api/
    │   ├── autenticacao.py   # Sessão autenticada SPTrans OlhoVivo
    │   └── sptrans_client.py # buscar_linhas, buscar_previsao, buscar_veiculos
    └── data/
        ├── gtfs_loader.py    # Leitura de routes.txt e stops.txt
        └── gtfs/
            ├── routes.txt    # 1.365 rotas (gitignored)
            └── stops.txt     # 22.274 paradas (gitignored)
```

---

## Como o agente funciona

O loop em `agent/assistant.py` implementa o ciclo de Tool Calling do Anthropic SDK:

```
usuário → LLM decide qual tool chamar
       → ferramenta executa (API real ou dado local)
       → resultado volta ao LLM
       → LLM decide: chamar outra tool ou responder
       → resposta final ao usuário
```

O agente pode encadear múltiplas chamadas em sequência — por exemplo, para buscar previsão com endereço em texto:

```
geocodificar_endereco("Av. Paulista, 1000")
  → buscar_linhas("5178")
    → buscar_parada_proxima_com_previsao(codigo, lat, lon)
      → resposta: "Ônibus a 1.360m, chegando às 15:48"
```

---

## Ferramentas disponíveis (Tools)

| Tool | Descrição |
|---|---|
| `geocodificar_endereco` | Endereço em texto → lat/lon (Nominatim) |
| `buscar_linhas` | Número da linha → código interno SPTrans |
| `buscar_parada_proxima_com_previsao` | Parada mais próxima do usuário com ETA real |
| `buscar_veiculos_por_linha` | Posição em tempo real dos veículos (fallback) |
| `calcular_distancia` | Distância Haversine entre dois pontos |
| `salvar_linha_favorita` | Adiciona linha ao favoritos.json |
| `remover_linha_favorita` | Remove linha do favoritos.json |
| `listar_linhas_favoritas` | Lista linhas salvas |
| `buscar_linhas_por_destino` | RAG: busca linhas pelo nome do destino |

---

## RAG — busca por destino

`agent/tools/rag.py` implementa um pipeline RAG simples sobre o arquivo GTFS `routes.txt`:

1. **Indexação** — cada rota vira um documento de texto: `"Linha 5178-10: Term. Pinheiros - Metrô Brigadeiro"`
2. **Vetorização** — TF-IDF com `analyzer="char_wb"` e n-gramas de 3 a 5 caracteres (captura variações de acento e abreviações)
3. **Consulta** — query do usuário vira vetor; cosine similarity rankeia as rotas mais relevantes
4. **Augmentação** — top-5 resultados com `score > 0.05` são retornados ao LLM como contexto

O índice é construído uma vez (lazy) e mantido em memória durante a sessão.

**Limitação:** TF-IDF não captura semântica — "Consolação" e "Metrô Consolação" podem não retornar as linhas mais relevantes se o nome da rota usar outra denominação.

---

## Setup

```bash
# 1. Clone o repo
git clone https://github.com/wellingtonpawlino/sptrans-bus-arrival-ai.git
cd sptrans-bus-arrival-ai

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente
cp .env.example .env
# edite .env com suas chaves

# 4. Adicione os arquivos GTFS (gitignored)
# Baixe routes.txt e stops.txt em https://www.sptrans.com.br/desenvolvedores/
# e coloque em pipeline/data/gtfs/

# 5. Rode o app
streamlit run streamlit_app.py
```

---

## Variáveis de ambiente

```env
ANTHROPIC_API_KEY=   # console.anthropic.com → API Keys
SPTRANS_TOKEN=       # sptrans.com.br/desenvolvedores → Meu Painel
```

---

## Dependências

```
anthropic==0.40.0       # Anthropic SDK (Tool Calling)
streamlit==1.40.0       # Frontend
python-dotenv==1.0.1    # Variáveis de ambiente
requests==2.32.3        # HTTP (SPTrans API + Nominatim)
scikit-learn==1.5.2     # TF-IDF (RAG)
numpy==2.1.3            # Operações vetoriais
```

---

## Roadmap

| Fase | Conteúdo | Status |
|---|---|---|
| 1 | Chat básico com personalidade — Anthropic SDK + Streamlit | ✅ |
| 2 | Tool Calling — integração API SPTrans em tempo real | ✅ |
| 3 | Rota inteligente — parada mais próxima + previsão real | ✅ |
| 4 | Memória — favoritos persistidos entre sessões | ✅ |
| 5 | RAG — busca semântica sobre base GTFS | ✅ |
| 6 | LangGraph — agente como grafo de estados | 🔜 |
| 7 | Multiagentes — Planejador + Mobilidade + RAG + Comunicador | 🔜 |
