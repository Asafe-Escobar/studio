"""Transforma o pedido de edição em texto livre num plano que o renderizador executa.

Lê a transcrição com tempos (midia/<id>/transcricao.json) e o pedido do usuário, faz UMA chamada à IA e grava
midia/<id>/plano_edicao.json:
  {"titulo", "trechos": [{"inicio","fim","motivo"}], "modo": crop|blur|original|null, "legenda": true|false|null,
   "musica": {"arquivo": "<nome em midia/musicas> ou null", "volume": 0.15} | null, "nao_feito": ["..."], "resumo": "..."}

Uso: python ferramentas/podcast/plano_edicao.py <id> --pedido "tira o começo, corta a parte do erro, música calma"
     [--inicio 00:10 --fim 02:00] [--modelo-ia sonnet]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

from comum import RAIZ, MIDIA, pasta, ts, para_segundos

BIBLIOTECA = MIDIA / "musicas"
EXT_MUSICA = {".mp3", ".m4a", ".wav", ".aac", ".ogg"}


def musicas():
    if not BIBLIOTECA.exists():
        return []
    return sorted(p.name for p in BIBLIOTECA.iterdir() if p.suffix.lower() in EXT_MUSICA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--pedido", required=True)
    ap.add_argument("--inicio", default=None)
    ap.add_argument("--fim", default=None)
    ap.add_argument("--modelo-ia", default="sonnet")
    args = ap.parse_args()

    p = pasta(args.id)
    tj = json.loads((p / "transcricao.json").read_text(encoding="utf-8"))
    total = float(tj.get("duracao_s") or 0)
    lim_ini = para_segundos(args.inicio) if args.inicio else 0.0
    lim_fim = para_segundos(args.fim) if args.fim else total
    linhas = [f"[{ts(s['s'])} - {ts(s['e'])}] {s['texto'].strip()}" for s in tj["segmentos"]
              if s["e"] >= lim_ini and s["s"] <= lim_fim]
    lista_musicas = musicas()
    marcas = []
    for arq in sorted((RAIZ / "dados" / "perfis").glob("*.json")):
        try:
            pf = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        if pf.get("estilo_video"):
            ev = pf["estilo_video"]
            marcas.append(f"  - {pf.get('nome')} ({pf.get('instagram')}): estilo \"{ev.get('estilo')}\", cor {ev.get('cor')}")
    marcas = chr(10).join(marcas) or "  (nenhuma)"
    arq_aprend = RAIZ / "conhecimento" / "editor-video" / "aprendizados.md"
    aprend = arq_aprend.read_text(encoding="utf-8") if arq_aprend.exists() else ""

    prompt = f"""Você é o editor de vídeo da Agência Zero1. Transforme o pedido de edição abaixo num plano executável.
Não use ferramentas: responda SÓ com um JSON válido, sem texto antes ou depois.

Pedido do usuário: {args.pedido}

O que dá para fazer: escolher os trechos que ficam (em ordem; tudo fora deles sai), enquadramento
(crop = vertical 9:16 seguindo quem fala; blur = vertical com fundo desfocado, bom para 2+ pessoas; original = mantém),
legenda queimada (sim/não), música de fundo da biblioteca e volume (0.05 a 0.4; padrão 0.15; a música já abaixa sozinha quando alguém fala).
A edição final é feita no Remotion e você também define:
- "gancho_tela": título curto (até 7 palavras, sem ponto final) que aparece no topo nos 3 primeiros segundos. Precisa
  gerar curiosidade ou prometer algo concreto (número, erro, segredo, consequência). Nada genérico.
