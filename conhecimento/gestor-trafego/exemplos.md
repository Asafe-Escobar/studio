# Exemplos de saída

> Exemplo de calibragem, não aprovado por cliente. Mostra o nível de detalhe esperado, não valores reais.

Cenário: conta nova de serviço local, vende por WhatsApp, verba e CPA ainda não informados.

```json
"trafego": {
  "orcamento_diario": null,
  "premissas": { "verba_mensal": null, "cpa_alvo": null, "conversoes_semana_estimadas": null },
  "rastreamento": {
    "pixel": null, "capi": null, "ga4": null,
    "eventos": ["conversa iniciada"],
    "pendencias": ["confirmar pixel instalado", "sem retorno de vendas do WhatsApp: resultado medido só até a conversa"]
  },
  "campanhas": [
    {
      "nome": "cliente_meta_mensagens_frio_2026-11",
      "plataforma": "meta",
      "etapa": "frio",
      "objetivo": "Engajamento > Mensagens (WhatsApp)",
      "evento_otimizacao": "conversa iniciada",
      "lance": "volume mais alto (sem limite de custo)",
      "publico": "Aberto, raio da região atendida (raio a pedir ao cliente)",
      "orcamento": null,
      "criativos": ["cr01_talking-head_dor_v1", "cr02_antes-depois_resultado_v1", "cr03_lista-top_numero_v1"],
      "metrica_decisao": "custo por conversa",
      "regra_corte": "pausar criativo com CTR < 0,8% após 2.000 impressões",
      "observacoes": "orçamento null: falta verba e CPA alvo"
    }
  ],
  "testes": [
    {
      "hipotese": "gancho de número reduz custo por conversa em relação a gancho de dor",
      "variavel": "gancho (cr01 vs cr03)",
      "metrica": "custo por conversa",
      "prazo": "7 dias ou 2.000 impressões por criativo",
      "criterio_vitoria": "menor custo por conversa com diferença registrada no relatório"
    }
  ]
}
```
