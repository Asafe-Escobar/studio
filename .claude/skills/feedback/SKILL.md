---
name: feedback
description: Registra o feedback do dono da agência sobre uma entrega (aprovou, reprovou, pediu ajuste) e treina o agente responsável, gravando a regra nos aprendizados dele. Use quando o usuário avaliar um roteiro, corte, copy, criativo ou plano.
argument-hint: <agente ou entrega> <o que achou>
---
# Feedback → treinamento

Entrada: `$ARGUMENTS`.

1. Identifique o agente responsável (roteirista, copywriter, editor-video etc.) e o cliente, se houver.
2. Transforme o comentário em uma **regra reutilizável**, curta e verificável.
   Ex.: "esse gancho ficou fraco" → "Ganchos de [cliente] devem citar número ou situação concreta nos 2 primeiros segundos".
3. Grave em `conhecimento/<agente>/aprendizados.md`: `- AAAA-MM-DD [cliente/geral] regra (motivo)`.
   Se for específico do cliente, grave também em `clientes/<cliente>/perfil.md` na seção "Aprovado/Reprovado".
4. Se o usuário pediu ajuste, acione o agente para refazer a entrega aplicando a regra e atualize o JSON em `dados/`.
5. Confirme ao usuário a regra registrada, em uma linha.
