# Rastreamento, UTMs e nomenclatura

## Checklist antes de subir verba (sem isso, a campanha otimiza no escuro)
- [ ] Pixel Meta instalado e disparando nas páginas certas (testar no Gerenciador de Eventos).
- [ ] API de Conversões (CAPI) ativa ou planejada; eventos do navegador e do servidor com deduplicação (event_id).
- [ ] Domínio verificado no Business Manager.
- [ ] Eventos-chave mapeados e testados: PageView, ViewContent, AddToCart, InitiateCheckout, Purchase (com valor
      e moeda BRL), Lead, Contact. Para WhatsApp: evento de conversa ou clique no botão.
- [ ] Google: tag do Google/GA4 instalada, conversões importadas ou criadas no Google Ads, conversões
      principais vs secundárias definidas.
- [ ] TikTok: Pixel e/ou Events API com os mesmos eventos.
- [ ] E-commerce: feed de produtos aprovado (Merchant Center / catálogo Meta).
- [ ] Teste ponta a ponta: clique no anúncio de teste → conversão aparece nas plataformas e no GA4.
- [ ] Vendas fora do site (WhatsApp, loja, CRM): definir como volta o dado (planilha semanal, importação
      offline ou CRM integrado). Sem isso, registrar "resultado medido só até a conversa".
Item não verificado = registrar como risco no plano, não presumir que funciona.

## Padrão de UTMs
Tudo minúsculo, sem acento, hífen no lugar de espaço.

| Parâmetro | Valor | Exemplo |
|---|---|---|
| utm_source | plataforma | `meta`, `google`, `tiktok` |
| utm_medium | tipo de mídia | `cpc`, `paid-social` |
| utm_campaign | nome da campanha (padrão abaixo) | `zero1-vendas-frio-2026-11` |
| utm_content | criativo | `cr03-gancho-numero-v2` |
| utm_term | conjunto/palavra-chave | `lal-1-compradores` ou `{keyword}` |

Use parâmetros dinâmicos das plataformas quando disponíveis (a confirmar a sintaxe atual em cada gerenciador
antes de aplicar). Nunca use UTM em link interno do site.

## Nomenclatura
Campanha: `cliente_plataforma_objetivo_etapa_AAAA-MM` → `zero1_meta_vendas_frio_2026-11`
Conjunto/grupo: `publico_detalhe_posicionamento` → `lal-1-compradores_br_auto`
Anúncio: `crNN_formato_gancho_vN` → `cr03_tela-dividida_numero_v2` (o `formato` usa as chaves do CLAUDE.md)
Etapas: `frio`, `morno`, `quente`. Objetivos: `vendas`, `leads`, `mensagens`, `alcance`, `trafego`.
O nome do anúncio deve bater com `utm_content` e com `criativos[].nome` do JSON da campanha.
