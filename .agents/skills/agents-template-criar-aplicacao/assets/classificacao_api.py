"""Adaptable FastAPI example; model calls happen only on POST /classificar."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.orchestration.gpt_agent import GPTAgent


class ClassificacaoRequest(BaseModel):
    texto: str = Field(min_length=1)


class ClassificacaoResponse(BaseModel):
    categoria: str
    justificativa: str


classificador = GPTAgent(
    name="Classificador de solicitações",
    instructions=(
        "Classifique a solicitação como dúvida, incidente ou sugestão. "
        "Justifique em português usando apenas o texto recebido."
    ),
    output_type=ClassificacaoResponse,
)

app = FastAPI(title="Classificação de solicitações")


@app.post("/classificar", response_model=ClassificacaoResponse)
async def classificar(payload: ClassificacaoRequest) -> ClassificacaoResponse:
    return await classificador.run(payload.texto)
