"""Cortes de podcast escolhidos pela IA, num pipeline que não depende de agente segurando processo longo.

Etapas (cada uma pula se já foi feita):
  1. baixa o episódio            -> midia/<id>/original.*
  2. transcreve (faster-whisper) -> midia/<id>/transcricao.json/.txt
  3. a IA (Claude, chamada única) escolhe os melhores momentos a partir da transcrição e do playbook do editor
  4. grava dados/cortes/<id>.json (o Studio já mostra os cortes) e renderiza com cortar.py

Uso:
  python ferramentas/podcast/cortes_ia.py <url-ou-arquivo> <id> [--quantidade 8] [--min 30] [--max 75]
         [--modo blur|crop|original] [--sem-legenda] [--temas "..."] [--titulo "..."] [--modelo-ia sonnet]
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from comum import RAIZ, DADOS, pasta, original, duracao, para_segundos, ts

AQUI = Path(__file__).resolve().parent


def agora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def gravar(dados):
    destino = DADOS / "cortes" / f"{dados['id']}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def rodar(script, *args):
    print(f"\n== {script} {' '.join(args)}", flush=True)
    r = subprocess.run([sys.executable, str(AQUI / script), *args], cwd=RAIZ)
    if r.returncode != 0:
        sys.exit(f"Falhou: {script}")


def ajustar_fim(palavras, ini, fim, mn, mx):
    """Se o corte passou do máximo, termina no fim da última frase que cabe (ou exatamente no máximo)."""
    if fim - ini <= mx + 3:
        return fim
    finais = [p["e"] for p in palavras if ini + mn <= p["e"] <= ini + mx and p["w"][-1:] in ".?!"]
    return (finais[-1] + 0.3) if finais else ini + mx


def palavras_de(p):
    tj = p / "transcricao.json"
    if not tj.exists():
        return []
    return [w for s in json.loads(tj.read_text(encoding="utf-8"))["segmentos"] for w in s["palavras"]]


def bloco_mercado(m):
    if not m or not m.get("top_posts"):
        return ""
    return f"""
CORTES ESTRATÉGICOS: priorize momentos que repliquem o que está EM ALTA neste nicho agora (dados reais do Instagram).
Nicho: {m.get('nicho')}
Padrões que performam: {json.dumps(m.get('padroes') or [], ensure_ascii=False)}
Formatos que performam: {json.dumps(m.get('formatos') or [], ensure_ascii=False)}
Posts em alta (outlier = quantas vezes passou da média do próprio perfil):
{json.dumps(m.get('top_posts'), ensure_ascii=False, indent=0)}
Para cada corte, preencha "mercado": o padrão ou gancho em alta que ele replica, a url do post parecido e "alinhamento" 0-10.
A nota final pondera qualidade do momento (60%) e alinhamento com o mercado (40%). Evite temas que não aparecem no mercado,
a menos que o momento seja muito forte."""


def escolher(transcricao, total, args, titulo, mercado=None):
    playbook = (RAIZ / "conhecimento" / "editor-video" / "playbook.md").read_text(encoding="utf-8")
    aprend = RAIZ / "conhecimento" / "editor-video" / "aprendizados.md"
    aprend = aprend.read_text(encoding="utf-8") if aprend.exists() else ""
    prompt = f"""Você é o editor de vídeo da Agência Zero1. Escolha os {args.quantidade} melhores cortes deste episódio
para Reels/TikTok/Shorts. Não use ferramentas: responda SÓ com um JSON válido, sem texto antes ou depois.

Regras (playbook e aprendizados do editor; aprendizados prevalecem):
{playbook}
{aprend}

Restrições deste pedido:
- Cada corte entre {args.min} e {args.max} segundos. Comece no início de uma frase forte e termine no fim de uma ideia.
- Use os tempos da transcrição (formato HH:MM:SS.s). O episódio tem {ts(total)}.
- Não sobreponha cortes. Varie os temas. Nota 0-10; não entregue nada abaixo de 6.
{f'- Priorize: {args.temas}' if args.temas else ''}
{bloco_mercado(mercado)}

Formato da resposta:
{{"resumo": "do que o episódio trata, 2 frases",
  "cortes": [{{"titulo": "gancho em até 8 palavras", "inicio": "00:12:03.4", "fim": "00:13:01.0",
    "gancho": "primeira frase dita no corte", "por_que": "por que vai performar",
    "nota": 8.5, "legenda": "contexto em 1 linha + CTA para o episódio completo", "hashtags": ["#..."],
    "mercado": {{"padrao": "qual padrão/gancho em alta este corte replica (ou null)", "referencia_url": "url do post em alta parecido (ou null)", "alinhamento": 0}},
    "edicao": {{"gancho_tela": "título do topo nos 3 primeiros segundos, até 7 palavras, curiosidade concreta",
      "destaques": ["4 a 8 palavras-chave ditas no corte que ganham cor na legenda"],
      "enfases": ["00:12:20.1 (2 a 5 momentos de impacto para zoom, tempos da transcrição)"]}}}}]}}

