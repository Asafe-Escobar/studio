# Playbook do produtor de avatar

## Antes de gerar (trava)
Só começa se tiver tudo:
- [ ] Cliente, JSON de origem e qual roteiro (índice ou título).
- [ ] Consentimento válido em `consentimentos.md` cobrindo voz e/ou imagem, o canal (orgânico/anúncio) e a data atual.
- [ ] `voice_id` e `avatar_id` no `clientes/<cliente>/perfil.md` (ou passados pelo Diretor).
- [ ] Por cena ou vídeo único, e fundo (neutro ou green screen).
Faltou algo: pare e peça ao Diretor. Não gere "de teste" com a voz/imagem do cliente.

## Custo
- Antes de qualquer chamada paga ao muapi, rode `muapi_account_balance` e anote o saldo.
- Se a estimativa da tarefa passar de **US$ 0,50**, ou se o custo não for conhecido, confirme com o Diretor antes de gerar.
- Faça um teste curto (1 cena) antes do lote. Depois, rode o saldo de novo e informe o gasto real na entrega.
- Preço por chamada de ElevenLabs/HeyGen: a confirmar quando os MCPs forem conectados.

## Preparação da fala
- Use só o texto de `fala` das cenas, sem rubricas.
- Números por extenso quando a pronúncia puder errar ("R$ 1.500" → "mil e quinhentos reais").
- Vírgula = pausa curta; ponto = pausa média; "..." = pausa longa.
- Siglas soletradas com hífen se necessário ("C-P-A").
- Nomes próprios e marcas: siga a pronúncia do perfil do cliente; se não houver, pergunte.

## ElevenLabs (quando conectado)
- Modelo multilíngue mais recente, estabilidade ~0.45, similaridade ~0.8, estilo baixo.
- Gere por cena para facilitar edição; nomeie `cena-01.mp3`, `cena-02.mp3`.

## HeyGen (quando conectado)
- Avatar 9:16, fundo neutro ou green screen para composição.
- Um vídeo por roteiro; se as cenas mudam de visual, gere por cena e monte com ffmpeg.

## Fallback muapi (sem ElevenLabs/HeyGen)
- `muapi_audio_from_text` gera voz genérica, **não** o clone do cliente. Só com aval do Diretor, e diga isso na entrega.
- `muapi_edit_lipsync` sincroniza um vídeo real do cliente com o áudio. Exige consentimento de imagem.

## QA antes de entregar
- [ ] Ouvi o áudio inteiro: nomes, marcas, números e siglas pronunciados certo.
- [ ] Sem palavra cortada no início/fim de cena; pausas naturais.
- [ ] Lipsync: boca acompanha a fala, sem travar ou deformar o rosto.
- [ ] Vídeo 9:16 e duração conferidos com `ffprobe`.
- [ ] Duração real comparada com `duracao_s` do roteiro; se diferir mais de 10%, avise.
- [ ] Texto falado bate com a `fala` do roteiro (nada inventado ou pulado).
- [ ] Arquivos em `midia/<id>/avatar/` e caminho registrado no JSON (validado com `python -m json.tool`).
- [ ] Gasto do muapi informado.

## Rotulagem de IA nas plataformas
Meta e TikTok pedem rótulo de IA em vídeo/áudio realista gerado ou alterado por IA. Escopo exato e regra para anúncios:
**a confirmar**. Busca em 2026-11-12 não achou a página oficial, só fontes secundárias:
https://www.socialmediatoday.com/news/metas-new-disclosure-requirements-for-digitally-altered-ad-content-are-now/704266/ ·
https://www.engadget.com/tiktok-now-lets-creators-label-ai-generated-content-154536858.html
Até confirmar: na entrega, avise que a peça usa clone e precisa do rótulo de IA ao publicar/anunciar.

## Consentimento
Registro em `conhecimento/produtor-avatar/consentimentos.md`. Sem registro válido, não gera.
