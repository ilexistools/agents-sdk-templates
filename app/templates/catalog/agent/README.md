# __TITLE__

> Agente `__ID__`. Resuma aqui, em uma frase, o que ele faz.

## Quando usar

- Situação em que o agente resolve o problema.
- Situação em que **não** deve ser usado (e o que usar no lugar).

## Como funciona

1. `handler.py` valida a entrada (`Input`).
2. `GPTAgent` carrega o prompt de `app/assets/agents/__ID__.md`.
3. O modelo responde no formato `Output`, validado antes de ser devolvido.

Explique aqui as decisões do prompt que não são óbvias.

## Entrada e saída

Os campos estão documentados em `handler.py` e aparecem no painel do catálogo.

## Exemplo

```powershell
'{"text":"Texto de exemplo."}' | uv run --locked python -m app.catalog_cli run __ID__ --input -
```

## Requisitos e limitações

- Requer `OPENAI_API_KEY` (modelo opcional em `OPENAI_MODEL_NAME`).
- Respostas de LLM variam entre execuções; não use para cálculos exatos.
