"""Coleta dados reais de perfis do Instagram pela API oficial da Meta (Business Discovery).

Só funciona com contas profissionais (comercial ou criador). Perfis pessoais voltam como "nao_encontrado".
A busca por hashtag exige revisão do app na Meta (Public Content Access); por isso a entrada é uma lista de perfis.

Uso:
  python ferramentas/instagram/perfis.py <id> @perfil1 perfil2 ... [--posts 30]
Saída:
  midia/<id>/bruto/instagram.json   perfis + posts + métricas calculadas
  (resumo no terminal: ranking de perfis e top posts por engajamento)

Credenciais em .env na raiz: META_TOKEN e IG_USER_ID (conta profissional usada como observadora).
"""
import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
API = "https://graph.facebook.com/v22.0"
CAMPOS_POST = "caption,like_count,comments_count,media_type,media_product_type,timestamp,permalink,view_count"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def env():
    vals = {}
    arq = RAIZ / ".env"
    if arq.exists():
        for linha in arq.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.startswith("#"):
                k, v = linha.split("=", 1)
                vals[k.strip()] = v.strip()
    if not vals.get("META_TOKEN") or not vals.get("IG_USER_ID"):
        sys.exit("Faltam META_TOKEN e/ou IG_USER_ID no .env")
    return vals["META_TOKEN"], vals["IG_USER_ID"]


def get(caminho, params, token):
    params = {**params, "access_token": token}
    url = f"{API}/{caminho}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = json.loads(e.read() or b"{}")
        return {"error": corpo.get("error", {"message": str(e)})}


def formato(p):
    if p.get("media_product_type") == "REELS":
        return "reels"
    return {"CAROUSEL_ALBUM": "carrossel", "IMAGE": "imagem", "VIDEO": "video"}.get(p.get("media_type"), "outro")


def coletar(usuario, token, ig, limite):
    campos = (f"business_discovery.username({usuario}){{username,name,biography,website,followers_count,"
              f"media_count,profile_picture_url,media.limit({min(limite, 50)}){{{CAMPOS_POST}}}}}")
    d = get(ig, {"fields": campos}, token)
    if "error" in d:
        return {"username": usuario, "erro": d["error"].get("message")}
    bd = d["business_discovery"]
    posts = bd.get("media", {}).get("data", [])
    depois = bd.get("media", {}).get("paging", {}).get("cursors", {}).get("after")
    while depois and len(posts) < limite:
        mais = get(ig, {"fields": f"business_discovery.username({usuario}){{media.limit(50).after({depois}){{{CAMPOS_POST}}}}}"}, token)
        m = mais.get("business_discovery", {}).get("media", {})
        if not m.get("data"):
            break
        posts += m["data"]
        depois = m.get("paging", {}).get("cursors", {}).get("after")
    bd["media"] = posts[:limite]
    return bd


