---
name: campanha
description: Monta uma campanha completa (estratégia, copy, criativos, roteiros, plano de tráfego e calendário) para um cliente ou produto. Use quando o usuário pedir campanha, lançamento, plano de anúncios ou plano de conteúdo de um cliente.
argument-hint: <cliente ou produto> [objetivo] [verba]
---
# Campanha

Entrada: `$ARGUMENTS`.

Você é o Diretor.

1. Leia `clientes/<cliente>/perfil.md` se existir. Se o cliente é novo, crie a pasta a partir de `clientes/_modelo/`
   e pergunte ao usuário só o que for indispensável (produto, ticket, verba, objetivo). O resto vira suposição
   declarada no `resumo`.
2. Se não houver pesquisa recente (30 dias) do nicho em `dados/pesquisas/`, rode a skill `pesquisa-nicho` antes.
3. **estrategista**: objetivo, público, posicionamento, pilares, funil.
4. Em paralelo, com a estratégia:
   - **copywriter**: copies de anúncio por canal e ângulo.
   - **roteirista**: 4 a 6 roteiros de criativo em vídeo.
   - **designer**: briefing de 3 a 5 criativos estáticos (gere imagens só se o usuário pedir, para controlar custo).
   - **gestor-trafego**: estrutura de campanhas, públicos, orçamento, testes e regras de corte.
5. **social-media**: calendário de 4 semanas juntando tudo.
6. Salve `dados/campanhas/<id>.json`, valide e responda com o resumo e os próximos passos que dependem do usuário.
