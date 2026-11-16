"""Renderiza um carrossel de Instagram (PNG 1080x1350 por slide) a partir de dados/carrosseis/<id>.json.

Uso:
  python ferramentas/design/carrossel.py <id>
  python ferramentas/design/carrossel.py <id> --de-roteiro dados/pesquisas/<pid>.json --indice 2 [--arroba @perfil]
      (cria o JSON direto de um roteiro de formato carrossel, sem IA, e renderiza)

Schema (dados/carrosseis/<id>.json):
  { "id", "tipo": "carrossel", "titulo", "cliente", "criado_em", "arroba",
    "origem": {"arquivo", "indice"},
    "estilo": {"fundo": "#141210", "texto": "#F5F1EC", "destaque": "#FF6A13", "fundo_capa": "#FF6A13", "texto_capa": "#141210"},
    "slides": [ {"n": 1, "tipo": "capa|conteudo|cta", "titulo": "...", "texto": "...", "arquivo": "midia/<id>/carrossel/01.png"} ],
    "legenda", "hashtags" }
"""
import argparse
import html
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESTILO = {"fundo": "#141210", "texto": "#F5F1EC", "destaque": "#FF6A13", "fundo_capa": "#FF6A13", "texto_capa": "#141210"}

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def navegador():
    for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if Path(c).exists():
            return c
    for nome in ["google-chrome", "chromium", "chrome", "msedge"]:
        if shutil.which(nome):
            return shutil.which(nome)
    sys.exit("Chrome ou Edge não encontrado para renderizar os slides.")


def pagina(slide, total, est, arroba):
    capa = slide.get("tipo") == "capa"
    cta = slide.get("tipo") == "cta"
    fundo = est["fundo_capa"] if capa else est["fundo"]
    cor = est["texto_capa"] if capa else est["texto"]
    titulo = html.escape(slide.get("titulo") or "").replace("\n", "<br>")
    texto = html.escape(slide.get("texto") or "").replace("\n", "<br>")
    tam = 112 if capa else (84 if len(titulo) < 60 else 68)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Inter:wght@500;600&display=block" rel="stylesheet">
<style>
*{{margin:0;box-sizing:border-box}}
html,body{{width:1080px;height:1350px;overflow:hidden}}
body{{background:{fundo};color:{cor};font-family:Inter,Arial,sans-serif;padding:96px 90px;display:flex;flex-direction:column}}
.topo{{display:flex;justify-content:space-between;font:600 28px Inter,Arial;opacity:.75}}
.meio{{margin:auto 0;display:flex;flex-direction:column;gap:40px}}
h1{{font-family:"Bricolage Grotesque",Arial Black,sans-serif;font-weight:800;font-size:{tam}px;line-height:1.02;letter-spacing:-.035em}}
h1 em{{font-style:normal;color:{est['destaque'] if not capa else est['texto_capa']}}}
p{{font-size:44px;line-height:1.32;font-weight:500;opacity:.92}}
.barra{{width:120px;height:12px;border-radius:99px;background:{est['destaque'] if not capa else est['texto_capa']}}}
.base{{display:flex;justify-content:space-between;align-items:center;font:600 28px Inter,Arial;opacity:.8}}
.seta{{font-size:44px}}
.cta{{display:inline-block;background:{est['destaque']};color:{est['fundo']};border-radius:999px;padding:26px 46px;font:700 40px Inter,Arial;align-self:flex-start}}
</style></head><body>
<div class="topo"><span>{html.escape(arroba or '')}</span><span>{slide['n']}/{total}</span></div>
<div class="meio">{'' if capa else '<div class="barra"></div>'}<h1>{titulo}</h1>{f'<p>{texto}</p>' if texto and not cta else ''}{f'<span class="cta">{texto}</span>' if cta and texto else ''}</div>
<div class="base"><span>{'Arrasta para o lado' if capa else ''}</span><span class="seta">{'→' if slide['n'] < total else ''}</span></div>
</body></html>"""


def de_roteiro(arq, indice, id_, arroba):
    d = json.loads((RAIZ / arq).read_text(encoding="utf-8"))
    r = d["roteiros"][indice]
    cenas = r.get("cenas") or []
    slides = []
    for i, c in enumerate(cenas):
        tipo = "capa" if i == 0 else ("cta" if i == len(cenas) - 1 and len(cenas) > 2 else "conteudo")
        titulo = c.get("texto_tela") or c.get("visual") or ""
        texto = c.get("fala") or ("" if c.get("texto_tela") else "")
        if tipo == "cta":
            titulo, texto = c.get("texto_tela") or "Gostou?", r.get("cta") or c.get("fala") or ""
        slides.append({"n": i + 1, "tipo": tipo, "titulo": titulo, "texto": texto, "arquivo": None})
    return {"id": id_, "tipo": "carrossel", "titulo": r.get("titulo"), "cliente": d.get("cliente"),
            "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "arroba": arroba, "origem": {"arquivo": arq, "indice": indice}, "estilo": ESTILO,
            "slides": slides, "legenda": r.get("legenda"), "hashtags": r.get("hashtags") or []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--de-roteiro")
    ap.add_argument("--indice", type=int, default=0)
    ap.add_argument("--arroba", default=None)
    args = ap.parse_args()

    destino = RAIZ / "dados" / "carrosseis" / f"{args.id}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    if args.de_roteiro:
        dados = de_roteiro(args.de_roteiro, args.indice, args.id, args.arroba)
        destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    dados = json.loads(destino.read_text(encoding="utf-8"))
    est = {**ESTILO, **(dados.get("estilo") or {})}
    slides = dados.get("slides") or []
    if not slides:
        sys.exit("Carrossel sem slides.")

    pasta = RAIZ / "midia" / args.id / "carrossel"
    pasta.mkdir(parents=True, exist_ok=True)
    chrome = navegador()
    with tempfile.TemporaryDirectory() as tmp:
        for s in slides:
            s["n"] = s.get("n") or slides.index(s) + 1
            arq_html = Path(tmp) / f"{s['n']:02d}.html"
            arq_html.write_text(pagina(s, len(slides), est, dados.get("arroba")), encoding="utf-8")
            png = pasta / f"{s['n']:02d}.png"
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            "--window-size=1080,1350", "--virtual-time-budget=3000", f"--user-data-dir={tmp}/perfil",
                            f"--screenshot={png}", arq_html.as_uri()], capture_output=True, timeout=90)
            if not png.exists():
                sys.exit(f"Falhou ao renderizar o slide {s['n']}")
            s["arquivo"] = png.relative_to(RAIZ).as_posix()
            print(f"slide {s['n']}/{len(slides)} ok", flush=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PRONTO {len(slides)} slides em {pasta}")


if __name__ == "__main__":
    main()
