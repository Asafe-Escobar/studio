---
name: cortes-podcast
description: Transforma um episódio de podcast (URL do YouTube ou arquivo local) em vários cortes verticais com legenda e roteiriza vídeos derivados do episódio. Use quando o usuário mandar um podcast, live ou entrevista longa.
argument-hint: <url ou caminho do arquivo> [cliente]
---

## Regra principal (velocidade e confiabilidade)
Rode o pipeline completo **em primeiro plano** (nunca em segundo plano: a sessão pode encerrar e matar o processo):
`python ferramentas/podcast/cortes_ia.py <url-ou-arquivo> <id> --quantidade 8 --min 30 --max 75 --modo blur|crop`
Ele baixa, usa a legenda automática do YouTube (segundos) ou o Whisper (arquivos enviados), deixa a IA escolher os
cortes numa chamada só, grava `dados/cortes/<id>.json` e renderiza. Leva 2 a 3 min para vídeo do YouTube.
Só depois, se pedirem, chame o roteirista para os vídeos derivados (gravando em `roteiros` do mesmo JSON).

# Cortes de podcast

Entrada: `$ARGUMENTS`.

Você é o Diretor.

1. Defina o `id` = `AAAA-MM-DD-slug-do-episodio`.
2. **editor-video**: rodar o pipeline completo do playbook dele (baixar, transcrever, escolher 5 a 12 cortes,
   escrever `dados/cortes/<id>.json`, renderizar com `cortar.py`). A transcrição pode levar vários minutos:
   rode os comandos longos em background e espere a notificação.
3. Com o JSON dos cortes salvo, rode **em paralelo**:
   - **copywriter**: título (gancho em até 8 palavras), legenda e hashtags de cada corte.
   - **roteirista**: 4 a 6 roteiros derivados do episódio em outros formatos (react ao corte mais forte,
     tela-dividida com dado que comprova uma fala, carrossel com os pontos principais, talking-head do apresentador
     aprofundando um tema). Passe a transcrição e os cortes.
4. Atualize `dados/cortes/<id>.json` com títulos, legendas e `roteiros`. Valide com `python -m json.tool`.
5. Responda com: quantos cortes, os 3 melhores (nota e motivo), onde estão os arquivos e "abra o Studio".
