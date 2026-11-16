"""Baixa os vídeos (Reels) e imagens dos posts em alta de uma pesquisa, para o Studio mostrar e tocar.

Uso: python ferramentas/instagram/videos.py <id_pesquisa> [--top 15]
Lê os posts de dados/pesquisas/<id>.json (posts_referencia) ou midia/<id>/bruto/resumo.json (top_posts).
Os links de mídia da API expiram em horas, então ele pede links novos pela API oficial (Business Discovery)
e salva em midia/<id>/refs/<shortcode>.mp4 (Reels/vídeo) ou .jpg (imagem/carrossel, capa).
O Studio liga cada post ao arquivo pelo shortcode da URL.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from perfis import env, get  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def codigo(url):
    m = re.search(r"/(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def baixar(url, destino):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
            while True:
                bloco = r.read(1 << 16)
                if not bloco:
                    break
                f.write(bloco)
        return True
    except Exception as e:
        print(f"   falhou {destino.name}: {e}")
        if destino.exists():
            destino.unlink()
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()
    token, ig = env()

    posts = []
    pesq = RAIZ / "dados" / "pesquisas" / f"{args.id}.json"
    if pesq.exists():
        posts = json.loads(pesq.read_text(encoding="utf-8")).get("posts_referencia") or []
    if not posts:
        res = RAIZ / "midia" / args.id / "bruto" / "resumo.json"
        if res.exists():
            posts = json.loads(res.read_text(encoding="utf-8")).get("top_posts") or []
    posts = sorted(posts, key=lambda p: -(p.get("outlier_score") or 0))[: args.top]
    if not posts:
        sys.exit("Pesquisa sem posts de referência.")

    pasta = RAIZ / "midia" / args.id / "refs"
    pasta.mkdir(parents=True, exist_ok=True)
    por_perfil = {}
    for p in posts:
        c = codigo(p.get("url"))
        if c and not list(pasta.glob(f"{c}.*")):
            por_perfil.setdefault((p.get("perfil") or "").lstrip("@"), set()).add(c)

    feitos = 0
    for usuario, codigos in por_perfil.items():
        if not usuario:
            continue
        d = get(ig, {"fields": f"business_discovery.username({usuario}){{media.limit(50){{permalink,media_type,media_url,thumbnail_url}}}}"}, token)
        midias = d.get("business_discovery", {}).get("media", {}).get("data", []) if "error" not in d else []
        for m in midias:
            c = codigo(m.get("permalink"))
            if c not in codigos:
                continue
            if m.get("media_type") == "VIDEO" and m.get("media_url"):
                ok = baixar(m["media_url"], pasta / f"{c}.mp4")
                if m.get("thumbnail_url"):
                    baixar(m["thumbnail_url"], pasta / f"{c}.jpg")
            else:
                ok = bool(m.get("media_url")) and baixar(m["media_url"], pasta / f"{c}.jpg")
            feitos += bool(ok)
            print(f"@{usuario} {c} {'vídeo' if m.get('media_type') == 'VIDEO' else 'imagem'} {'ok' if ok else 'sem mídia'}", flush=True)
    print(f"OK {feitos} mídias em {pasta}")


if __name__ == "__main__":
    main()
