"""Busca B-roll em bancos de imagem/vídeo livres e baixa para midia/<id>/broll/.

Ordem: Pexels (vídeo vertical, depois foto; precisa de PEXELS_API_KEY no .env, chave grátis em pexels.com/api)
-> Wikimedia Commons (foto livre, sem chave). Devolve (caminho_local, tipo, credito) ou None.
A busca deve ir em inglês (os bancos respondem melhor).

Teste: python ferramentas/remotion/banco.py "surgeon operating room" [--saida pasta]
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
UA = "Zero1Studio/1.0 (b-roll fetcher)"


def _env(nome):
    if os.environ.get(nome):
        return os.environ[nome]
    arq = RAIZ / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if linha.startswith(nome + "="):
                return linha.split("=", 1)[1].strip().strip('"')
    return None


def _get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _baixar(url, destino, headers=None):
    destino.parent.mkdir(parents=True, exist_ok=True)
    dados = _get(url, headers, timeout=60)
    destino.write_bytes(dados)
    return destino


def pexels(busca, destino_base, usados):
    chave = _env("PEXELS_API_KEY")
    if not chave:
        return None
    h = {"Authorization": chave}
    q = urllib.parse.quote(busca)
    try:
        r = json.loads(_get(f"https://api.pexels.com/videos/search?query={q}&orientation=portrait&per_page=8&size=medium", h))
        for v in r.get("videos", []):
            if v["id"] in usados or not (4 <= v.get("duration", 0) <= 60):
                continue
            arquivos = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("height") and f["height"] >= f.get("width", 0)]
            arquivos.sort(key=lambda f: abs((f.get("height") or 0) - 1920))
            if arquivos:
                usados.add(v["id"])
                arq = _baixar(arquivos[0]["link"], destino_base.with_suffix(".mp4"))
                return arq, "video", f"Pexels: {v.get('user', {}).get('name', '')}"
        r = json.loads(_get(f"https://api.pexels.com/v1/search?query={q}&orientation=portrait&per_page=8", h))
        for f in r.get("photos", []):
            if f["id"] in usados:
                continue
            usados.add(f["id"])
            arq = _baixar(f["src"].get("portrait") or f["src"]["large2x"], destino_base.with_suffix(".jpg"))
            return arq, "imagem", f"Pexels: {f.get('photographer', '')}"
    except Exception as e:
        print(f"   pexels falhou ({busca}): {e}", flush=True)
    return None


def wikimedia(busca, destino_base, usados):
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 12,
              "gsrsearch": f"filetype:bitmap {busca}", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
              "iiurlwidth": 1080}
    try:
        r = json.loads(_get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)))
        paginas = sorted((r.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
        for p in paginas:
            info = (p.get("imageinfo") or [{}])[0]
            if p["pageid"] in usados or info.get("mime") not in ("image/jpeg", "image/png"):
                continue
            if (info.get("width") or 0) < 800:
                continue
            usados.add(p["pageid"])
            url = info.get("thumburl") or info["url"]
            arq = _baixar(url, destino_base.with_suffix(".jpg" if info["mime"] == "image/jpeg" else ".png"))
            autor = ((info.get("extmetadata") or {}).get("Artist") or {}).get("value", "")
            return arq, "imagem", f"Wikimedia Commons: {p.get('title', '')} {autor[:60]}"
    except Exception as e:
        print(f"   wikimedia falhou ({busca}): {e}", flush=True)
    return None


def buscar(busca, destino_base, usados=None):
    usados = usados if usados is not None else set()
    return pexels(busca, destino_base, usados) or wikimedia(busca, destino_base, usados)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    saida = Path(sys.argv[sys.argv.index("--saida") + 1]) if "--saida" in sys.argv else RAIZ / "midia" / "_broll_teste"
    print(buscar(sys.argv[1], saida / "teste"))
