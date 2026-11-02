# Padrões de orquestração

Fontes: `app/orchestration/gpt_agent.py`, `gpt_agent_local.py` e
`app/tests/test_gpt_agents.py`. Confira a API do SDK instalado para opções
que os exemplos não usam.

## Sequência obrigatória

O [exemplo de extração e revisão](../assets/fluxo_sequencial.py) é um módulo
importável, sem efeitos externos na importação. `processar` aceita dois agentes
para facilitar testes com mocks. Use `criar_agentes()` quando quiser instanciar
os wrappers OpenAI configurados no ambiente.

O código chama extração, serializa o resultado e então chama revisão. Se uma
etapa falhar, a exceção interrompe o fluxo; nenhuma revisão fictícia é criada.
Em uma aplicação, trate a falha no limite do serviço ou endpoint e documente
se haverá tentativa adicional. Troque `GPTAgent` por `GPTLocalAgent` e configure
`LOCAL_*` para um provedor compatível, validando o comportamento nesse provedor.

## Handoff escolhido pelo modelo

```python
from app.orchestration.gpt_agent import GPTAgent

especialista = GPTAgent(
    name="Revisor",
    instructions="Revise o texto recebido e apresente as pendências.",
)
triagem = GPTAgent(
    name="Triagem",
    instructions="Encaminhe pedidos de revisão ao agente Revisor.",
    handoffs=[especialista],
)
```

`triagem.run(...)` pode terminar no especialista. Essa configuração não garante
que todos os pedidos passem por ele. Se a revisão for obrigatória, use uma
sequência controlada pelo código. Caso haja saídas tipadas, considere que o
agente final determina o resultado; alinhe os contratos possíveis.

## Especialista como ferramenta

```python
consulta_revisor = especialista.as_tool(
    tool_name="consultar_revisor",
    tool_description="Solicitar revisão de clareza de um texto.",
)
coordenador = GPTAgent(
    name="Coordenador",
    instructions="Consulte o revisor quando necessário e sintetize a resposta.",
    tools=[consulta_revisor],
)
```

O coordenador continua responsável pelo retorno. Verifique como o SDK serializa
a saída da ferramenta se o especialista tiver um contrato estruturado. Não
confunda esse padrão com duas chamadas Python obrigatórias.
