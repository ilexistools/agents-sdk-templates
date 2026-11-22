"""__TITLE__ (agente).

Contrato do catálogo: Input, Output e async run. O comportamento do modelo
fica em app/assets/agents/__ID__.md; este arquivo só adapta a entrada,
chama o agente e devolve a saída estruturada. Documente cada campo com
description: o texto aparece na interface, na API e no schema MCP.
"""

from pydantic import BaseModel, Field

from app.orchestration.gpt_agent import GPTAgent


class Input(BaseModel):
    text: str = Field(min_length=1, description="Texto que o agente deve processar.")


class Output(BaseModel):
    result: str = Field(description="Resposta produzida pelo agente.")


async def run(request: Input) -> Output:
    agent = GPTAgent(agent_id="__ID__", output_type=Output)
    return await agent.run(request.text)
