# Word counter

> Tool `word_count`. Counts the words and non-whitespace characters in a text.
> It runs offline and is the reference example for deterministic tools.

## When to use

- Measuring the size of a text before sending it to a model or a form.
- **Do not** use it to count LLM tokens: tokens do not map to words.

## How it works

1. `handler.py` validates the input (`Input.text`).
2. `count_words` (in `app/mcp_tools/tools.py`) splits the text with `str.split()`,
   which treats any run of spaces, tabs or line breaks as one separator.
3. `word_count` is the number of parts; `character_count` is the sum of their
   lengths, so whitespace is not counted. Punctuation attached to a word counts as a character.

The logic lives in a pure function outside the handler so it can be tested and
reused by other servers (for example, `app/mcp_tools/server.py`).

## Example

```powershell
uv run --locked python -m app.catalog_cli run word_count --example 1
'{"text":"one two three"}' | uv run --locked python -m app.catalog_cli run word_count --input -
```

Output: `{"word_count": 3, "character_count": 11}`.

## Requirements and limitations

- No external dependencies and no API key.
- Words joined by hyphens or punctuation without spaces count as a single word.
