# Definições e contratos

Fontes: `app/orchestration/util.py`, `app/assets/agents/template.md` e o wrapper
que será usado. A skill de execução `agent_description_writer` orienta a redação
do papel, objetivo e seções; preserve essas orientações, mas escolha o modelo
pelo provedor atual em vez de copiar um default fixo de outro exemplo.

## Modelo adaptável

O arquivo [relatorio_revisor.md](../assets/relatorio_revisor.md) é uma definição
completa. Copie-o para `app/assets/agents/relatorio_revisor.md` apenas quando
esse agente fizer parte da tarefa. Ele omite `model` para aceitar o fallback
do wrapper e especifica explicitamente o orçamento de saída.

Defina também o contrato no código que usa o agente:

```python
from pydantic import BaseModel
from app.orchestration.gpt_agent import GPTAgent

class RevisaoResponse(BaseModel):
    resumo: str
    pendencias: list[str]

revisor = GPTAgent(agent_id="relatorio_revisor", output_type=RevisaoResponse)
# Em uma função async: resultado = await revisor.run(texto)
```

Com DeepSeek ou servidor local, troque o import e a classe por `GPTLocalAgent`
de `app.orchestration.gpt_agent_local`; configure `LOCAL_*`. Não reaproveite
um frontmatter com um nome de modelo OpenAI nesse provedor.

## Semântica do loader

- A busca usa o nome do arquivo, não o valor de `id` dentro do YAML.
- `name` é opcional; o fallback é o `agent_id`.
- `goal`, `backstory` e os conteúdos das seções são unidos em instruções.
  `role` é acrescentado pelo wrapper. Os títulos não são preservados nessa união.
- As seções convencionais são `INPUT`, `OUTPUT`, `INSTRUCTIONS` e `KNOWLEDGE`.
  Evite novos títulos Markdown de nível 1 dentro delas: o parser os interpreta
  como novas seções, inclusive dentro de blocos de código.
- `model` ausente ou vazio usa o fallback. `max_tokens` ausente usa 2048;
  vazio não é equivalente a ausente e falha na conversão.
- O validador exige `id`, `role`, `goal` e as quatro seções preenchidas como
  convenção de autoria. O loader em si é mais permissivo.

## Critérios de autoria

Escreva propósito verificável, entradas aceitas, tratamento de dados ausentes,
idioma e formato de saída. Use `backstory` para contexto de comportamento quando
útil. Dimensione `max_tokens` pela saída esperada. Não acrescente conhecimento
ou fontes que o agente não receberá. Se houver citações, defina como retornar
a referência junto à afirmação e como agir quando não houver evidência.
