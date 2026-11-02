"""A pure function and its Agents SDK adapter, without live calls on import."""

from agents import function_tool

from app.orchestration.gpt_agent import GPTAgent


def contar_palavras(texto: str) -> int:
    return len(texto.split())


@function_tool
def contar_palavras_tool(texto: str) -> int:
    """Conta palavras separadas por espaços ou quebras de linha no texto."""
    return contar_palavras(texto)


def criar_agente() -> GPTAgent:
    return GPTAgent(
        name="Analista de texto",
        instructions="Use a ferramenta para contar palavras quando solicitado.",
        tools=[contar_palavras_tool],
    )
