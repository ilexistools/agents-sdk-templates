# Sandbox e skills de execução

Leia `app/orchestration/gpt_sandbox_agent.py` e a seção de sandbox do README
antes de escolher o backend. As classes de sandbox podem mudar entre versões
do Agents SDK; confira os imports no ambiente travado.

```python
from app.orchestration.gpt_sandbox_agent import GPTSandboxAgent

agente = GPTSandboxAgent(
    name="Assistente com skills",
    instructions="Use a skill haiku_quality para revisar o haiku recebido.",
)
# Somente com backend configurado: resultado = await agente.run(texto)
```

## Ambiente e arquivos

- Sem cliente explícito, o wrapper escolhe `UnixLocalSandboxClient` fora do
  Windows e tenta `DockerSandboxClient` no Windows. O backend local Unix não
  executa no Windows. Docker exige a dependência opcional e um daemon acessível;
  importar ou construir o cliente não comprova sua disponibilidade.
- Use `sandbox_client` para fornecer um backend configurado. Não presuma que
  uma chave DeepSeek dá acesso ao ambiente ou às capacidades de sandbox.
- O diretório padrão de skills é `app/assets/skills`. `skills_dir` aceita outro
  caminho; confira `resolve_skills_dir` para a resolução de caminhos relativos.
- A configuração padrão soma `Skills(LocalDirLazySkillSource(...))` a
  `Capabilities.default()`. Ao passar `capabilities` explicitamente, você
  substitui essa composição inteira; inclua a capacidade de skills se necessária.
- `skills_path=".agents"` é um caminho dentro do workspace do sandbox.
  Ele não é o diretório `.agents/skills/` de desenvolvimento deste repositório.

## Como verificar

Separe três evidências: construção do agente e resolução dos caminhos;
execução de uma tarefa pelo backend; e uso de uma skill no resultado.
Para demonstrar uso, peça uma tarefa em que as orientações específicas da
skill façam diferença e verifique esse comportamento ou os traces disponíveis.
A presença de um arquivo não comprova que o modelo o leu.

Se o ambiente não tiver backend, valide apenas configuração e imports e
registre a limitação. Não declare um teste de execução bem-sucedido com base
somente em mocks ou construção de objetos.
