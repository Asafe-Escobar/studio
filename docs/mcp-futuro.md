# Conectar ElevenLabs e HeyGen (clones de voz e avatar)

Quando tiver as chaves, adicione os servidores em `.mcp.json` (ou com `claude mcp add`) e reinicie o Claude Code.
O agente `produtor-avatar` detecta as ferramentas `mcp__elevenlabs__*` e `mcp__heygen__*` sozinho.

## ElevenLabs (MCP oficial)
```
claude mcp add elevenlabs --scope project -e ELEVENLABS_API_KEY=<sua-chave> -- uvx elevenlabs-mcp
```
Precisa do `uv` instalado (`pip install uv`). Confira o nome do pacote no repositório oficial `elevenlabs/elevenlabs-mcp`
antes de rodar, porque ele pode mudar.

## HeyGen
A HeyGen publica um servidor MCP próprio. Pegue o comando atual na documentação da HeyGen e adicione com:
```
claude mcp add heygen --scope project -e HEYGEN_API_KEY=<sua-chave> -- <comando do servidor>
```

## Depois de conectar
1. Registre o consentimento do dono da voz/imagem em `conhecimento/produtor-avatar/consentimentos.md`.
2. Anote o `voice_id` e o `avatar_id` do cliente em `clientes/<cliente>/perfil.md`.
3. Peça: "transforma o roteiro 2 da pesquisa X em vídeo com meu clone".

Não coloque chaves de API em arquivos versionados. Use variáveis de ambiente.
