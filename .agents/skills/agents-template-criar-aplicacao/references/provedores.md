# Provedores e configuração

Consulte `app/orchestration/config.py`, `gpt_local.py`, `gpt_agent_local.py`,
`env-example` e as seções de provedores do README. As versões efetivas estão
em `uv.lock`; não atualize dependências só para reproduzir um exemplo.

| Destino | Configuração | Wrappers previstos |
|---|---|---|
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL_NAME` | `GPT`, `GPTAgent` |
| Decisions OpenAI | `OPENAI_API_KEY`, `OPENAI_DECISION_MODEL_NAME` | `GPTDecision` |
| Sandbox OpenAI | anteriores e `OPENAI_SANDBOX_MODEL_NAME` | `GPTSandboxAgent` |
| LM Studio / Ollama | `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, `LOCAL_API_KEY` | `GPTLocal`, `GPTLocalAgent` |
| DeepSeek | as mesmas variáveis `LOCAL_*`, com chave real DeepSeek | `GPTLocal`, `GPTLocalAgent` |

Sem um modelo explícito, use o default atual do projeto. Se o usuário pedir
um modelo atual específico ou o mais recente, confira a documentação oficial
do provedor antes de escolher seu identificador. Não troque silenciosamente
o provedor nem trate um identificador de exemplo como recomendação permanente.

## Servidores locais

LM Studio costuma usar `http://localhost:1234/v1`; Ollama,
`http://localhost:11434/v1`. Eles precisam estar em execução com o modelo
carregado. Chaves fictícias só servem quando o servidor permite isso.

## DeepSeek

Use `https://api.deepseek.com` como `LOCAL_BASE_URL` e uma chave DeepSeek
real em `LOCAL_API_KEY`. Defina o nome do modelo em `LOCAL_MODEL_NAME`, conforme
a [documentação DeepSeek](https://api-docs.deepseek.com/guides/harness).
O README contém um exemplo de `.env` completo.

`DEEPSEEK_API_KEY` não é lida automaticamente pelos wrappers. Para usar esse
nome, carregue o ambiente e passe explicitamente `api_key=os.environ["DEEPSEEK_API_KEY"]`.
Mantenha `LOCAL_DISABLE_TRACING="true"` para não exportar traces à OpenAI.
`GPTLocalAgent` configura o tracing global do Agents SDK ao ser construído;
considere esse efeito quando misturar provedores no mesmo processo.

Chat Completions compatível não garante equivalência de ferramentas, parâmetros
e raciocínio. Em especial, verifique o replay de `reasoning_content` em chamadas
de ferramentas quando o modo de raciocínio estiver habilitado. O projeto não
implementa um adaptador DeepSeek dedicado; não prometa esse suporte sem teste.

## Saída estruturada

`GPT` usa `responses.parse(text_format=...)`; `GPTAgent` usa o contrato do
Agents SDK. Nos dois wrappers locais, o schema entra nas instruções e o texto
é validado depois. `GPTLocalAgent` retorna string internamente e faz o parsing
no wrapper; não acrescenta `response_format` à chamada.

Um schema customizado inválido pode causar erro de validação. `GPTLocal` pode
retornar `GPTLocalResponse` como fallback; se a aplicação exige o tipo customizado,
verifique o tipo antes de usá-lo. Não apresente o fallback como validação bem-sucedida.
