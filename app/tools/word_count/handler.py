"""Contador de palavras (ferramenta).

Adapta a função pura ``count_words`` ao contrato do catálogo.
"""

from pydantic import BaseModel, Field

from app.mcp_tools.tools import count_words


class Input(BaseModel):
    text: str = Field(description="Texto a analisar. Palavras são separadas por qualquer espaço em branco.")


class Output(BaseModel):
    word_count: int = Field(description="Quantidade de palavras.")
    character_count: int = Field(description="Quantidade de caracteres, sem contar espaços e quebras de linha.")


async def run(request: Input) -> Output:
    return Output(**count_words(request.text))
