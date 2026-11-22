"""__TITLE__ (ferramenta).

Contrato do catálogo: Input, Output e async run. Toda a lógica deve ser
determinística e testável sem rede. Documente cada campo com description:
o texto aparece na interface, na documentação da API e no schema MCP.
"""

from pydantic import BaseModel, Field


class Input(BaseModel):
    text: str = Field(min_length=1, description="Texto de entrada.")


class Output(BaseModel):
    result: str = Field(description="Resultado do processamento.")


async def run(request: Input) -> Output:
    return Output(result=request.text)
