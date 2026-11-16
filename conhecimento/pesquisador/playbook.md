# Playbook do pesquisador

## Perguntas que toda pesquisa de nicho responde
1. Quais formatos estão trazendo mais views e engajamento nos últimos 30-60 dias?
2. Quais ganchos aparecem nos vídeos outliers?
3. Quais temas se repetem entre os vencedores (e quais estão saturados)?
4. Qual a duração média dos vencedores?
5. Quais CTAs geram mais comentários?
6. Quais 5-10 perfis concentram mais posts de alto desempenho no período? (Apify não dá histórico de seguidores; "crescimento" só com snapshots, ver abaixo.)

## Métricas
**Fonte principal do Instagram: API oficial** (`ferramentas/instagram/perfis.py`), que já calcula `outlier_score` sobre a mediana de interações dos últimos 30 posts de cada perfil e traz `views` de Reels. As regras de Apify abaixo valem só quando ele estiver conectado (TikTok/hashtags).
Campos, inputs e preços de cada ator: `atores-apify.md`. Views = `videoPlayCount` (IG) e `playCount` (TikTok); não compare redes entre si.
- **Outlier score** = views do post ÷ mediana de views do perfil nos últimos 30 posts. Acima de 3 = outlier.
  - Calcule só para os perfis dos 5 melhores posts da etapa de hashtags (reel-scraper, `resultsLimit` 30 = ~150 itens). Isso cabe no teto de 500.
  - Perfil sem essa coleta: `outlier_score` = `null`, ranqueie pelas views dentro do lote e diga no `resumo` que o outlier não foi calculado.
  - Se o perfil tiver menos de 10 posts no período, não calcule (mediana instável).
- **Perfis em destaque** = nº de posts do perfil no top 20 do lote + mediana de views. Não chame de "crescimento".
- **Crescimento real**: só comparando snapshots. Em toda pesquisa, salve `followersCount`/`authorMeta.fans` com data em `midia/<id>/bruto/perfis.json`. Se houver snapshot anterior do mesmo perfil, informe a variação e as duas datas. (`midia/` não é versionada: o snapshot se perde se a pasta for limpa.)
- **Engajamento** = (likes + comentários) ÷ views. Sem views: ÷ seguidores (diga qual usou).
- **Razão comentários/likes** alta indica polêmica ou CTA de palavra-chave.
- Compare formatos pela **mediana**, não pela média (um viral distorce a média).

## Uso do Apify (custo e qualidade)
- `resultsLimit` entre 30 e 50 por hashtag/perfil. Uma pesquisa completa deve ficar em 300-500 itens.
- Filtre por data (`onlyPostsNewerThan`: "60 days") quando o ator permitir. O hashtag scraper do IG não permite: filtre por `timestamp` depois.
- Ordem padrão: hashtags (~200 itens) → reels dos 5 perfis dos melhores posts (~150) → details desses perfis (5). Antes de rodar, estime itens × preço.
- Hashtags genéricas (#fitness) trazem lixo internacional; prefira hashtags em português e de subnicho.
- Salve o bruto em `midia/<id>/bruto/` (JSON) para reanálise sem pagar de novo.

## Classificação de formato por sinais
- Duração < 10s + texto grande na legenda/tela → `pov-texto` ou `trend-audio`
- Legenda com "parte 1", "reagindo", "@ fulano" → `react` / `dueto-costura`
- Tipo `Sidecar` (várias imagens) ou TikTok `isSlideshow: true` → `carrossel`
- Duração > 60s, 2 vozes, menção a episódio → `entrevista-podcast`
- Legenda com "passo a passo", "tutorial", nome de app → `tutorial-tela`
- Na dúvida, abra a thumbnail (`displayUrl`) e olhe.

## Ética
Dados públicos apenas. Não colete dados pessoais de seguidores. Roteiros se inspiram, não copiam.
