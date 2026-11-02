---
name: agents-template-integrar-ferramentas
description: Integrar funções Python, servidores MCP 2 ou capacidades de sandbox aos agentes deste projeto. Use para implementar ferramentas, conectar MCP ou disponibilizar arquivos e skills em sandbox, preservando os contratos e o ciclo de conexão dos wrappers.
---

# Integrar ferramentas e sandbox

Leia o wrapper escolhido e, para MCP, `app/mcp_tools/server.py` e seus testes.
Escolha apenas a referência necessária:

- [Funções Python](references/funcoes.md): ferramenta executada pela aplicação.
- [MCP 2](references/mcp.md): servidor externo ou ferramentas compartilhadas.
- [Sandbox](references/sandbox.md): arquivos, execução isolada e skills em runtime.

## Integração no projeto

`GPTAgent`, `GPTLocalAgent` e `GPTSandboxAgent` aceitam `tools` e servidores
MCP. `GPT` e `GPTLocal` são wrappers de chamadas diretas e não encaminham esses
parâmetros. Não conclua que um argumento funciona apenas porque o construtor
aceita `**kwargs`; confira seu encaminhamento no código.

Mantenha a função de negócio testável fora do adaptador da ferramenta. Defina
tipos, parâmetros obrigatórios e resultado; passe erros de forma que o agente
possa distingui-los de resultados válidos. Para ações que mudam dados externos,
preserve a autorização e o escopo do usuário na ferramenta implementada.

## Validação

Teste funções localmente. Em MCP, verifique descoberta e chamada de ferramenta
pelo cliente, além da construção do servidor. O teste existente pode ser rodado
com `uv run --locked python -m unittest app.tests.test_mcp_server -v`.

Para sandbox, instanciar o agente não prova que o backend executa nem que a
skill foi usada. Registre separadamente testes de configuração, execução do
backend e evidência de uso da skill, conforme o ambiente disponível.

Documente transportes, endpoints, variáveis, dependências opcionais e como
executar a integração. Não instale backends ou crie serviços externos quando
a tarefa for apenas fornecer a configuração ou um exemplo.
