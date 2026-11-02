"""Sequential orchestration with explicit contracts and injectable agents."""

from typing import Any, Protocol

from pydantic import BaseModel

from app.orchestration.gpt_agent import GPTAgent


class ExtracaoResponse(BaseModel):
    fatos: list[str]


class RevisaoResponse(BaseModel):
    resumo: str
    pendencias: list[str]


class AgenteExecutavel(Protocol):
    async def run(self, prompt: str) -> Any: ...


def criar_agentes() -> tuple[GPTAgent, GPTAgent]:
    extrator = GPTAgent(
        name="Extrator",
        instructions="Extraia apenas fatos explícitos do texto fornecido.",
        output_type=ExtracaoResponse,
    )
    revisor = GPTAgent(
        name="Revisor",
        instructions="Resuma os fatos recebidos e identifique inconsistências internas.",
        output_type=RevisaoResponse,
    )
    return extrator, revisor


async def processar(
    texto: str, extrator: AgenteExecutavel, revisor: AgenteExecutavel
) -> RevisaoResponse:
    extracao = ExtracaoResponse.model_validate(await extrator.run(texto))
    revisao = await revisor.run(extracao.model_dump_json())
    return RevisaoResponse.model_validate(revisao)