- "destaques": 4 a 10 palavras-chave ditas no vídeo que ganham cor na legenda (termos técnicos, números, a palavra da virada).
- "enfases": 2 a 6 momentos (tempo HH:MM:SS.s da transcrição) para zoom de ênfase: revelação, número, frase de impacto.
- "cor": cor de destaque em hex (padrão "#FFD400").
- "estilo": "padrao" ou "safe". Estilos de marca cadastrados (se o pedido citar a marca, use o estilo e a cor dela):
{marcas}
- "sfx": true (padrão: whoosh nas transições, impacto no "erro", ding na dica, estalo nos zooms) ou false se o pedido não quiser efeito sonoro.
- "broll": 3 a 7 cenas de apoio que cobrem a tela por 1,5 a 3 s enquanto a fala continua ("fundo interativo").
  Nunca nos primeiros 3 s (gancho). Cada cena é de um tipo:
  * banco de imagens/vídeos: {{"t": "HH:MM:SS.s", "dur": 2.2, "tipo": "estoque", "busca": "termo EM INGLÊS, concreto e visual (ex.: surgeon scrubbing hands, operating room lights)", "titulo": "texto curto de reserva"}}
  * gráfico animado: {{"t": "...", "dur": 2.0, "tipo": "grafico", "variante": "erro|dica|numero|alerta|frase", "rotulo": "ERRO Nº 1", "titulo": "até 6 palavras"}}
  Use gráfico para listas, números e frases de impacto ("Erro número um" -> variante erro, rótulo "ERRO Nº 1");
  use banco para o objeto/lugar citado na fala. Sem imagem de paciente identificável nem sangue explícito.
Pausas e respiros já são cortados automaticamente e a câmera alterna o zoom a cada corte seco; não precisa pedir.
O que NÃO dá para fazer aqui (coloque em "nao_feito"): gerar música (música só da biblioteca), trocar a ordem de imagem com áudio diferente.

Regras (aprendizados do editor prevalecem):
{aprend}
- Use os tempos da transcrição (HH:MM:SS.s). Cada trecho começa no início de uma frase e termina no fim de uma ideia.
- Respeite o limite: de {ts(lim_ini)} a {ts(lim_fim)}. Se o pedido não fala em cortar nada, devolva um trecho só com tudo.
- "modo", "legenda" e "musica" só se o pedido falar disso; senão null.
- Música: escolha pelo nome do arquivo o que combina com o pedido. Biblioteca: {", ".join(lista_musicas) or "(vazia: musica = null e explique em nao_feito)"}

Formato:
{{"titulo": "título curto do vídeo", "resumo": "o que foi feito, 1 frase",
  "trechos": [{{"inicio": "00:00:03.3", "fim": "00:00:41.0", "motivo": "..."}}],
  "modo": null, "legenda": null, "musica": {{"arquivo": "nome.mp3", "volume": 0.15}},
  "gancho_tela": "3 erros que te tiram do campo", "destaques": ["campo", "estéril"], "enfases": ["00:00:12.4"],
  "cor": "#FFD400", "estilo": "padrao", "broll": [], "nao_feito": []}}

Transcrição:
{chr(10).join(linhas)}"""

    claude = shutil.which("claude") or "claude"
    print(f"== IA lendo o pedido de edição ({args.modelo_ia})…", flush=True)
    r = subprocess.run([claude, "-p", "--model", args.modelo_ia, "--output-format", "text"], input=prompt,
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ,
                       shell=sys.platform == "win32" and claude == "claude")
    m = re.search(r"\{[\s\S]*\}", r.stdout or "")
    if r.returncode != 0 or not m:
        sys.exit(f"A IA não devolveu o plano. {(r.stdout or '')[:400]} {(r.stderr or '')[:400]}")
    plano = json.loads(m.group(0))

    # Sanidade: trechos dentro do limite e em ordem; música precisa existir.
    trechos = []
    for t in plano.get("trechos") or []:
        a = max(para_segundos(t["inicio"]), lim_ini)
        b = min(para_segundos(t["fim"]), lim_fim)
        if b - a >= 0.5:
            trechos.append({"inicio": ts(a), "fim": ts(b), "motivo": t.get("motivo")})
    plano["trechos"] = sorted(trechos, key=lambda t: para_segundos(t["inicio"])) or [{"inicio": ts(lim_ini), "fim": ts(lim_fim), "motivo": "vídeo inteiro"}]
    mu = plano.get("musica")
    if mu and mu.get("arquivo") not in lista_musicas:
        plano.setdefault("nao_feito", []).append(f"música '{mu.get('arquivo')}' não está na biblioteca")
        plano["musica"] = None
    plano["pedido"] = args.pedido
    (p / "plano_edicao.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    dur = sum(para_segundos(t["fim"]) - para_segundos(t["inicio"]) for t in plano["trechos"])
    print(f"plano: {len(plano['trechos'])} trecho(s), {dur:.0f}s · {plano.get('resumo', '')}", flush=True)
    for x in plano.get("nao_feito") or []:
        print(f"   não feito: {x}", flush=True)


if __name__ == "__main__":
    main()
