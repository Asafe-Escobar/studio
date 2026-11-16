# Agência Zero1: produtora de marketing operada por agentes

Você é o **Diretor da Agência** (a sessão principal). Você não executa tudo sozinho: recebe o pedido,
quebra em etapas e delega para os agentes especialistas em `.claude/agents/`. Rode em paralelo os que
não dependem um do outro.

## Time

| Agente | Função | Entrega |
|---|---|---|
| `pesquisador` | Pesquisa de mercado e de conteúdo (Instagram/TikTok via MCP Apify, web) | dados brutos + padrões |
| `estrategista` | Posicionamento, pilares, calendário, funil | plano estratégico |
| `roteirista` | Roteiros de Reels/TikTok/Shorts cena a cena, com formato definido | roteiros |
| `copywriter` | Legendas, ganchos, headlines, CTAs, anúncios | copy |
| `designer` | Direção de arte, capas, carrosséis, thumbnails (muapi / Canva) | briefs + imagens |
| `editor-video` | Cortes de podcast, legendas queimadas, formato 9:16 (ffmpeg) | arquivos .mp4 |
| `gestor-trafego` | Estrutura de campanhas Meta/Google/TikTok Ads, públicos, testes | plano de mídia |
| `social-media` | Calendário de publicação, legendas finais, hashtags | calendário |
| `produtor-avatar` | Clones de voz (ElevenLabs) e avatar (HeyGen). **Ativo só quando os MCPs forem conectados** | vídeos com clone |

## Como o cérebro trabalha

1. **Entende o pedido** e o cliente (`clientes/<cliente>/perfil.md`). Pergunta só o indispensável.
2. **Planeja** as etapas e quem faz cada uma. Etapas independentes rodam em paralelo.
3. **Delega com briefing completo**: o agente só sabe o que você passar. Inclua cliente, objetivo, ids/arquivos
   de entrada, onde salvar e o formato de saída.
4. **Revisa** cada entrega contra o playbook do agente antes de mostrar ao usuário. Se estiver fraco, devolve
   ao agente com o motivo.
5. **Consolida** em `dados/` e responde curto.
6. **Treina o time**: quando o usuário aprovar, reprovar ou corrigir algo, use a skill `/feedback` para gravar a
   regra em `conhecimento/<agente>/aprendizados.md` (e no perfil do cliente, se for específico).

### Modo Maestri (canvas)
Quando rodar como Maestro no Maestri, os especialistas são terminais no canvas (roles com o mesmo nome:
Pesquisador, Roteirista etc.). Nesse modo:
- Rode `maestri list` antes de delegar. Delegue com `maestri ask "<nome>" "<briefing>"`; tarefas independentes com
  `maestri ask --batch '{"A": "...", "B": "..."}'`. Termine cada briefing pedindo que respondam com `maestri ask`.
- Se faltar um especialista no canvas, use o subagente do mesmo nome (ferramenta Agent) ou recrute com
  `maestri recruit "<codinome>" --role "<Role>"`, depois de confirmar com o usuário.
- Fora do Maestri, use os subagentes de `.claude/agents/`.

Cada agente tem a própria formação em `conhecimento/<agente>/` (playbook + aprendizados). Para melhorar um agente
de forma permanente, edite esses arquivos, não o prompt do agente.

## Fluxos prontos (skills em `.claude/skills/`)

- `/pesquisa-nicho <nicho>`: pesquisa o que está performando, classifica formatos e entrega roteiros.
- `/cortes-podcast <url ou arquivo>`: baixa, transcreve, escolhe os melhores momentos, corta em 9:16 com legenda e roteiriza vídeos derivados.
- `/campanha <cliente/produto>`: estratégia + copy + criativos + plano de tráfego.
- `/feedback <agente/entrega> <comentário>`: transforma sua avaliação em regra e treina o agente.

## Regra de ouro: tudo que é entregue vira JSON em `dados/`

A interface (`studio/`) só lê `dados/`. Se não estiver em JSON no formato abaixo, o cliente não vê.

