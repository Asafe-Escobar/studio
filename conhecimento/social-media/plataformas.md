# Especificações de plataforma

Só entra número com fonte oficial. Checado em 2026-11-12. Item sem fonte oficial = "a confirmar" (não use como regra).
Reverifique a cada 6 meses ou quando a plataforma anunciar mudança.

| Rede | Item | Valor | Fonte |
|---|---|---|---|
| Instagram | Legenda (máx.) | 2.200 caracteres | [Graph API, IG User Media](https://developers.facebook.com/documentation/instagram-platform/instagram-graph-api/reference/ig-user/media) |
| Instagram | Hashtags (máx.) | 30 por legenda | idem; [Help Center](https://help.instagram.com/351460621611097) |
| Instagram | @menções (máx.) | 20 por legenda | idem Graph API |
| Instagram | Teste de limite de 5 hashtags | a confirmar (só fontes de terceiros) | — |
| Instagram | Corte do "mais" na legenda | a confirmar | — |
| TikTok | Legenda de vídeo (máx.) | 2.200 caracteres UTF-16 (emoji conta mais) | [Content Posting API, Direct Post](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post) |
| TikTok | Corte do "mais" / duração máx. de vídeo | a confirmar | — |
| YouTube Shorts | Duração | até 3 min, vertical ou quadrado | [YouTube Help 15424877](https://support.google.com/youtube/answer/15424877?hl=en) |
| YouTube Shorts | Música licenciada | até 90 s dentro do Short de 3 min | idem |
| YouTube | Título (máx.) | 100 caracteres, sem `<` `>` | [YouTube Help 57404](https://support.google.com/youtube/answer/57404?hl=en) |
| YouTube | Descrição (máx.) | 5.000 caracteres (na API são bytes: acento e emoji gastam mais) | idem; [Data API videos](https://developers.google.com/youtube/data/reference/rest/v3/videos) |
| YouTube Shorts | Caracteres do título visíveis no feed | a confirmar | — |
| LinkedIn | Post (máx.) | 3.000 caracteres | [LinkedIn Help 86780](https://www.linkedin.com/help/linkedin/answer/86780) |
| LinkedIn | Corte do "ver mais" / limite de hashtags | a confirmar | — |
| Todas | Safe zones de texto na tela | a confirmar (pedir ao designer/editor a fonte oficial antes de usar) | — |

Regra prática enquanto o corte do "mais" estiver "a confirmar": o gancho cabe na primeira linha da legenda, curta.
