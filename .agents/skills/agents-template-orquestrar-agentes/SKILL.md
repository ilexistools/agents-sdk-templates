---
name: agents-template-orquestrar-agentes
description: Implementar fluxos com vários agentes deste template, escolhendo entre etapas sequenciais, handoffs e agentes como ferramentas, com contratos e tratamento de falhas. Use quando mais de um agente participar do processamento de uma solicitação.
---

# Orquestrar agentes do projeto

Leia os wrappers envolvidos, `app/orchestration/util.py` e as definições dos
agentes reutilizados. Use [padrões e exemplo executável](references/padroes.md)
para escolher o fluxo antes de implementar.

## Escolha do fluxo

- Use uma sequência Python com `await` quando todas as etapas forem obrigatórias,
  houver ordem definida ou o código precisar validar cada resultado.
- Use `handoffs=[especialista]` quando o modelo precisar transferir a condução
  da conversa. Um handoff não agenda automaticamente uma revisão posterior.
- Use `especialista.as_tool(...)` quando um coordenador precisar consultar
  outro agente e continuar responsável pelo resultado. Confira a assinatura
  instalada; esse método vem da classe `Agent` herdada.
- Use concorrência apenas para tarefas independentes. Os métodos `run()` com
  `mcp_url` modificam `self.mcp_servers`; não compartilhe a mesma instância
  entre execuções concorrentes que abrem essas conexões.

## Contratos e integração

Defina entradas e saídas de cada etapa, a condição de término e o responsável
pelo resultado final. Serialize modelos Pydantic com `model_dump_json()` para
o prompt seguinte; o resultado dos wrappers já é o conteúdo final.

Com `agent_id`, confira o `model` do frontmatter de cada especialista: ele
prevalece sobre o ambiente e o argumento homônimo do construtor. Configure
todos para o provedor correto, inclusive os destinos de handoff.

Os wrappers `GPT` e `GPTLocal` não herdam `Agent`; não os passe diretamente a
`handoffs` ou use `as_tool` neles. Ferramentas/handoffs com provedores compatíveis
precisam de validação por modelo, em especial quando houver raciocínio.

## Verificar e entregar

Teste a ordem das etapas, os dados transmitidos e a interrupção em caso de
erro com `AsyncMock` ou agentes falsos. Não invente uma resposta bem-sucedida
para esconder falhas nem adicione repetição sem limite.

Em handoffs, separe testes da configuração de evidências de que o modelo
realmente transferiu a conversa. Em um fluxo completo, documente execução,
contratos, falhas e quais partes dependeram de chamadas reais.