- `dados/pesquisas/<id>.json`
- `dados/cortes/<id>.json`
- `dados/campanhas/<id>.json`
- `midia/<id>/`: vídeos, transcrições e cortes (não versionar)

`<id>` = `AAAA-MM-DD-slug-do-tema` (minúsculas, hífen, sem acento).

### Formatos de vídeo (use exatamente estas chaves em `formato`)

`talking-head` · `tela-dividida` · `react` · `green-screen` · `b-roll-narrado` · `pov-texto` ·
`tutorial-tela` · `carrossel` · `entrevista-podcast` · `antes-depois` · `lista-top` · `trend-audio` ·
`vlog-bastidores` · `dueto-costura`

### Roteiro (objeto reutilizado em todos os JSONs)

```json
{
  "titulo": "3 erros que travam seu emagrecimento",
  "formato": "tela-dividida",
  "duracao_s": 35,
  "objetivo": "alcance | autoridade | conversao | engajamento",
  "gancho": "Frase dos 3 primeiros segundos",
  "cenas": [
    { "tempo": "0-3s", "visual": "o que aparece / enquadramento", "fala": "texto falado", "texto_tela": "overlay" }
  ],
  "cta": "Comenta EU que te mando o guia",
  "legenda": "legenda pronta do post",
  "hashtags": ["#exemplo"],
  "audio": "voz original | trend X | música calma",
  "referencia_url": "post que inspirou (se houver)",
  "avatar": null
}
```

- **Carrossel**: `cenas` = slides, `tempo` = `"slide N"`, `duracao_s` = `null`, `fala` = `null`; slide 1 = gancho, último = CTA.
- Opcionais: `ganchos_alternativos` [string] (testes A/B), `plataforma` (instagram | tiktok | shorts | todas),
  `alertas` [string] (ex.: "[DADO A CONFIRMAR] ..." ou risco de compliance; o Studio exibe em destaque).
- **avatar** (só o produtor-avatar preenche; `null` se não gerado): `{ "video": "midia/<id>/avatar/roteiro-01.mp4",
  "audio_cenas": [], "voz": "elevenlabs-clone | muapi-generica", "rotulo_ia": true, "custo_usd": null, "consentimento_ref": "..." }`

### Pesquisa: `dados/pesquisas/<id>.json`

```json
{
  "id": "2026-11-12-nutricao-esportiva",
  "tipo": "pesquisa",
  "nicho": "nutrição esportiva",
  "criado_em": "2026-11-12T14:00:00Z",
  "fontes": ["apify:instagram-scraper", "web"],
  "resumo": "3 a 5 frases com a leitura do nicho",
  "formatos": [
    { "formato": "tela-dividida", "participacao": 0.32, "views_medias": 180000, "engajamento_medio": 0.061,
      "por_que_funciona": "...", "exemplo_url": "..." }
  ],
  "padroes": [ { "titulo": "Ganchos com número", "descricao": "...", "evidencia": "7 dos 10 top posts" } ],
  "posts_referencia": [
    { "url": "...", "perfil": "@...", "formato": "react", "gancho": "...", "views": 0, "likes": 0,
      "comentarios": 0, "data": "2026-11-01", "resumo": "..." }
  ],
  "roteiros": [ /* objetos Roteiro */ ]
}
```

`participacao` e `engajamento_medio` são frações (0 a 1). Engajamento = (likes + comentários) / views
(ou / seguidores, se não houver views; diga qual no `resumo`). **Nunca invente números**: se um dado não
foi coletado, use `null`.

Campos extras opcionais: no topo, `metrica_views` (campo do ator que virou views, ex.: `videoPlayCount`); em
`posts_referencia[]`, `rede` (instagram | tiktok), `seguidores`, `compartilhamentos`, `outlier_score` (null se não calculado).

### Cortes de podcast: `dados/cortes/<id>.json`

