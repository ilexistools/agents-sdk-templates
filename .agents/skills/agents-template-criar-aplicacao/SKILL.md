---
name: agents-template-criar-aplicacao
description: Implementar funcionalidades Python, serviços ou endpoints FastAPI usando os wrappers deste projeto, com OpenAI, Decisions, modelos locais ou DeepSeek. Use para integrar chamadas de modelos a uma aplicação; não para um pedido restrito à redação de uma definição Markdown.
---

# Criar aplicações com os wrappers

Leia `pyproject.toml`, `app/main.py`, `app/orchestration/config.py` e o wrapper
necessário. Trabalhe na raiz do projeto e execute módulos a partir dela.
Reutilize a estrutura existente, sem criar uma camada genérica de provedores
ou alterar wrappers quando a configuração existente resolve o pedido.

## Escolher a integração

| Necessidade | Wrapper |
|---|---|
| OpenAI Responses API, saída tipada | `GPT` |
| Probabilidade, categoria fixa ou score de rubrica | `GPTDecision` |
| OpenAI com ferramentas e handoffs | `GPTAgent` |
| Execução em sandbox e skills de execução | `GPTSandboxAgent` |
| Chat Completions local ou remoto compatível | `GPTLocal` |
| Agents SDK com Chat Completions compatível | `GPTLocalAgent` |

Leia [provedores e configuração](references/provedores.md) para configurar a
conexão escolhida. Leia [integração FastAPI](references/fastapi.md) se houver
endpoint HTTP. Para configuração avançada, confira a assinatura do SDK
instalado; os wrappers aceitam `**kwargs`, mas não encaminham qualquer opção.

Para Decisions, leia [decisões e triagem](references/decisions.md). Esse wrapper
recebe perguntas diretamente, não usa `agent_id`/`output_type` e devolve o objeto
SDK `Decision` inteiro, em vez do conteúdo final dos wrappers de agentes.

## Implementar

- Defina modelos Pydantic de entrada e saída adequados à funcionalidade.
  Passe o modelo de saída em `output_type`; uma descrição no prompt não
  substitui o contrato Python.
- Com `agent_id`, o frontmatter define `model` e `max_tokens`, ignorando
  argumentos homônimos. Se o modelo for configurável por ambiente, omita
  `model` do Markdown. Consulte `load_agent_config` para a precedência atual.
- Em FastAPI e outras funções assíncronas, use `await wrapper.run(prompt)`.
  Os wrappers de agentes retornam o conteúdo final, não o `RunResult` do SDK.
  `GPTDecision.run(...)` exige `questions` e retorna `Decision`.
- Em `GPTLocal` e `GPTLocalAgent`, a saída estruturada depende de instruções
  e parsing; não prometa JSON Schema garantido pelo servidor.
- Mantenha chaves em variáveis de ambiente e acrescente apenas placeholders
  ao `env-example`. Configure o tracing de acordo com o provedor.
- Para falhas do provedor, preserve a causa nos logs sem expor credenciais.
  Ao mapear erros HTTP, diferencie entrada inválida de falha do serviço.

## Concluir

Sincronize com `uv sync --locked`. Valide imports, construção dos wrappers e
contratos/endpoints com respostas simuladas. Use os exemplos de `app/tests`
como demonstrações: vários executam chamadas reais quando iniciados como
módulos, e não são testes automatizados de API.

Rode testes existentes pertinentes. Documente configuração, execução,
contratos e limites; distinga o que foi verificado offline de chamadas reais.
As referências fornecem exemplos adaptáveis, não alteram o provedor escolhido
pelo usuário nem autorizam publicação da aplicação.
