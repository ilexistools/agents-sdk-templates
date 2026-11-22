# Contador de palavras

> Ferramenta `word_count`. Conta palavras e caracteres (sem espaços) de um texto.
> Funciona offline e é o exemplo de referência para ferramentas determinísticas.

## Quando usar

- Medir o tamanho de um texto antes de enviá-lo a um modelo ou formulário.
- **Não** use para contar tokens de LLM: tokens não correspondem a palavras.

## Como funciona

1. `handler.py` valida a entrada (`Input.text`).
2. `count_words` (em `app/mcp_tools/tools.py`) divide o texto com `str.split()`,
   que trata qualquer sequência de espaços, tabulações ou quebras de linha como um separador.
3. `word_count` é o número de partes; `character_count` é a soma do tamanho de cada parte,
   portanto espaços não entram na conta. Pontuação colada à palavra conta como caractere.

A lógica fica numa função pura, fora do handler, para poder ser testada e
reaproveitada por outros servidores (por exemplo, `app/mcp_tools/server.py`).

## Exemplo

```powershell
uv run --locked python -m app.catalog_cli run word_count --example 1
'{"text":"um dois três"}' | uv run --locked python -m app.catalog_cli run word_count --input -
```

Saída: `{"word_count": 3, "character_count": 10}`.

## Requisitos e limitações

- Nenhuma dependência externa nem chave de API.
- Não reconhece palavras unidas por hífen ou pontuação sem espaço como palavras separadas.
