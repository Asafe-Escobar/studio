"""Cortes com minutagem definida pelo usuário, ou edição de um vídeo inteiro, sem passar pela IA.

Baixa (ou copia) a fonte, transcreve se houver legenda, grava dados/cortes/<id>.json e renderiza com cortar.py.

Uso:
  python ferramentas/podcast/manual.py <url-ou-arquivo> <id> --cortes '[{"inicio":"00:01:10","fim":"00:02:00","titulo":"..."}]'
  python ferramentas/podcast/manual.py <url-ou-arquivo> <id> --edicao            (vídeo inteiro ou --inicio/--fim)
Opções: --titulo, --modo blur|crop|original, --sem-legenda, --modelo small
  --pedido "como quero a edição" (IA monta o plano: trechos, enquadramento, legenda, música)
  --musica <arquivo em midia/musicas> [--volume 0.15]
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from comum import RAIZ, DADOS, pasta, original, duracao, para_segundos, ts

AQUI = Path(__file__).resolve().parent


def rodar(script, *args):
    print(f"\n== {script} {' '.join(args)}", flush=True)
    r = subprocess.run([sys.executable, str(AQUI / script), *args], cwd=RAIZ)
    if r.returncode != 0:
        sys.exit(f"Falhou: {script}")


def primeira_frase(palavras, ini, fim, limite=14):
    dentro = [p["w"] for p in palavras if ini - 0.05 <= p["s"] <= fim]
    return " ".join(dentro[:limite]) or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonte")
    ap.add_argument("id")
    ap.add_argument("--cortes", default="[]", help="JSON com [{inicio, fim, titulo}]")
    ap.add_argument("--edicao", action="store_true", help="edita o vídeo como um único corte")
    ap.add_argument("--inicio", default=None)
    ap.add_argument("--fim", default=None)
    ap.add_argument("--titulo", default=None)
    ap.add_argument("--modo", default="crop", choices=["blur", "crop", "original"])
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--pedido", default=None, help="pedido de edição em texto livre (só com --edicao)")
    ap.add_argument("--musica", default=None, help="arquivo em midia/musicas para fundo")
    ap.add_argument("--volume", default="0.15")
    args = ap.parse_args()

    rodar("baixar.py", args.fonte, args.id)
    fonte = original(args.id)
    total = duracao(fonte)

    if args.edicao:
        ini = para_segundos(args.inicio) if args.inicio else 0.0
        fim = para_segundos(args.fim) if args.fim else total
        pedidos = [{"inicio": ini, "fim": fim, "titulo": args.titulo or "Vídeo editado"}]
    else:
        pedidos = json.loads(args.cortes)
        if not pedidos:
            sys.exit("Nenhum corte informado.")

    cortes = []
    for n, c in enumerate(pedidos, 1):
        ini, fim = para_segundos(c["inicio"]), min(para_segundos(c["fim"]), total)
        if fim <= ini:
            sys.exit(f"Corte {n}: fim ({c['fim']}) precisa ser depois do início ({c['inicio']}).")
        cortes.append({
            "n": n, "titulo": c.get("titulo") or f"Corte {n}", "inicio": ts(ini), "fim": ts(fim),
            "duracao_s": round(fim - ini, 1), "gancho": None, "por_que": "Minutagem definida pelo usuário",
            "nota": None, "formato": "talking-head" if args.edicao else "entrevista-podcast",
            "legenda": None, "hashtags": [], "arquivo": None,
        })

    palavras = []
    plano = None
    if not args.sem_legenda or (args.edicao and args.pedido):
        rodar("transcrever.py", args.id, "--modelo", args.modelo)
        tj = pasta(args.id) / "transcricao.json"
        for seg in json.loads(tj.read_text(encoding="utf-8"))["segmentos"]:
            palavras.extend(seg["palavras"])
        if args.edicao and args.pedido:
            extra_lim = (["--inicio", args.inicio] if args.inicio else []) + (["--fim", args.fim] if args.fim else [])
            rodar("plano_edicao.py", args.id, "--pedido", args.pedido, *extra_lim)
            plano = json.loads((pasta(args.id) / "plano_edicao.json").read_text(encoding="utf-8"))
            c = cortes[0]
            c["trechos"] = plano["trechos"]
            c["inicio"], c["fim"] = plano["trechos"][0]["inicio"], plano["trechos"][-1]["fim"]
            c["duracao_s"] = round(sum(para_segundos(t["fim"]) - para_segundos(t["inicio"]) for t in plano["trechos"]), 1)
            c["por_que"] = plano.get("resumo") or "Edição pelo pedido"
            c["edicao"] = {k: plano.get(k) for k in ("gancho_tela", "destaques", "enfases", "cor", "estilo", "broll") if plano.get(k)}
            if plano.get("sfx") is False:
                c["edicao"]["sfx"] = False
            if not args.titulo and plano.get("titulo"):
                c["titulo"] = plano["titulo"]
            if plano.get("modo") in ("crop", "blur", "original"):
                args.modo = plano["modo"]
            if plano.get("legenda") is False:
                args.sem_legenda = True
            if plano.get("musica") and not args.musica:
                args.musica, args.volume = plano["musica"]["arquivo"], str(plano["musica"].get("volume") or 0.15)
        for c in cortes:
            ini_c = para_segundos((c.get("trechos") or [c])[0]["inicio"])
            c["gancho"] = primeira_frase(palavras, ini_c, para_segundos(c["fim"]))

    info = pasta(args.id) / "info.txt"
    titulo_fonte = None
    if info.exists():
        for linha in info.read_text(encoding="utf-8").splitlines():
            if linha.startswith("titulo:"):
                titulo_fonte = linha.split(":", 1)[1].strip()

    dados = {
        "id": args.id,
        "tipo": "cortes",
        "origem": "edicao" if args.edicao else "manual",
        "titulo": args.titulo or titulo_fonte or Path(args.fonte).stem,
        "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "fonte": {"url": args.fonte if "://" in args.fonte else None,
                  "arquivo": fonte.relative_to(RAIZ).as_posix(), "duracao_s": round(total, 1)},
        "resumo": ("Edição: " if args.edicao else f"{len(cortes)} cortes com minutagem escolhida. ")
                  + f"Enquadramento {args.modo}, {'sem' if args.sem_legenda else 'com'} legenda.",
        "cortes": cortes,
        "roteiros": [],
    }
    if plano:
        dados["pedido_edicao"] = {"texto": args.pedido, "resumo": plano.get("resumo"), "nao_feito": plano.get("nao_feito") or []}
        dados["resumo"] = f"Edição pelo pedido: {plano.get('resumo') or args.pedido}"
    destino = DADOS / "cortes" / f"{args.id}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON salvo: {destino}", flush=True)

    # Legenda de Instagram de cada corte (precisa da transcrição), em paralelo com a renderização.
    legendas = None if args.sem_legenda else subprocess.Popen([sys.executable, str(AQUI / "legendas_ig.py"), args.id], cwd=RAIZ)
    extra = ["--sem-legenda"] if args.sem_legenda else []
    rodar("cortar.py", args.id, "--modo", args.modo, *extra)
    if args.musica:
        print("\n== música de fundo", flush=True)
        subprocess.run([sys.executable, str(AQUI / "musica.py"), args.id, "--musica", args.musica, "--volume", str(args.volume)], cwd=RAIZ)
    if legendas and legendas.wait() != 0:
        print("aviso: as legendas de Instagram falharam; rode legendas_ig.py de novo", flush=True)
    print("PRONTO", flush=True)


if __name__ == "__main__":
    main()