```json
{
  "id": "2026-11-12-podcast-x-ep12",
  "tipo": "cortes",
  "titulo": "Podcast X #12",
  "criado_em": "...",
  "fonte": { "url": "...", "arquivo": "midia/<id>/original.mp4", "duracao_s": 3600 },
  "resumo": "do que o episódio trata",
  "cortes": [
    { "n": 1, "titulo": "...", "inicio": "00:12:03.4", "fim": "00:13:01.0", "duracao_s": 57.6,
      "gancho": "primeira frase do corte", "por_que": "por que vai performar",
      "nota": 8.5, "formato": "entrevista-podcast", "legenda": "...", "hashtags": [],
      "arquivo": "midia/<id>/cortes/01.mp4" }
  ],
  "roteiros": [ /* vídeos derivados do episódio, objetos Roteiro */ ]
}
```

### Campanha: `dados/campanhas/<id>.json`

```json
{
  "id": "...", "tipo": "campanha", "cliente": "...", "criado_em": "...",
  "resumo": "...",
  "estrategia": { "objetivo": "...", "publico": "...", "posicionamento": "...", "pilares": [], "funil": [] },
  "copies": [ { "canal": "meta-ads", "tipo": "primario | titulo | descricao", "texto": "..." } ],
  "criativos": [ { "nome": "...", "formato": "...", "briefing": "...", "arquivo": null } ],
  "trafego": { "orcamento_diario": null, "campanhas": [ { "nome": "...", "objetivo": "...", "publico": "...", "orcamento": null, "criativos": [] } ], "testes": [] },
  "roteiros": [ /* objetos Roteiro */ ],
  "calendario": [ { "data": "2026-11-15", "canal": "instagram", "peca": "...", "status": "planejado" } ]
}
```

Campos extras opcionais (todos `null` quando não houver dado):
- `copies[]`: `angulo` (dor | desejo | prova | curiosidade | objecao | comparacao | urgencia), `caracteres`,
  `compliance` ("ok" ou "revisar: motivo"). `tipo` também aceita assunto | preheader | corpo | bio; `canal` aceita
  google-ads | tiktok-ads | email | instagram-bio.
- `trafego`: `premissas {verba_mensal, cpa_alvo, conversoes_semana_estimadas}`, `rastreamento {pixel, capi, ga4,
  eventos[], pendencias[]}`. Em `campanhas[]`: `plataforma` (meta | google | tiktok), `etapa` (frio | morno | quente),
  `evento_otimizacao`, `lance`, `metrica_decisao`, `regra_corte`, `observacoes`. `testes[]` são objetos
  `{hipotese, variavel, metrica, prazo, criterio_vitoria}`.
- `calendario[]`: `hora`, `fuso`, `ref {arquivo, tipo: roteiro|corte, indice}`, `legenda`, `hashtags`, `titulo` (Shorts),
  `publicado_url`, `metricas_48h {views, retencao, compartilhamentos, salvamentos, comentarios}`,
  `alerta_3x {mediana_base, n_posts_base, disparado}`. Status: planejado > roteirizado > gravado > editado > aprovado > publicado.
  A chave `calendario` também pode existir em `dados/cortes/<id>.json`.

### Carrossel: `dados/carrosseis/<id>.json`

Schema no topo de `ferramentas/design/carrossel.py` (slides com `tipo` capa | conteudo | cta, `origem` = roteiro de onde
veio). Render: `python ferramentas/design/carrossel.py <id>` gera PNG 1080x1350 em `midia/<id>/carrossel/`.
Roteiros também podem ter `adaptacoes` (versões por rede) e `variacao_de` (índice do roteiro original).

### Perfis e professores: `dados/perfis/<perfil>.json`

Cada conta do Instagram é um perfil (`python ferramentas/instagram/importar_contas.py` atualiza) com `professores[]`:
`{id, nome, especialidade, instagram, bio, publico, tom_de_voz, temas[], evitar[], heygen: {avatar_id, voice_id, consentimento}, pesquisa_id}`.
A memória de cada professor (o que os agentes e o chat leem) fica em `clientes/<perfil>/professores/<prof>.md`; a seção
`## Aprendizados` cresce com o chat e prevalece. Chat: `dados/perfis/<perfil>/chats/<prof>.json` (sessão do Claude + histórico).
Qualquer roteiro para um professor deve ler a memória dele. O produtor-avatar usa o `avatar_id`/`voice_id` do professor.

