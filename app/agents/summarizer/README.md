# Resumidor

> Agente `summarizer`. Resume um texto no idioma original, preservando fatos,
> conclusões e ressalvas. É o exemplo de referência para agentes baseados em LLM.

## Quando usar

- Condensar atas, e-mails, artigos ou relatórios para leitura rápida.
- **Não** use para traduzir (veja o agente `translator` em `app/assets/agents/`)
  nem quando cada número do texto precisa ser reproduzido exatamente.

## Como funciona

Um agente do catálogo tem duas partes:

| Parte | Arquivo | Responsabilidade |
|---|---|---|
| Contrato | `app/agents/summarizer/handler.py` | Define `Input` e `Output` e chama o agente |
| Comportamento | `app/assets/agents/summarizer.md` | Papel, objetivo e instruções do modelo |

Fluxo de uma execução:

1. O canal (API, CLI ou MCP) recebe `{"text": "..."}` e o catálogo verifica se o item
   está ativo nesse canal.
2. `handler.py` valida a entrada com `Input` (texto não pode ser vazio).
3. `GPTAgent(agent_id="summarizer")` lê `summarizer.md`: o frontmatter define `role`,
   `goal` e `max_tokens`, e todas as seções (`# INPUT`, `# OUTPUT`, `# INSTRUCTIONS`,
   `# KNOWLEDGE`) são concatenadas às instruções enviadas ao modelo.
4. O modelo responde com `output_type=Output`, ou seja, um JSON com `summary`.
5. O catálogo valida a resposta com `Output` antes de devolvê-la ao canal.

Para mudar **o que** o agente faz, edite o `.md`. Para mudar **o formato** da
entrada ou saída, edite `handler.py`, a seção `# OUTPUT` do `.md`, os exemplos do
`item.toml` e suba `version`.

## Exemplo

```powershell
uv run --locked python -m app.catalog_cli run summarizer --example 1
```

Saída (varia entre execuções): `{"summary": "Orçamento de 2027 aprovado com +8% em pesquisa; corte em viagens adiado para março."}`

## Requisitos e limitações

- Requer `OPENAI_API_KEY`; o modelo pode ser trocado com `OPENAI_MODEL_NAME`.
- `max_tokens: 768` limita o tamanho do resumo.
- Textos muito longos podem exceder a janela de contexto do modelo; divida-os antes.
