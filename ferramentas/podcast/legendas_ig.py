"""Escreve a legenda de Instagram de cada corte (uma chamada de IA para todos), a partir da fala exata do corte.

Uso: python ferramentas/podcast/legendas_ig.py <id> [--perfil @medsafebrasil] [--modelo sonnet]
Grava em dados/cortes/<id>.json, em cada corte: legenda (pronta para colar), hashtags e titulo_capa.
Segue conhecimento/copywriter/ e conhecimento/social-media/ (aprendizados prevalecem).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

from comum import RAIZ, DADOS, pasta, para_segundos

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def ler(rel):
    p = RAIZ / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def fala(palavras, ini, fim):
    return " ".join(p["w"] for p in palavras if ini - 0.1 <= p["s"] <= fim)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--perfil", default="")
    ap.add_argument("--modelo", default="sonnet")
    args = ap.parse_args()

    arq = DADOS / "cortes" / f"{args.id}.json"
    d = json.loads(arq.read_text(encoding="utf-8"))
    palavras = []
    tj = pasta(args.id) / "transcricao.json"
    if tj.exists():
        for s in json.loads(tj.read_text(encoding="utf-8"))["segmentos"]:
            palavras.extend(s["palavras"])

    cortes = []
    for c in d.get("cortes", []):
        ini, fim = para_segundos(c["inicio"]), para_segundos(c["fim"])
        cortes.append({"n": c["n"], "titulo": c.get("titulo"), "fala": fala(palavras, ini, fim)[:2500] or c.get("gancho")})

    mercado = ""
    arq_m = pasta(args.id) / "mercado.json"
    if arq_m.exists():
        m = json.loads(arq_m.read_text(encoding="utf-8"))
        if m.get("top_posts"):
            mercado = ("Ganchos que estão EM ALTA neste nicho agora (dados reais do Instagram; use o mesmo tipo de abertura, sem copiar):\n"
                       + "\n".join(f"- {p.get('gancho')} ({p.get('outlier')}x a média de {p.get('perfil')})" for p in m["top_posts"][:12] if p.get("gancho")))
    prompt = f"""Você é o copywriter e social media da Agência Zero1. Escreva a legenda de Instagram de cada corte abaixo.
Não use ferramentas. Responda SÓ com JSON válido, sem texto antes ou depois.

Regras da agência (aprendizados prevalecem sobre playbooks):
--- copywriter/playbook ---
{ler('conhecimento/copywriter/playbook.md')}
--- copywriter/aprendizados ---
{ler('conhecimento/copywriter/aprendizados.md')}
--- social-media/aprendizados ---
{ler('conhecimento/social-media/aprendizados.md')}

Formato de cada legenda (Instagram, Reels):
- Linha 1: gancho forte que aparece antes do "mais" (até ~90 caracteres). Nada de "Sabe aquele momento", pergunta retórica vazia ou emoji no começo.
- Linhas 2 a 4: contexto concreto do que é dito no corte, com palavras do próprio corte. Frases curtas, quebra de linha entre ideias.
- CTA que gera comentário ou salvamento ligado ao tema (ex.: pergunta de opinião específica), e chamada para o episódio completo.
- Sem inventar números, nomes ou fatos que não estão na fala. Português do Brasil, sem travessão em excesso, sem "não é X, é Y".
- hashtags: 4 a 6, específicas do tema (misture 2 amplas e 2 a 4 de nicho), sem repetir a mesma lista em todos os cortes.
- titulo_capa: texto curto para a capa do Reels (até 6 palavras).
{f'- Perfil que vai postar: {args.perfil}' if args.perfil else ''}

{mercado}
Episódio: {d.get('titulo')}
Resumo: {d.get('resumo')}

Cortes (fala transcrita):
{json.dumps(cortes, ensure_ascii=False, indent=1)}

Resposta: {{"legendas": [{{"n": 1, "legenda": "texto com \\n entre linhas", "hashtags": ["#..."], "titulo_capa": "..."}}]}}"""

    claude = shutil.which("claude") or "claude"
    print(f"escrevendo {len(cortes)} legendas ({args.modelo})…", flush=True)
    r = subprocess.run([claude, "-p", "--model", args.modelo, "--output-format", "text"], input=prompt,
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)
    m = re.search(r"\{[\s\S]*\}", r.stdout or "")
    if r.returncode != 0 or not m:
        sys.exit(f"A IA não devolveu JSON: {(r.stdout or '')[:400]} {(r.stderr or '')[:400]}")
    por_n = {int(x["n"]): x for x in json.loads(m.group(0)).get("legendas", [])}

    d = json.loads(arq.read_text(encoding="utf-8"))  # relê: o render pode ter atualizado arquivos no meio
    feitos = 0
    for c in d.get("cortes", []):
        x = por_n.get(int(c["n"]))
        if not x:
            continue
        c["legenda"] = x.get("legenda", "").strip()
        c["hashtags"] = [h if h.startswith("#") else "#" + h for h in x.get("hashtags", [])]
        c["titulo_capa"] = x.get("titulo_capa")
        feitos += 1
    arq.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {feitos} legendas em {arq}")


if __name__ == "__main__":
    main()
