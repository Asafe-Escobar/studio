# Agência Zero1

Produtora de marketing operada por agentes. Um Diretor (o "cérebro") recebe o pedido e distribui o trabalho para
9 especialistas, cada um com o próprio treinamento.

```
.claude/agents/        quem é cada agente e como trabalha
.claude/skills/        fluxos: /pesquisa-nicho, /cortes-podcast, /campanha, /feedback
conhecimento/<agente>/ treinamento: playbook + aprendizados (cresce com o seu feedback)
clientes/              perfil de cada cliente (copie _modelo/)
dados/                 entregas em JSON (o Studio lê daqui)
midia/                 vídeos, transcrições, cortes, imagens
ferramentas/podcast/   baixar.py, transcrever.py, cortar.py
ferramentas/maestri/   criar_roles.py (um role do Maestri por agente)
studio/                interface web local
```

## Primeiro uso
1. Abra o Claude Code nesta pasta e rode `/mcp` para autenticar o **Apify** (pesquisa no Instagram/TikTok).
   Crie a conta em apify.com; o plano gratuito dá créditos mensais.
2. `node studio/server.js` e abra http://localhost:4747 (no Maestri, abra como portal).
3. Peça: `/pesquisa-nicho nutrição esportiva` ou `/cortes-podcast https://youtube.com/...`.

## No Maestri
Cada especialista é um terminal no canvas, criado com o role do mesmo nome (já cadastrados):
Pesquisador, Estrategista, Roteirista, Copywriter, Designer, Editor de Video, Gestor de Trafego, Social Media,
Produtor Avatar. O terminal do Diretor fica em Maestro Mode, conectado a todos.
Se mudar ou adicionar um agente, rode `python ferramentas/maestri/criar_roles.py` para atualizar os roles.

## Treinar o time
Diga o que achou de qualquer entrega (`/feedback roteirista os ganchos estão genéricos`). Vira regra em
`conhecimento/<agente>/aprendizados.md` e vale para todas as próximas tarefas.
