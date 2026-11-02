# Decisions na aplicação

Leia `app/orchestration/gpt_decision.py`, `app/examples/decisions.py` e o
[guia de Decisions](../../../../docs/decisions.md). Reutilize o wrapper para
probabilidades de condições, categorias fixas e scores de rubrica. Para
extração de campos, justificativas livres ou ferramentas, use os demais wrappers.

`OPENAI_DECISION_MODEL_NAME` é independente do modelo dos especialistas.
Consulte o suporte atual do provedor antes de alterá-lo. Esta integração é
OpenAI; não pressuponha suporte em um endpoint Chat Completions compatível.

Cada pergunta precisa de `name` único, `instructions` e `type` apropriado;
choices e níveis pertencem ao contrato da pergunta. A validação local do
wrapper não substitui o schema da API. Use os tipos do SDK instalado.

O retorno preserva `answers`, `model` e `usage`. Trate recusas por pergunta
sem perder as demais respostas. Predicados têm `probability`; escolhas e
scores têm `confidence` e distribuições, com semânticas distintas. Não transforme
um score fracionário em categoria por arredondamento sem uma regra da aplicação.

Os clientes são lazy e injetáveis. Gerencie-os por contexto ou pelo ciclo de
vida do serviço; a construção do wrapper não prova acesso ao modelo.
Os argumentos extras de `run`/`run_sync` vão para `decisions.create`, não para
`Runner.run`. Não passe `agent_id`, `output_type`, `tools` ou `max_tokens`.

Para endpoints, serialize o objeto SDK ou defina explicitamente o contrato da
aplicação. Teste com transportes HTTP simulados; registre separadamente acesso
real e calibração com dados rotulados. Execute as verificações existentes com:

```bash
uv run --locked python -m unittest app.tests.test_gpt_decision -v
```
