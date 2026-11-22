# Instruções para assistentes de IA

## Catálogo de agentes e ferramentas

Ao criar ou alterar qualquer item em `app/agents/` ou `app/tools/`, siga
[docs/padroes-catalogo.md](docs/padroes-catalogo.md). Resumo obrigatório:

1. Crie itens novos com o gerador, nunca copiando pastas à mão:
   `uv run --locked python -m app.catalog_cli new <agent|tool> <id> --title "<Título>"`.
2. Cada item tem `item.toml`, `handler.py` e `README.md`; agentes também têm
   `app/assets/agents/<id>.md`.
3. `handler.py` expõe apenas `Input`, `Output` e `async def run(request: Input) -> Output`;
   todo campo tem `Field(description=...)`.
4. `item.toml` tem pelo menos um `[[examples]]`; ferramentas incluem `output` esperado.
5. Ao mudar `Input`/`Output`, atualize exemplos, README, a seção `# OUTPUT` do prompt
   (agentes) e suba `version` (SemVer).
6. Antes de concluir, rode e deixe passando:
   - `uv run --locked python -m app.catalog_cli check`
   - `uv run --locked python -m unittest app.tests.test_catalog -v`

Não altere `app/catalog*.py` ou `app/catalog.html` para acomodar um item
específico: se o padrão não comporta o caso, proponha a mudança no padrão.
