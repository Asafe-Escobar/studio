# Exemplos de roteiro

> **Exemplo de calibragem, não aprovado por cliente.** Mostra nível de detalhe e formato do JSON. Não copie as falas. Roteiros aprovados de verdade entram acima destes, com cliente e data.

## 1. Tela dividida (exemplo de calibragem, não aprovado por cliente)
```json
{
  "titulo": "O erro no café da manhã de quem treina cedo",
  "formato": "tela-dividida",
  "duracao_s": 30,
  "objetivo": "alcance",
  "gancho": "Você treina às 6h e come isso antes? Para.",
  "cenas": [
    { "tempo": "0-3s", "visual": "CIMA: eu, plano fechado, apontando para baixo. BAIXO: close do prato do café da manhã", "fala": "Você treina às 6h e come isso antes? Para.", "texto_tela": "Treina cedo? Para." },
    { "tempo": "3-8s", "visual": "CIMA: eu falando. BAIXO: mão afastando o prato", "fala": "Tem um detalhe que faz muita gente passar mal no treino.", "texto_tela": "O detalhe que ninguém fala" },
    { "tempo": "8-22s", "visual": "CIMA: eu falando, jump cuts. BAIXO: montagem da troca do prato, passo a passo", "fala": "[ponto técnico validado pelo especialista do cliente]", "texto_tela": "Troque por isso" },
    { "tempo": "22-30s", "visual": "CIMA: eu sorrindo. BAIXO: prato novo pronto", "fala": "Comenta CAFÉ que eu te mando 3 opções prontas.", "texto_tela": "Comenta CAFÉ" }
  ],
  "cta": "Comenta CAFÉ que eu te mando 3 opções prontas",
  "legenda": "Treino cedo pede outro café da manhã. Comenta CAFÉ que eu te mando as opções.",
  "hashtags": ["#treinocedo"],
  "audio": "voz original",
  "referencia_url": null
}
```
A fala técnica fica como marcador até o cliente validar. Nenhum número sem fonte.

## 2. Carrossel, convenção cenas = slides (exemplo de calibragem, não aprovado por cliente)
```json
{
  "titulo": "4 sinais de que sua planilha financeira não funciona",
  "formato": "carrossel",
  "duracao_s": null,
  "objetivo": "engajamento",
  "gancho": "Planilha bonita, conta no vermelho?",
  "cenas": [
    { "tempo": "slide 1", "visual": "Fundo claro, print desfocado de planilha, título grande no centro", "fala": null, "texto_tela": "Planilha bonita, conta no vermelho?" },
    { "tempo": "slide 2", "visual": "Número 1 grande à esquerda, frase à direita", "fala": null, "texto_tela": "1. Você só anota, nunca revisa" },
    { "tempo": "slide 3", "visual": "Mesmo layout", "fala": null, "texto_tela": "2. Não tem categoria de imprevisto" },
    { "tempo": "slide 4", "visual": "Mesmo layout", "fala": null, "texto_tela": "3. Atualiza só no fim do mês" },
    { "tempo": "slide 5", "visual": "Mesmo layout, cor de destaque (melhor item por último)", "fala": null, "texto_tela": "4. Não decide o destino da sobra" },
    { "tempo": "slide 6", "visual": "Foto do cliente + palavra-chave grande", "fala": null, "texto_tela": "Comenta PLANILHA e recebe o modelo" }
  ],
  "cta": "Comenta PLANILHA e recebe o modelo",
  "legenda": "Salva para revisar a sua no fim de semana.",
  "hashtags": ["#financaspessoais"],
  "audio": null,
  "referencia_url": null
}
```
