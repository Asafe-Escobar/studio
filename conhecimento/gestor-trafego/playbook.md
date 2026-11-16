# Playbook do gestor de tráfego

Arquivos de apoio (ler quando a tarefa tocar o tema): `rastreamento.md` (checklist, UTMs, nomenclatura),
`specs-plataformas.md` (limites e políticas com fonte), `exemplos.md` (calibragem de saída).

## Perguntas obrigatórias
Verba mensal, ticket médio, margem, CPA máximo aceitável (= margem × % que topa investir), pixel/CAPI e
eventos configurados, histórico de campanhas, LTV, se vende online ou via direct/WhatsApp, região atendida,
categoria especial (crédito/finanças, imóvel, emprego, política). Faltou dado: `null` + pergunta ao Diretor.

## Verba mínima (decida a estrutura pela conta, não pelo gosto)
- Meta sai do aprendizado com ~50 eventos de otimização na semana após a última edição significativa
  (fonte em `specs-plataformas.md`). Verba semanal por conjunto para isso ≈ 50 × CPA alvo.
- Se a verba não cobre 50 × CPA na semana: otimize por um evento mais frequente (ex.: AddToCart, Lead,
  conversa iniciada) ou reduza conjuntos. Nunca divida verba que não fecha nem um conjunto.
- Orçamento diário mínimo por conjunto ≈ 1 a 2× o CPA alvo.
- Verba que não sustenta uma plataforma bem: uma plataforma só. Regra de escolha: demanda existe e é
  buscada → Google Search; demanda precisa ser criada → Meta.
- Registre a conta no `resumo` ou nas observações: "verba X ÷ CPA Y = Z conversões/semana → estrutura W".

## Meta Ads
- **Vendas com histórico (50+ conversões/semana)**: Advantage+ Sales, 1 campanha, 5-10 criativos.
- **Conta nova ou pouco volume**: CBO, 2-3 conjuntos (aberto, interesse, lookalike/remarketing), 3-5 criativos cada.
- **Mensagens (WhatsApp/direct)**: objetivo Engajamento > Mensagens, criativos com CTA para conversar.
- **Remarketing**: engajou 30-90 dias, visitou site 30 dias; prova social e objeções.
- **Categoria especial**: declare na campanha; segmentação fica restrita (ver `specs-plataformas.md`).
  Planeje com público amplo e criativo fazendo a segmentação.

## Google Ads
- Search primeiro: palavras de intenção ("comprar", "preço", "perto de mim"), correspondência de frase/exata,
  negativas desde o dia 1.
- **Estrutura Search**: 1 campanha por objetivo/região; grupos por tema de intenção (ex.: produto, problema,
  concorrente, marca). Cada grupo com palavras do mesmo tema e RSA que repete o termo no título.
  Marca em campanha separada para não inflar o resultado.
- **Lances**: conta sem conversões começa em Maximizar cliques com limite de CPC ou Maximizar conversões;
  com histórico, CPA desejado. O Google recomenda avaliar CPA desejado em janela de 30 dias com 30+
  conversões e evitar trocar a meta no meio de um ciclo de conversão (fonte em `specs-plataformas.md`).
  Meta de CPA baixa demais reduz volume.
- **Termos de pesquisa**: revisar semanalmente; termo irrelevante vira negativa.
- PMax para e-commerce com feed ou depois de ter conversões.
- **Demand Gen / YouTube**: remarketing e topo com cortes de podcast. Só depois que Search estiver rodando.

## TikTok Ads
- Spark Ads com posts orgânicos que já performaram; criativo nativo (cara de criador). Em Spark Ads a
  legenda vem do post orgânico: ajuste no post antes de impulsionar.
- Conta nova: 1 campanha, 1-2 grupos amplos, 3-5 vídeos por grupo. Mesma conta de verba mínima do Meta.
- Gancho visual no primeiro segundo; vídeo com cara de anúncio cai rápido.

## Regras de otimização (ponto de partida)
- Criativo: pausar com CTR < 0,8% depois de 2.000 impressões ou CPA > 2× alvo depois de gastar 1,5× o CPA.
- Escalar 20-30% a cada 3 dias quando CPA estiver abaixo da meta.
- Não mexer em conjunto em aprendizado por 3-5 dias. Pausar, trocar evento, público ou criativo reinicia o aprendizado.
- Fadiga: frequência > 3 em 7 dias no frio → novo criativo.

## Testes
Ordem de impacto: criativo (gancho) > oferta > público > posicionamento. Uma variável por teste, hipótese escrita
("trocar gancho de dor por gancho de número reduz CPA em Meta frio"), métrica, prazo e critério de vitória.

## Métricas por etapa
Topo: CPM, ThruPlay, CTR. Meio: CPC, taxa de conversão da página. Fundo: CPA, ROAS, custo por conversa.

## Benchmarks (CPM, CPC, CPL, CPA)
Preencher com dados do cliente. Sem fonte oficial datada para o mercado brasileiro até 2026-11-12.
Formato de registro: `- AAAA-MM-DD [cliente] plataforma | objetivo | CPM | CPC | CTR | CPL/CPA | período | fonte (export do gerenciador)`.
Até existir histórico, a meta vem da conta de margem (CPA máximo), nunca de média de mercado.
