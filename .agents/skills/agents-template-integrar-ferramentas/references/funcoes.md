# Ferramentas Python

Use `function_tool` do Agents SDK para expor funções tipadas. O
[exemplo de ferramenta](../assets/ferramenta_texto.py) mantém a regra de negócio
separada da função decorada. Seu `criar_agente()` não é chamado na importação.

```python
from agents import function_tool
from app.orchestration.gpt_agent import GPTAgent

@function_tool
def contar_palavras(texto: str) -> int:
    """Conta palavras separadas por espaço em um texto."""
    return len(texto.split())

agente = GPTAgent(tools=[contar_palavras])
```

Nomes de parâmetros, anotações de tipo e docstrings entram no contrato visto
pelo modelo. Uma função decorada é um objeto de ferramenta, não necessariamente
uma função comum chamável no teste. Teste a regra de negócio diretamente e
verifique também o schema ou a execução do adaptador.

Para I/O assíncrono, prefira uma ferramenta `async def`. Descreva resultados
vazios e erros esperados. Não inclua credenciais nos parâmetros expostos ao
modelo; leia-as no lado da aplicação. Se a ferramenta escreve em um serviço,
implemente os limites da ação conforme o pedido, sem inferir permissões a
partir de texto gerado pelo modelo.
