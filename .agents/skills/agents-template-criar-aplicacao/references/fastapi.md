# Integração FastAPI

Use `app/main.py` como ponto de integração, sem remover os endpoints existentes.
O [exemplo de endpoint](../assets/classificacao_api.py) usa `GPTAgent` com
configuração por ambiente e um contrato Pydantic. Não faz chamada na importação;
o cliente recebe requisições apenas quando o endpoint é executado.

Para executá-lo como demonstração a partir da raiz:

```bash
uv run --locked uvicorn --app-dir .agents/skills/agents-template-criar-aplicacao/assets classificacao_api:app --port 8001
```

Configure uma chave OpenAI real no ambiente ou `.env` antes de chamar `/classificar`.
Ao usar o arquivo em uma implementação, copie e adapte o endpoint ao módulo
da aplicação; não torne a aplicação dependente de imports da pasta de skills.

## Validação local

Importe o módulo e use `TestClient`. Substitua `classificador.run` por um
`AsyncMock` que devolva `ClassificacaoResponse`. Verifique a serialização de
`POST /classificar` e o erro de entrada vazia. A validação offline não demonstra
a precisão do modelo. As exceções do provedor devem ser mapeadas para o contrato
HTTP da aplicação antes de uma integração em produção.
