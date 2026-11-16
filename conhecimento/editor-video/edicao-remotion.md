# Edição de retenção no Remotion

O editor final da agência é o Remotion (`ferramentas/remotion/`). O ffmpeg só enquadra o 9:16 (`cortar.py` gera
`NN-base.mp4`); a edição sai de `python ferramentas/remotion/editar.py <id>`, que lê o bloco `edicao` de cada corte.
Para mexer no visual, edite `ferramentas/remotion/src/` e use a skill `remotion-best-practices`.

## O que cada vídeo recebe (e por quê)

| Recurso | Regra | Por que retém |
|---|---|---|
| Gancho na tela | `gancho_tela`, até 7 palavras, 0 a 3,2 s, curiosidade concreta (número, erro, consequência) | decide se a pessoa fica nos 3 primeiros segundos |
| Corte seco nas pausas | pausa > 0,45 s sai; fica 0,12 s de respiro | ritmo de fala de criador, sem "ééé" |
| Zoom alternado | cada corte seco alterna 1,00 / 1,09 | esconde o pulo do corte e renova o quadro |
| Zoom de ênfase | `enfases`: 2 a 6 momentos (revelação, número, frase forte), no máximo 1 a cada 4 s | marca o ponto que importa |
| Legenda animada | 1 a 3 palavras por vez, a palavra falada pula; `destaques` (4 a 10 termos) ganham a cor da marca | 85% assiste sem som; destaque guia o olho |
| B-roll ("fundo interativo") | `broll`: 3 a 7 cenas de 1,5 a 3 s, nunca no gancho, respiro de 1,5 s entre elas | troca de imagem a cada 5 a 8 s segura a atenção |
| Gráfico animado | `tipo: grafico`, variantes erro / dica / numero / alerta / frase, `rotulo` ("ERRO Nº 1") + `titulo` (até 6 palavras) | lista e número viram capítulo visual |
| Banco de imagem/vídeo | `tipo: estoque`, `busca` em inglês, concreta e visual (Pexels com `PEXELS_API_KEY` no .env; senão Wikimedia; senão vira gráfico) | mostra o objeto/lugar citado |
| Efeitos sonoros | automáticos: whoosh no gancho e em cada B-roll, impacto grave no "erro", ding na "dica", estalo leve nos zooms | o som marca a transição; volume baixo |
| Barra de progresso | embaixo, na cor da marca | mostra que é curto e prende até o fim |
| Música | só da biblioteca `midia/musicas/` (faixas livres), com ducking (`musica.py`) | clima sem brigar com a voz |

## Estilo de marca
- Perfis com `estilo_video` em `dados/perfis/<perfil>.json` (ex.: Safe Internato = `safe`, vermelho `#E30613`:
  título branco grande com sombra, palavra falada em caixa vermelha).
- Se o pedido citar a marca, use o estilo e a cor dela. Senão, `padrao` (caixa branca no título, destaque amarelo).

## Cuidados (saúde / CFM)
- Sem imagem de paciente identificável, sangue explícito ou procedimento real chocante no B-roll.
- Gráfico de "erro" ensina o certo; nada de expor colega ou instituição.

## O que não fazemos aqui
- Gerar música ou imagem por IA paga (decisão do dono: só Claude + bancos livres).
- Trocar a ordem de imagem com áudio diferente.
