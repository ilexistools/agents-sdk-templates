---
name: agents-template-criar-agente
description: Criar ou revisar definições Markdown de agentes deste template, com contrato Pydantic e código de carregamento compatíveis com app/orchestration. Use para transformar uma necessidade em um agente executável; fluxos entre vários agentes pertencem à skill de orquestração.
---

# Criar um agente com o template

Trabalhe na raiz do repositório que contém `pyproject.toml` e `app/orchestration`.
Leia `app/orchestration/util.py`, o wrapper escolhido e uma definição existente
antes de gerar arquivos. O código atual prevalece sobre os exemplos desta skill.

## Entrega

Produza `app/assets/agents/<agent_id>.md`, o contrato Python de saída quando
necessário e um exemplo de carregamento. Adapte um agente existente quando ele
já atende à finalidade; preserve o provedor e o modelo solicitados.

Use [o contrato e o exemplo de definição](references/definicoes.md) para escrever
o Markdown. A skill de execução `app/assets/skills/agent_description_writer/SKILL.md`
também contém orientações de redação; esta skill acrescenta integração Python,
configuração de provedor e validação do carregamento.

## Decisões específicas do projeto

- Escolha `GPT` para Responses API da OpenAI, `GPTAgent` para ferramentas e
  handoffs, `GPTSandboxAgent` para execução em sandbox, `GPTLocal` ou
  `GPTLocalAgent` para Chat Completions local ou de um provedor compatível.
- O nome do arquivo determina a busca por `agent_id`; mantenha o campo `id`
  igual ao nome do arquivo sem `.md`.
- Com `agent_id`, nome, papel, instruções, modelo e limite de tokens vêm do
  Markdown. Os argumentos `model` e `max_tokens` não substituem esses campos.
  Omita `model` no frontmatter para usar o fallback do wrapper/provedor.
- As seções do Markdown viram instruções de texto. Declarar uma classe em
  `OUTPUT` não cria um modelo Python: defina a classe e passe `output_type`.
- `max_tokens` ausente assume 2048; não deixe o campo vazio, pois o loader
  converte seu valor com `int(...)`.
- O nome padrão vem do identificador; o frontmatter pode usar `name`.
- Use `await agent.run(...)` em código assíncrono. O retorno já é o resultado
  final; o atributo `final_output` só existe se fizer parte do contrato retornado.

## Verificação e documentação

Execute o validador a partir da raiz:

```bash
uv run --locked python .agents/skills/agents-template-criar-agente/scripts/validar_agente.py app/assets/agents/relatorio_revisor.md
```

Substitua o caminho pelo arquivo criado. O validador usa o loader real, sem
chamar modelos. Depois instancie o wrapper e verifique o contrato com dados
representativos. Para OpenAI, um cliente pode exigir uma chave mesmo sem
chamada: use uma chave fictícia somente no teste isolado, sem alterar `.env`.
Documente como executar e quais verificações foram locais ou com mocks.
Não apresente a validação estrutural como prova da qualidade das respostas.
