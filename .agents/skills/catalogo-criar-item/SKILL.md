---
name: catalogo-criar-item
description: Criar ou alterar um agente ou ferramenta do catálogo (app/agents, app/tools) seguindo o padrão do projeto, com manifesto, contrato Pydantic, exemplos executáveis e README. Use quando o pedido for adicionar, publicar, documentar ou modificar um item exibido no painel, na API, na CLI ou no MCP do catálogo.
---

# Criar ou alterar um item do catálogo

Leia `docs/padroes-catalogo.md` inteiro antes de começar. Use como referência
`app/tools/word_count/` (ferramenta) e `app/agents/summarizer/` (agente).

## Fluxo

1. **Classifique.** Ferramenta se a tarefa cabe em código determinístico;
   agente apenas se exigir LLM. Na dúvida, prefira ferramenta.
2. **Gere o esqueleto.**
   `uv run --locked python -m app.catalog_cli new <agent|tool> <id> --title "<Título>"`
3. **Preencha o contrato** em `handler.py`: campos com `description`, restrições
   Pydantic e lógica pura (ferramenta) ou chamada a `GPTAgent` (agente).
4. **Preencha o manifesto** `item.toml`: descrição com verbo no presente
   (até 120 caracteres), `category` existente sempre que possível, `requires`,
   e exemplos realistas (com `output` em ferramentas).
5. **Agentes:** escreva `app/assets/agents/<id>.md`; a seção `# OUTPUT` reproduz
   `Output`. Para técnicas de escrita, use a skill `agents-template-criar-agente`.
6. **Documente** no `README.md` do item as seis seções do padrão.
7. **Valide** e só conclua com tudo passando:
   - `uv run --locked python -m app.catalog_cli check`
   - `uv run --locked python -m unittest app.tests.test_catalog -v`
   - `uv run --locked python -m app.catalog_cli run <id> --example 1`
     (agentes exigem `OPENAI_API_KEY`; sem ela, informe que não foi executado).

## Alterações em itens existentes

Mudou `Input` ou `Output`? Atualize exemplos, README, prompt e `version`
(major se quebrar compatibilidade). Nunca renomeie `id` de item publicado.
