# SPTrans Bus Arrival AI — Visão de Negócio

Assistente de mobilidade urbana para trabalhadores de São Paulo que dependem de ônibus no dia a dia.

---

## O problema

Quem usa ônibus em São Paulo convive com incerteza: o ônibus vai passar logo ou já passou? Quando vai chegar? Qual linha pegar para ir a determinado lugar?

A API OlhoVivo da SPTrans tem os dados — posição dos veículos e previsão de chegada em tempo real — mas exige que o usuário saiba o código da linha, navegue por telas e interprete os resultados por conta própria.

---

## A solução

Um assistente de chat que responde em linguagem natural. O usuário fala como fala com qualquer pessoa — e recebe uma resposta direta.

**Em vez de:**
> Abrir app → digitar "5178" → selecionar sentido → encontrar parada → ler horário

**O usuário pergunta:**
> "Estou na Paulista. Meu ônibus 5178 está chegando?"

**E recebe:**
> "Parada a 1,3 km de você. Ônibus chegando às 15:48. Veículo acessível."

---

## Funcionalidades

### Previsão de chegada
Informe sua localização (endereço ou bairro) e o número da linha. O assistente encontra a parada mais próxima de você e informa o horário real de chegada do próximo ônibus.

### Linhas favoritas
Salve as linhas que você usa com frequência. Da próxima vez, basta perguntar "meu ônibus está chegando?" — sem precisar informar o número de novo.

### Busca por destino
Não sabe o número da linha? Pergunte "tem ônibus para o Metrô Consolação?" e o assistente sugere as linhas mais relevantes e já busca a previsão da melhor opção.

---

## Exemplo de uso

```
Usuário:  adiciona a linha 5178 nos meus favoritos
Assistente: Linha 5178 adicionada aos favoritos!

Usuário:  meu ônibus está chegando? estou na Av. Paulista, 1000
Assistente: Ônibus 5178 — parada mais próxima a 1.360m.
            Previsão de chegada: 15:48. Veículo acessível ♿

Usuário:  tem ônibus que vai para Pinheiros? estou no Ibirapuera
Assistente: Encontrei a linha 6401 com rota para Pinheiros.
            Parada mais próxima a 820m, próximo ônibus às 16:05.
```

---

## Para quem é

- Trabalhadores que pegam ônibus todos os dias e querem saber, sem abrir vários apps, se precisam correr ou podem esperar
- Usuários que não conhecem bem os números de linha e querem buscar por destino
- Quem usa linhas acessíveis e quer confirmar antes de ir à parada

---

## Dados utilizados

| Fonte | Dados | Atualização |
|---|---|---|
| SPTrans OlhoVivo API | Posição dos veículos e previsão de chegada | Tempo real |
| GTFS SPTrans | 1.365 rotas e 22.274 paradas | Estático (atualização periódica) |
| OpenStreetMap (Nominatim) | Geocodificação de endereços | Tempo real |

Os dados de posição e previsão são fornecidos diretamente pela SPTrans via API pública. O assistente não inventa horários — se não houver dado disponível, informa ao usuário.
