"""Resume midia/<id>/bruto/instagram.json num arquivo pequeno para o agente ler rápido.

Uso: python ferramentas/instagram/resumo.py <id> [--top 25]
Gera midia/<id>/bruto/resumo.json com: ranking de perfis (métricas) e os top posts por outlier_score
(legenda cortada), além do mix de formatos geral. O bruto continua lá para consulta pontual.
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--nicho", default=None)
    args = ap.parse_args()
    pasta = RAIZ / "midia" / args.id / "bruto"
    d = json.loads((pasta / "instagram.json").read_text(encoding="utf-8"))
    ok = [p for p in d.get("perfis", []) if p.get("status", "ok") == "ok" and p.get("posts")]

    perfis = []
    for p in ok:
        m = p.get("metricas", {})
        perfis.append({"username": p.get("username"), "nome": p.get("name"), "seguidores": p.get("followers_count"),
                       "bio": (p.get("biography") or "")[:160], **{k: m.get(k) for k in
                       ["engajamento_mediano", "mediana_interacoes", "posts_por_semana", "mix_formatos", "posts_analisados"]}})
    perfis.sort(key=lambda x: x.get("engajamento_mediano") or 0, reverse=True)

    posts = []
    for p in ok:
        for post in p["posts"]:
            if post.get("outlier_score") is None:
                continue
            posts.append({"perfil": "@" + p["username"], "seguidores": p.get("followers_count"), "url": post.get("url"),
                          "data": post.get("data"), "formato_ig": post.get("formato_ig"), "likes": post.get("likes"),
                          "comentarios": post.get("comentarios"), "views": post.get("views"),
                          "outlier_score": post.get("outlier_score"), "engajamento_seguidores": post.get("engajamento_seguidores"),
                          "legenda": (post.get("legenda") or "")[:280]})
    posts.sort(key=lambda x: x["outlier_score"], reverse=True)
    top = posts[: args.top]

    todos = [post for p in ok for post in p["posts"]]
    mix_geral, mix_top = {}, {}
    for x in todos:
        mix_geral[x["formato_ig"]] = mix_geral.get(x["formato_ig"], 0) + 1
    for x in top:
        mix_top[x["formato_ig"]] = mix_top.get(x["formato_ig"], 0) + 1
    views_reels = [x["views"] for x in todos if x.get("views") and x["formato_ig"] == "reels"]

    resumo = {
        "fonte": d.get("fonte", "meta:business_discovery"), "coletado_em": d.get("coletado_em"),
        "perfis_coletados": len(ok), "posts_analisados": len(todos),
        "nota": "outlier_score = interações do post / mediana do próprio perfil (>=3 é outlier). engajamento = (likes+comentários)/seguidores.",
        "mix_formatos_geral": {k: round(v / len(todos), 3) for k, v in mix_geral.items()} if todos else {},
        "mix_formatos_top": {k: round(v / len(top), 3) for k, v in mix_top.items()} if top else {},
        "mediana_views_reels": statistics.median(views_reels) if views_reels else None,
        "perfis": perfis, "top_posts": top,
    }
    destino = pasta / "resumo.json"
    destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"resumo: {len(ok)} perfis, {len(todos)} posts, top {len(top)} -> {destino} ({destino.stat().st_size // 1024} KB)")

    # Pesquisa preliminar: o Studio mostra os dados reais na hora, antes da análise e dos roteiros da IA.
    pesq = RAIZ / "dados" / "pesquisas" / f"{args.id}.json"
    if not pesq.exists():
        from datetime import datetime, timezone
        nicho = args.nicho or args.id[11:].replace("-", " ")
        mix = ", ".join(f"{k} {round(v * 100)}%" for k, v in sorted(resumo["mix_formatos_top"].items(), key=lambda x: -x[1]))
        melhor = perfis[0] if perfis else {}
        prelim = {
            "id": args.id, "tipo": "pesquisa", "nicho": nicho, "status": "coletado",
            "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "fontes": [resumo["fonte"]], "metrica_views": "view_count (Reels)",
            "resumo": (f"Dados reais de {len(ok)} perfis e {len(todos)} posts do Instagram. Entre os {len(top)} posts que mais passaram da "
                       f"média do próprio perfil, o mix é: {mix or 'sem dados'}. Maior engajamento: @{melhor.get('username')} "
                       f"({round((melhor.get('engajamento_mediano') or 0) * 100, 2)}% por post). Análise de formatos e roteiros em andamento."),
            "perfis": perfis,
            "formatos": [], "padroes": [],
            "posts_referencia": [{"url": p["url"], "perfil": p["perfil"], "rede": "instagram", "formato": None, "formato_ig": p["formato_ig"],
                                  "gancho": (p["legenda"].split("\n")[0][:140] or None), "views": p["views"], "likes": p["likes"],
                                  "comentarios": p["comentarios"], "seguidores": p["seguidores"], "outlier_score": p["outlier_score"],
                                  "data": p["data"], "resumo": None} for p in top[:20]],
            "roteiros": [],
        }
        pesq.parent.mkdir(parents=True, exist_ok=True)
        pesq.write_text(json.dumps(prelim, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"pesquisa preliminar -> {pesq}")


if __name__ == "__main__":
    main()