Episódio: {titulo}
Transcrição:
{transcricao}"""
    claude = shutil.which("claude") or "claude"
    print(f"\n== IA escolhendo {args.quantidade} cortes ({args.modelo_ia})…", flush=True)
    r = subprocess.run([claude, "-p", "--model", args.modelo_ia, "--output-format", "text"], input=prompt,
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, shell=sys.platform == "win32" and claude == "claude")
    saida = r.stdout.strip()
    m = re.search(r"\{[\s\S]*\}", saida)
    if r.returncode != 0 or not m:
        sys.exit(f"A IA não devolveu JSON. Saída: {saida[:500]} {r.stderr[:500]}")
    return json.loads(m.group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonte")
    ap.add_argument("id")
    ap.add_argument("--quantidade", type=int, default=8)
    ap.add_argument("--min", type=float, default=30)
    ap.add_argument("--max", type=float, default=75)
    ap.add_argument("--modo", default="crop", choices=["blur", "crop", "original"])
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--temas", default="")
    ap.add_argument("--titulo", default=None)
    ap.add_argument("--modelo-ia", default="sonnet")
    ap.add_argument("--nicho", default="", help="nicho do podcast para buscar o que está em alta (vazio = a IA identifica)")
    ap.add_argument("--pesquisa", default="", help="id de uma pesquisa de mercado já feita")
    ap.add_argument("--sem-mercado", action="store_true")
    ap.add_argument("--modelo", default="small", help="modelo do whisper")
    args = ap.parse_args()

    p = pasta(args.id)
    base = {"id": args.id, "tipo": "cortes", "origem": "ia", "status": "baixando", "titulo": args.titulo or "Podcast",
            "criado_em": agora(), "fonte": {"url": args.fonte if "://" in args.fonte else None, "arquivo": None, "duracao_s": None},
            "resumo": "Baixando o episódio…", "cortes": [], "roteiros": []}
    gravar(base)

    if not list(p.glob("original.*")):
        rodar("baixar.py", args.fonte, args.id)
    else:
        print("episódio já baixado, pulando", flush=True)
    fonte = original(args.id)
    total = duracao(fonte)
    titulo = args.titulo
    info = p / "info.txt"
    if not titulo and info.exists():
        titulo = next((l.split(":", 1)[1].strip() for l in info.read_text(encoding="utf-8").splitlines() if l.startswith("titulo:")), None)
    base.update(titulo=titulo or fonte.stem, status="transcrevendo",
                fonte={**base["fonte"], "arquivo": fonte.relative_to(RAIZ).as_posix(), "duracao_s": round(total, 1)},
                resumo=f"Transcrevendo {ts(total)} de episódio. Os cortes aparecem aqui assim que a IA escolher os momentos.")
    gravar(base)

    if (p / "transcricao.txt").exists():
        print("transcrição já existe, pulando", flush=True)
    else:
        rapido = False
        if re.search(r"youtube\.com|youtu\.be", args.fonte):
            # Legenda automática do YouTube tem tempo por palavra: segundos em vez de minutos de Whisper.
            print("\n== legenda do YouTube (atalho rápido)", flush=True)
            rapido = subprocess.run([sys.executable, str(AQUI / "legendas_yt.py"), args.fonte, args.id], cwd=RAIZ).returncode == 0
        if not rapido:
            rodar("transcrever.py", args.id, "--modelo", args.modelo)

    mercado = None
    if not args.sem_mercado:
        base.update(status="mercado", resumo="Buscando o que está em alta no nicho para escolher cortes estratégicos…")
        gravar(base)
        print("\n== mercado: o que está em alta no nicho", flush=True)
        extra_m = (["--nicho", args.nicho] if args.nicho else []) + (["--pesquisa", args.pesquisa] if args.pesquisa else [])
        subprocess.run([sys.executable, str(AQUI / "mercado.py"), args.id, "--titulo", base["titulo"], *extra_m], cwd=RAIZ)
        arq_m = p / "mercado.json"
        mercado = json.loads(arq_m.read_text(encoding="utf-8")) if arq_m.exists() else None
        if mercado and mercado.get("pesquisa_id"):
            base["mercado"] = {"nicho": mercado.get("nicho"), "pesquisa_id": mercado.get("pesquisa_id")}

    base.update(status="escolhendo", resumo="A IA está escolhendo os melhores momentos…")
    gravar(base)
    escolha = escolher((p / "transcricao.txt").read_text(encoding="utf-8"), total, args, base["titulo"], mercado)

    cortes = []
    palavras = palavras_de(p)
    for c in escolha.get("cortes", []):
        try:
            ini, fim = para_segundos(c["inicio"]), min(para_segundos(c["fim"]), total)
        except Exception:
            continue
        fim = ajustar_fim(palavras, ini, fim, args.min, args.max)
        if fim - ini < 5:
            continue
        cortes.append({"n": len(cortes) + 1, "titulo": c.get("titulo"), "inicio": ts(ini), "fim": ts(fim),
                       "duracao_s": round(fim - ini, 1), "gancho": c.get("gancho"), "por_que": c.get("por_que"),
                       "nota": c.get("nota"), "formato": "entrevista-podcast", "legenda": c.get("legenda"),
                       "hashtags": c.get("hashtags") or [], "mercado": c.get("mercado"), "edicao": c.get("edicao"), "arquivo": None})
    if not cortes:
        sys.exit("A IA não devolveu cortes válidos.")
    cortes.sort(key=lambda c: -(c["nota"] or 0))
    for i, c in enumerate(cortes, 1):
        c["n"] = i
    base.update(status="renderizando", resumo=escolha.get("resumo") or base["resumo"], cortes=cortes)
    gravar(base)
    print(f"{len(cortes)} cortes escolhidos; renderizando…", flush=True)

    # Legenda de Instagram de cada corte, escrita em paralelo com a renderização.
    legendas = subprocess.Popen([sys.executable, str(AQUI / "legendas_ig.py"), args.id], cwd=RAIZ)
    extra = ["--sem-legenda"] if args.sem_legenda else []
    rodar("cortar.py", args.id, "--modo", args.modo, *extra)
    if legendas.wait() != 0:
        print("aviso: as legendas de Instagram falharam; rode legendas_ig.py de novo", flush=True)
    final = json.loads((DADOS / "cortes" / f"{args.id}.json").read_text(encoding="utf-8"))
    final["status"] = "pronto"
    gravar(final)
    print("PRONTO", flush=True)


if __name__ == "__main__":
    main()