def metricas(perfil):
    seg = perfil.get("followers_count") or None
    posts = []
    for p in perfil.pop("media", []):
        likes = p.get("like_count")  # ausente quando o dono oculta as curtidas
        com = p.get("comments_count")
        interacoes = (likes or 0) + (com or 0) if likes is not None or com is not None else None
        views = p.get("view_count")
        posts.append({
            "url": p.get("permalink"), "data": (p.get("timestamp") or "")[:10], "formato_ig": formato(p),
            "legenda": (p.get("caption") or "")[:600], "likes": likes, "comentarios": com, "views": views,
            "engajamento_seguidores": round(interacoes / seg, 5) if interacoes is not None and seg else None,
            "engajamento_views": round(interacoes / views, 5) if interacoes is not None and views else None,
        })
    validos = [p for p in posts if p["likes"] is not None]
    inter = [p["likes"] + (p["comentarios"] or 0) for p in validos]
    mediana = statistics.median(inter) if inter else None
    for p in posts:
        if mediana and p["likes"] is not None:
            p["outlier_score"] = round((p["likes"] + (p["comentarios"] or 0)) / mediana, 2)
        else:
            p["outlier_score"] = None
    datas = sorted(p["data"] for p in posts if p["data"])
    freq = None
    if len(datas) >= 2:
        dias = (datetime.fromisoformat(datas[-1]) - datetime.fromisoformat(datas[0])).days or 1
        freq = round(len(datas) / dias * 7, 1)
    mix = {}
    for p in posts:
        mix[p["formato_ig"]] = mix.get(p["formato_ig"], 0) + 1
    perfil["metricas"] = {
        "posts_analisados": len(posts),
        "mediana_interacoes": mediana,
        "mediana_likes": statistics.median([p["likes"] for p in validos]) if validos else None,
        "mediana_comentarios": statistics.median([p["comentarios"] for p in validos if p["comentarios"] is not None]) if validos else None,
        "engajamento_mediano": round(mediana / seg, 5) if mediana is not None and seg else None,
        "posts_por_semana": freq,
        "mix_formatos": {k: round(v / len(posts), 2) for k, v in mix.items()} if posts else {},
        "views_disponiveis": any(p["views"] is not None for p in posts),
        "likes_ocultos": len(posts) - len(validos),
    }
    perfil["posts"] = posts
    return perfil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("perfis", nargs="+")
    ap.add_argument("--posts", type=int, default=30)
    args = ap.parse_args()
    token, ig = env()

    saida = []
    for u in args.perfis:
        u = u.strip().lstrip("@").split("/")[-1] if "instagram.com" not in u else u.rstrip("/").split("/")[-1]
        print(f"coletando @{u}…", flush=True)
        p = coletar(u, token, ig, args.posts)
        if "erro" in p:
            print(f"   não encontrado ou não é conta profissional: {p['erro'][:120]}")
            saida.append({"username": u, "status": "nao_encontrado", "erro": p["erro"]})
            continue
        saida.append({"status": "ok", **metricas(p)})
        time.sleep(0.3)

    pasta = RAIZ / "midia" / args.id / "bruto"
    pasta.mkdir(parents=True, exist_ok=True)
    dados = {"coletado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "fonte": "meta:business_discovery",
             "nota": "engajamento_seguidores = (likes + comentários) / seguidores. outlier_score = interações do post / mediana do perfil.",
             "perfis": saida}
    (pasta / "instagram.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    import subprocess
    subprocess.run([sys.executable, str(Path(__file__).with_name("resumo.py")), args.id])
    # baixa já os vídeos/imagens dos posts em alta (os links da API expiram em horas)
    subprocess.run([sys.executable, str(Path(__file__).with_name("videos.py")), args.id, "--top", "15"])

    ok = [p for p in saida if p["status"] == "ok"]
    print(f"\n{len(ok)}/{len(saida)} perfis coletados -> {pasta / 'instagram.json'}\n")
    print(f"{'perfil':24} {'seguidores':>11} {'eng. med.':>9} {'posts/sem':>9}  formatos")
    for p in sorted(ok, key=lambda x: x["metricas"]["engajamento_mediano"] or 0, reverse=True):
        m = p["metricas"]
        eng = f"{m['engajamento_mediano'] * 100:.2f}%" if m["engajamento_mediano"] is not None else "—"
        mix = ", ".join(f"{k} {int(v * 100)}%" for k, v in sorted(m["mix_formatos"].items(), key=lambda x: -x[1]))
        print(f"@{p['username'][:23]:23} {p['followers_count']:>11,} {eng:>9} {str(m['posts_por_semana'] or '—'):>9}  {mix}")
    todos = [dict(post, perfil=p["username"]) for p in ok for post in p["posts"] if post["outlier_score"]]
    print("\nTop posts (interações acima da mediana do próprio perfil):")
    for t in sorted(todos, key=lambda x: x["outlier_score"], reverse=True)[:10]:
        print(f"  {t['outlier_score']:>5}x  @{t['perfil']:20} {t['formato_ig']:9} {t['likes'] or 0:>8} likes {t['comentarios'] or 0:>6} com.  {t['url']}")


if __name__ == "__main__":
    main()
