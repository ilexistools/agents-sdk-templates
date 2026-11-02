# MCP 2 no template

O servidor atual importa `MCPServer` de `mcp.server.mcpserver`. Não gere código
com o antigo `mcp.server.fastmcp.FastMCP`. Registre funções com `@mcp.tool()`;
host, porta e opções HTTP pertencem a `run()`, não ao construtor.

Execute da raiz, em um processo separado:

```bash
uv run --locked python -m app.mcp_tools.server --transport streamable-http
```

O endpoint é `http://localhost:8000/mcp`. O exemplo FastAPI também usa a porta
8000, portanto altere a porta de um deles se ambos precisarem executar juntos.

## Cliente gerenciado pelo wrapper

```python
from app.orchestration.gpt_agent import GPTAgent

agente = GPTAgent(
    name="Assistente com MCP",
    instructions="Use as ferramentas disponíveis para analisar o texto.",
    mcp_url="http://localhost:8000/mcp",
    mcp_timeout=30,
)
```

`run()` abre e fecha `MCPServerStreamableHttp` com um context manager.
`mcp_headers` permite autenticação; obtenha valores de ambiente, sem gravar
tokens no código. O wrapper substitui `self.mcp_servers` pela conexão criada,
portanto não combine `mcp_url` com uma lista esperando preservar ambos.

Para múltiplos servidores, SSE ou stdio, gerencie os contextos no chamador e
passe os objetos conectados em `mcp_servers=[...]`, sem `mcp_url`. Mantenha os
contextos abertos até a conclusão de `await agente.run(...)`; não devolva um
agente dependente de uma conexão que já foi fechada.

O servidor oferece também `--transport sse` (endpoint padrão `/sse`) e
`--transport stdio`. No stdio não passe opções HTTP e não use stdout para logs
de aplicação. `app/tests/test_mcp_server.py` demonstra descoberta e chamada
via stdio com `MCPServerStdio` e requisições HTTP ao servidor sem modelo pago.

Um GET de navegador sem os cabeçalhos MCP pode falhar mesmo com o servidor
saudável. Valide com um cliente MCP e uma chamada de ferramenta.
