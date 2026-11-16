---
name: pesquisa-nicho
description: Pesquisa o que está performando em um nicho no Instagram/TikTok, classifica os formatos (tela dividida, react, talking head...) e entrega roteiros prontos. Use quando o usuário passar um nicho e quiser saber que conteúdo fazer.
argument-hint: <nicho> [cliente] [perfis]
---
# Pesquisa de nicho (fluxo rápido)

Entrada: `$ARGUMENTS` (nicho e, opcionalmente, cliente, perfis de referência, quantidade de roteiros e id).

Você é o Diretor. Velocidade importa: o usuário acompanha em tempo real. Siga exatamente estas 3 etapas,
sem revisões extras em fila.

## 1. Coleta (pesquisador, 1 chamada)
- `id` = o informado ou `AAAA-MM-DD-slug-do-nicho`.
- Perfis: use os que o usuário passou + os salvos em `conhecimento/pesquisador/perfis-nicho/<slug>.txt` (se existir).
  Só faça WebSearch para descobrir perfis se tiver menos de 10. Limite: 2 a 3 buscas.
- **Se `midia/<id>/bruto/resumo.json` já existe, pule a coleta** (só rode `python ferramentas/instagram/resumo.py <id>`
  se faltar o resumo e existir `instagram.json`).
- Peça ao **pesquisador**: rodar `python ferramentas/instagram/perfis.py <id> @perfis... --posts 30` (uma única
  chamada com todos os perfis; ela já gera o resumo), analisar **só `midia/<id>/bruto/resumo.json`** (o
  `instagram.json` é grande: consulte só trechos pontuais, nunca leia inteiro) e salvar JÁ `dados/pesquisas/<id>.json` no schema do CLAUDE.md com
  `resumo`, `fontes`, `formatos`, `padroes`, `posts_referencia` e `"roteiros": []`. Salvar a lista final de perfis
  em `conhecimento/pesquisador/perfis-nicho/<slug>.txt` (um @ por linha) para a próxima pesquisa pular a descoberta.
- Assim que esse JSON existir, o Studio já mostra a pesquisa enquanto os roteiros são escritos.
- **Não transcreva os vídeos de referência** (Whisper em CPU leva minutos por vídeo e trava o fluxo). Use legenda,
  gancho e métricas do `resumo.json`. Transcrição só se o usuário pedir, e no máximo 3 vídeos.

## 2. Roteiros (roteiristas em paralelo)
- Divida a quantidade pedida (padrão 6) em lotes de até 3 e chame **um roteirista por lote, todos na mesma
  mensagem** (paralelo). Cada lote recebe 1 formato dos que mais performam e os posts de referência dele.
- Cada roteirista já entrega `ganchos_alternativos` (2 por roteiro), legenda, hashtags e CTA prontos.
  Não chame copywriter nem estrategista neste fluxo.
- Cada roteirista grava o próprio lote em `midia/<id>/parciais/roteiros-<n>.json` (array de roteiros) assim que
  terminar: o Studio mostra os roteiros na hora, sem esperar os outros lotes. Não editar o JSON da pesquisa.

## 3. Fechamento (você)
- Junte os roteiros dos parciais em `dados/pesquisas/<id>.json` (depois apague `midia/<id>/parciais/`), mantenha a
  chave `perfis` se existir, troque `status` para `"pronto"`, acrescente ao `resumo` 2 a 3 recomendações de pilares e mix
  de formatos (você mesmo escreve) e valide com `python -m json.tool`.
- Responda em 3 linhas: leitura do nicho, ranking de formatos, "abra o Studio para ver os roteiros".
