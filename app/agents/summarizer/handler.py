"""Resumidor (agente).

O comportamento do modelo está em ``app/assets/agents/summarizer.md``.
Este handler só valida a entrada, chama o agente e devolve a saída estruturada.
"""

from pydantic import BaseModel, Field

from app.orchestration.gpt_agent import GPTAgent


class Input(BaseModel):
    text: str = Field(min_length=1, description="Texto a resumir, em qualquer idioma.")


class Output(BaseModel):
    summary: str = Field(description="Resumo fiel e conciso, no mesmo idioma do texto de entrada.")


async def run(request: Input) -> Output:
    agent = GPTAgent(agent_id="summarizer", output_type=Output)
    return await agent.run(request.text)
