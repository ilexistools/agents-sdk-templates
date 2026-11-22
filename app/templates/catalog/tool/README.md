# __TITLE__

> Ferramenta `__ID__`. Resuma aqui, em uma frase, o que ela faz.

## Quando usar

- Situação em que a ferramenta resolve o problema.
- Situação em que **não** deve ser usada (e o que usar no lugar).

## Como funciona

Explique o algoritmo em poucos passos, incluindo decisões não óbvias
(por exemplo, como espaços ou pontuação são tratados).

## Entrada e saída

Os campos estão documentados em `handler.py` (`Input` e `Output`) e aparecem
no painel do catálogo. Registre aqui apenas regras que o schema não expressa.

## Exemplo

```powershell
'{"text":"um dois três"}' | uv run --locked python -m app.catalog_cli run __ID__ --input -
```

## Requisitos e limitações

- Dependências externas: nenhuma.
- Limitações conhecidas.
