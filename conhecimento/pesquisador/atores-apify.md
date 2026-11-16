# Atores Apify: input e campos de saída

Fonte: páginas oficiais dos atores na Apify Store, lidas em 2026-11-12. Campo fora desta lista = confira a página antes de usar.
- https://apify.com/apify/instagram-reel-scraper
- https://apify.com/apify/instagram-hashtag-scraper
- https://apify.com/apify/instagram-scraper
- https://apify.com/clockworks/tiktok-scraper

## Input pronto (copie e troque os valores)

| Ator | Para quê | Input |
|---|---|---|
| `apify/instagram-hashtag-scraper` | descobrir posts e perfis | `{"hashtags": ["receitasfit"], "resultsType": "reels", "resultsLimit": 40}` |
| `apify/instagram-reel-scraper` | reels de perfis (base do outlier) | `{"username": ["perfil1"], "resultsLimit": 30, "onlyPostsNewerThan": "60 days", "skipPinnedPosts": true}` |
| `apify/instagram-scraper` | seguidores do perfil (snapshot) | `{"directUrls": ["https://www.instagram.com/perfil1/"], "resultsType": "details"}` |
| `clockworks/tiktok-scraper` | TikTok por hashtag/perfil | `{"hashtags": ["receitasfit"], "resultsPerPage": 40}` ou `{"profiles": ["perfil1"], "resultsPerPage": 30, "profileSorting": "latest", "excludePinnedPosts": true}` |

Cuidados:
- Hashtag scraper do IG **não tem filtro de data**. Filtre por `timestamp` depois de coletar e diga no `resumo` quantos itens caíram fora da janela.
- Hashtag no IG vai sem `#` (`receitasfit`).
- TikTok: `oldestPostDateUnified` (data ou nº de dias) é **filtro cobrado à parte** e só funciona com `profileSorting` "latest" ou "oldest". Use só se o Diretor liberar o custo. Sem ele, filtre por `createTimeISO` depois.
- Valores exatos de `resultsType` no hashtag scraper ("posts"/"reels"): a confirmar no input schema na primeira execução.
- Não ligue extras pagos (transcrição, download de vídeo, AI summary) sem pedido.

## Mapa de campos (use sempre este nome no JSON de entrega)

| Métrica | IG reel / instagram-scraper | IG hashtag | TikTok |
|---|---|---|---|
| views | `videoPlayCount` | `videoPlayCount` | `playCount` |
| likes | `likesCount` | `likesCount` (-1 = oculto → `null`) | `diggCount` |
| comentários | `commentsCount` | `commentsCount` | `commentCount` |
| compartilhamentos | só com `includeSharesCount` (plano Starter) | `sharesCount` | `shareCount` |
| salvamentos | não disponível | não disponível | `collectCount` |
| duração (s) | `videoDuration` | `videoDuration` (unidade não documentada; assumir s e checar) | `videoMeta.duration` |
| data | `timestamp` | `timestamp` | `createTimeISO` |
| perfil | `ownerUsername` | `ownerUsername` | `authorMeta.name` |
| seguidores | só `instagram-scraper` details: `followersCount` | não vem | `authorMeta.fans` |
| tipo | `type` (Video/Image/Sidecar), `productType` ("clips" = reel) | `type`, `productType` | `isSlideshow` (true = carrossel) |
| áudio | `musicInfo.song_name`, `uses_original_audio` | `musicInfo` | `musicMeta.musicName`, `musicOriginal` |
| link | `url` | `url` | `webVideoUrl` |
| publi | `paidPartnership`, `sponsors` | não documentado | `isAd`, `isSponsored` |

**Views no Instagram:** os atores trazem `videoPlayCount` e `videoViewCount`, e a Apify não define a diferença (a confirmar). Regra: use `videoPlayCount` (é o único presente nos dois atores do IG) e nunca misture os dois numa mesma comparação. Não compare views de IG com views de TikTok como se fossem a mesma métrica: compare dentro de cada rede.

Post patrocinado (`paidPartnership`, `isAd`, `isSponsored`) não entra no ranking orgânico; cite à parte se for relevante.

## Custo (preço de tabela, 2026-11-12, plano Free)
- instagram-reel-scraper: US$ 2,60 / 1.000 resultados
- instagram-hashtag-scraper: US$ 2,60 / 1.000
- instagram-scraper: US$ 2,70 / 1.000
- tiktok-scraper: "a partir de US$ 1,70 / 1.000"; preço por evento e filtros cobrados: a confirmar em https://apify.com/clockworks/tiktok-scraper/pricing

Estimativa antes de rodar: itens previstos × preço. Mande a estimativa ao Diretor se passar de 500 itens.