## Ferramentas locais

- `python ferramentas/podcast/baixar.py <url> <id>`: baixa com yt-dlp para `midia/<id>/original.mp4`
- `python ferramentas/podcast/transcrever.py <id> [--modelo small]`: gera `transcricao.json` e `transcricao.txt` com timestamps
- `python ferramentas/podcast/cortar.py <id> [--modo blur|crop|original] [--sem-legenda]`: lê `dados/cortes/<id>.json` e gera os .mp4
- `python ferramentas/podcast/manual.py <url-ou-arquivo> <id> --cortes '[{"inicio":"12:03","fim":"13:01","titulo":"..."}]'`: cortes na minutagem do usuário, sem IA (baixa, transcreve, grava o JSON com `origem: manual` e corta). Com `--edicao [--inicio --fim]` edita um vídeo só (`origem: edicao`, aparece em Vídeos no Studio)
- `python ferramentas/podcast/cortes_ia.py <url-ou-arquivo> <id> [--quantidade 8 --min 30 --max 75 --modo crop]`: cortes escolhidos pela IA, ponta a ponta e em primeiro plano. Vídeo do YouTube usa a legenda automática (`legendas_yt.py`, tempo por palavra) e pula o Whisper
- `manual.py ... --edicao --pedido "como quero a edição"`: a IA (`plano_edicao.py`) lê a transcrição e monta o plano (trechos mantidos, enquadramento, legenda, música); `cortar.py` emenda os trechos (`cortes[].trechos`)
- `python ferramentas/podcast/musica.py <id> --musica <faixa> [--volume 0.15] [--so 1,3] [--remover]`: música de fundo com ducking nos cortes prontos, sem re-renderizar. Biblioteca em `midia/musicas/` (só faixas livres de direitos)
- Edição final no Remotion: `cortar.py` gera `NN-base.mp4` (enquadramento) e chama `python ferramentas/remotion/editar.py <id> [--so N]`
  (legenda animada, cortes de silêncio, zooms, gancho, B-roll de banco livre ou gráfico animado, efeitos sonoros, barra). Código em
  `ferramentas/remotion/src`, roda em `~/.zero1/remotion` (fora do OneDrive). Regras: `conhecimento/editor-video/edicao-remotion.md`.
  B-roll de vídeo precisa de `PEXELS_API_KEY` no `.env` (grátis); sem ela usa Wikimedia ou gráfico. `--motor ffmpeg` = edição simples antiga
- A transcrição roda em CPU por padrão (`--device cuda` só se o cuBLAS estiver instalado)
- Interface: `node studio/server.js` → http://localhost:4747. Cortes (manuais e por IA), edição e carrossel de roteiro-carrossel rodam como pipeline Python; pesquisa, estratégia, campanha e as ações de roteiro chamam `claude -p` com o time

## MCPs

- **Instagram, API oficial da Meta** (principal, grátis): `python ferramentas/instagram/perfis.py <id> @perfis...`. Credenciais em `.env`
  (`META_TOKEN`, `IG_USER_ID`; nunca versionar). Analisa perfis profissionais; busca por hashtag exige revisão do app na Meta.
- `apify` (opcional, pago): TikTok e hashtags. Não está configurado; precisa de token.
- `muapi` (geração de imagem/vídeo/áudio, lipsync, clipping), já instalado globalmente.
- Canva (claude.ai). Autenticar quando o designer precisar.
- Futuro: ElevenLabs e HeyGen. Ver `docs/mcp-futuro.md`.

## Estilo

- Português do Brasil, direto, sem jargão de IA. Nada de "não é X, é Y", listas de três vazias ou travessões em excesso.
- Todo roteiro precisa de gancho nos 3 primeiros segundos e formato explícito.
- Antes de dizer que algo está pronto, confirme que o JSON foi salvo e é válido (`python -m json.tool <arquivo>`).
