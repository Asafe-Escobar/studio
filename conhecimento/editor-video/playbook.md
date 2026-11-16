# Playbook do editor de vídeo

## O que faz um corte de podcast performar
1. **Primeira frase forte**: afirmação, pergunta ou número. Se precisa de contexto, corte antes ou não use.
2. **Ideia completa**: começo, meio e fim. O espectador sai com algo (opinião, dado, história, dica).
3. **Emoção**: risada, discordância, revelação, vulnerabilidade, indignação.
4. **Universalidade**: alguém que nunca ouviu o podcast entende e se importa.
5. **Duração**: 25-75s. Histórias podem ir a 90s se a tensão se mantém.

## Tipos de momento para procurar
- Opinião polêmica ("eu acho que faculdade...")
- História pessoal com virada
- Dado surpreendente
- Conselho prático em passos
- Discordância entre os participantes
- Frase de efeito citável
- Pergunta difícil e resposta honesta

## Nota (0-10)
- 9-10: gancho imediato, emoção forte, tema amplo, fecha bem.
- 7-8: bom conteúdo, gancho ok ou tema mais nichado.
- 5-6: útil, mas precisa de texto na tela para segurar.
- < 5: não entregar.

## Acabamento
- Vertical 1080x1920. Padrão: `crop`, que segue quem está falando (enquadrar.py: rosto + movimento da boca, pula junto com os cortes de câmera). `blur` só quando precisar mostrar todos no quadro ao mesmo tempo. `--centro` força o recorte fixo.
- Legenda grande, centro-baixo, 2-4 palavras por vez, palavras-chave destacadas.
- Título fixo no topo opcional (o gancho em texto).
- Áudio normalizado (-14 LUFS); corte silêncios longos se a ferramenta permitir.

## Títulos e legendas dos cortes
Título = o gancho em até 8 palavras. Legenda: contexto em 1 linha + CTA para o episódio completo.
