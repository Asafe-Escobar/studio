# Playbook do roteirista

## Estrutura padrão de um vídeo curto (30-45s)
1. **Gancho (0-3s)**: para o dedo. Visual + fala + texto na tela dizendo a mesma coisa.
2. **Reforço (3-8s)**: por que a pessoa deveria ficar ("e o terceiro é o que quase ninguém faz").
3. **Corpo (8-35s)**: 1 a 3 pontos, cada um com exemplo concreto. Mude o visual a cada 2-4s.
4. **Virada/payoff**: entrega o prometido no gancho. Se prometeu 3, entrega 3.
5. **CTA (últimos 3-5s)**: uma ação só. Comentário com palavra-chave > "segue para mais".

## 12 modelos de gancho
1. Erro: "Você está [fazendo X] errado."
2. Número: "3 [coisas] que [resultado] em [prazo]."
3. Contradição: "[Crença comum] está te atrapalhando."
4. Segredo do bastidor: "O que [profissionais] não contam sobre [tema]."
5. Prova primeiro: mostre o resultado e diga "deixa eu te mostrar como".
6. Pergunta de identificação: "Você também [situação constrangedora específica]?"
7. Comparação: "R$ 50 vs R$ 500: qual [produto] vale mais?"
8. Aviso: "Não [ação] antes de ver isso."
9. História: "Em 2019 eu [situação ruim]. Hoje [resultado]."
10. Opinião forte: "Vou falar o que ninguém do [nicho] tem coragem de falar."
11. Desafio: "Testei [coisa] por 30 dias."
12. Reação: "Esse vídeo tem 2 milhões de views e está completamente errado."

## Retenção
- Loop aberto: prometa algo que só chega no fim ("e o último muda tudo").
- Corte seco a cada 2-4s; zoom de 110% em frases importantes.
- Texto na tela curto (até 6 palavras), no terço superior.
- Termine de forma que o início faça sentido de novo (loop) quando possível.

## Checklist antes de entregar
- [ ] O gancho funciona sem som (texto na tela)?
- [ ] Tem um único objetivo e um único CTA?
- [ ] Alguém do público entende sem contexto?
- [ ] O formato escolhido está justificado pela pesquisa?
- [ ] Dá para gravar com o que o cliente tem (celular, sem equipe)?
- [ ] Todo número na fala/tela tem fonte? Texto fora da base da tela (safe zone)?
- [ ] Nicho regulado ou anúncio? Passou pelo `compliance.md`?

## Carrossel no schema Roteiro
- `formato: "carrossel"`, `duracao_s: null`, `audio`: música sugerida ou `null`.
- `cenas` = slides: `tempo: "slide 1"`, `"slide 2"`... `visual` = layout/imagem, `texto_tela` = texto do slide, `fala: null`.
- Slide 1 = `gancho`. Último slide = `cta`. Uma ideia por slide.

## Quantidade por pedido (padrão interno, até o Diretor dizer outro)
- Pedido sem número: 3 roteiros, de preferência em formatos diferentes, justificados pela pesquisa.
- 1 gancho por roteiro em `gancho`. Para teste A/B, use `ganchos_alternativos` (opcional, só se pedirem).
- Se o briefing definir a rede, preencha `plataforma` (instagram | tiktok | shorts | todas) e siga `plataformas.md`.

## Números na fala
- Todo número dito ou escrito na tela precisa de fonte no briefing, na pesquisa ou no perfil do cliente.
- Sem fonte: reescreva sem o número ou deixe `[DADO A CONFIRMAR]` na fala, registre em `alertas` e avise o Diretor. Nunca estime.
- Risco de compliance também vai em `alertas`. `avatar` não é seu: deixe `null`.

## Arquivos de apoio
- `formatos.md`: as 14 chaves e como descrever o visual.
- `plataformas.md`: duração e safe zones com fonte oficial.
- `compliance.md`: o que não pode ir para fala/tela em nicho regulado e em anúncio.
- `exemplos.md`: roteiros de calibragem em JSON.
