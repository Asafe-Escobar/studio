"""Contexto de mercado para cortes estratégicos: o que está em alta no nicho do podcast.

Ordem:
  1. --pesquisa <id> informada  -> usa dados/pesquisas/<id>.json
  2. já existe pesquisa do mesmo nicho (últimos 30 dias) -> usa a mais recente
  3. senão: a IA identifica o nicho e sugere perfis; perfis.py coleta dados reais pela API do Instagram
     (gera também uma pesquisa preliminar que aparece no Studio)

Uso: python ferramentas/podcast/mercado.py <id_corte> [--nicho "..."] [--pesquisa <id>] [--titulo "..."]
Grava midia/<id_corte>/mercado.json com {pesquisa_id, nicho, padroes, formatos, top_posts}.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comum import RAIZ, DADOS, pasta

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def slug(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def claude_json(prompt, modelo="sonnet"):
    claude = shutil.which("claude") or "claude"
    r = subprocess.run([claude, "-p", "--model", modelo, "--output-format", "text"], input=prompt,
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    m = re.search(r"\{[\s\S]*\}", r.stdout or "")
    return json.loads(m.group(0)) if m else None


def achar_pesquisa(nicho):
    alvo = set(slug(nicho).split("-")) - {"de", "da", "do", "e", "para", "em"}
    limite = datetime.now(timezone.utc) - timedelta(days=30)
    melhores = []
    for arq in (DADOS / "pesquisas").glob("*.json"):
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
        except Exception:
            continue
        palavras = set(slug(d.get("nicho", "")).split("-"))
        comum = len(alvo & palavras)
        try:
            criado = datetime.fromisoformat(str(d.get("criado_em", "")).replace("Z", "+00:00"))
        except Exception:
            criado = limite
        if comum and criado >= limite:
            melhores.append((comum, criado, d))
    melhores.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return melhores[0][2] if melhores else None


def resumir(d):
    posts = sorted(d.get("posts_referencia") or [], key=lambda p: -(p.get("outlier_score") or 0))[:15]
    return {
        "pesquisa_id": d.get("id"), "nicho": d.get("nicho"), "resumo": d.get("resumo"),
        "padroes": [{"titulo": p.get("titulo"), "descricao": p.get("descricao")} for p in d.get("padroes") or []],
        "formatos": [{"formato": f.get("formato"), "por_que": f.get("por_que_funciona")} for f in d.get("formatos") or []],
        "top_posts": [{"perfil": p.get("perfil"), "gancho": p.get("gancho"), "outlier": p.get("outlier_score"),
                       "views": p.get("views"), "url": p.get("url")} for p in posts],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--nicho", default="")
    ap.add_argument("--pesquisa", default="")
    ap.add_argument("--titulo", default="")
    args = ap.parse_args()
    p = pasta(args.id)
    destino = p / "mercado.json"

    d = None
    if args.pesquisa:
        arq = DADOS / "pesquisas" / f"{args.pesquisa}.json"
        d = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None
    nicho = args.nicho
    perfis = []
    if d is None and not nicho:
        trecho = ""
        tt = p / "transcricao.txt"
        if tt.exists():
            trecho = tt.read_text(encoding="utf-8")[:6000]
        r = claude_json(f"""Identifique o nicho de conteúdo deste podcast para Instagram (público brasileiro) e liste 14 perfis
profissionais de Instagram (contas comerciais ou de criador, BR de preferência) que publicam sobre esse tema e performam bem.
Misture grandes e médios. Responda SÓ JSON: {{"nicho": "...", "perfis": ["@usuario", ...]}}
Título: {args.titulo}
Trecho da transcrição:
{trecho}""")
        if r:
            nicho, perfis = r.get("nicho", ""), r.get("perfis", [])
    if d is None and nicho:
        d = achar_pesquisa(nicho)
        if d:
            print(f"usando pesquisa existente do nicho: {d.get('id')}", flush=True)
    if d is None and nicho:
        if not perfis:
            r = claude_json(f"""Liste 14 perfis profissionais de Instagram (BR de preferência, grandes e médios) que publicam sobre
"{nicho}" e performam bem. Responda SÓ JSON: {{"perfis": ["@usuario", ...]}}""")
            perfis = (r or {}).get("perfis", [])
        if perfis:
            pid = f"{datetime.now().strftime('%Y-%m-%d')}-{slug(nicho)[:40]}"
            print(f"coletando o mercado de '{nicho}' ({len(perfis)} perfis) -> pesquisa {pid}", flush=True)
            subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "instagram" / "perfis.py"), pid, *perfis, "--posts", "25"], cwd=RAIZ)
            subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "instagram" / "resumo.py"), pid, "--nicho", nicho], cwd=RAIZ)
            arq = DADOS / "pesquisas" / f"{pid}.json"
            d = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else None

    if not d:
        print("sem contexto de mercado (seguindo só pela qualidade do episódio)", flush=True)
        destino.write_text(json.dumps({"nicho": nicho or None}, ensure_ascii=False), encoding="utf-8")
        return
    ctx = resumir(d)
    destino.write_text(json.dumps(ctx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"mercado: nicho '{ctx['nicho']}', {len(ctx['top_posts'])} posts em alta, {len(ctx['padroes'])} padrões -> {destino}", flush=True)


if __name__ == "__main__":
    main()
