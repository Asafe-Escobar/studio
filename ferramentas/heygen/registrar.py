"""Registra o que o chat do professor produz, para aparecer na área dele no Studio.

Vídeo do clone (HeyGen):
  python ferramentas/heygen/registrar.py video <perfil> <prof> --video-id ID --titulo "..." [--look ID] [--roteiro dados/x/y.json#0]
  python ferramentas/heygen/registrar.py video <perfil> <prof> --video-id ID --status pronto --url https://... [--duracao 38]
    (com --url baixa o .mp4 para midia/avatar/<prof>/<video-id>.mp4)
  Lista em dados/perfis/<perfil>/videos/<prof>.json

Entrega (roteiros/estratégia salvos em dados/<tipo>/<id>.json):
  python ferramentas/heygen/registrar.py entrega <perfil> <prof> --tipo campanhas --id <id> --titulo "..."
"""
import argparse, datetime, json, os, sys, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ler(arq, padrao):
    try:
        with open(arq, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return padrao


def gravar(arq, d):
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def agora():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def video(a):
    arq = os.path.join(RAIZ, "dados", "perfis", a.perfil, "videos", f"{a.prof}.json")
    lista = ler(arq, [])
    v = next((x for x in lista if x["video_id"] == a.video_id), None)
    if not v:
        v = {"video_id": a.video_id, "criado_em": agora(), "status": "processando", "titulo": a.titulo or "Vídeo do clone",
             "look": a.look, "roteiro": a.roteiro, "arquivo": None, "url": None, "duracao_s": None}
        lista.insert(0, v)
    for k in ("titulo", "look", "roteiro", "status", "duracao"):
        val = getattr(a, k)
        if val is not None:
            v["duracao_s" if k == "duracao" else k] = val
    if a.url:
        v["url"] = a.url
        rel = f"midia/avatar/{a.prof}/{a.video_id}.mp4"
        destino = os.path.join(RAIZ, *rel.split("/"))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        urllib.request.urlretrieve(a.url, destino)
        v["arquivo"] = rel
        v["status"] = "pronto"
    gravar(arq, lista)
    print(json.dumps(v, ensure_ascii=False))


def entrega(a):
    arq = os.path.join(RAIZ, "dados", "perfis", f"{a.perfil}.json")
    d = ler(arq, None)
    if not d:
        sys.exit(f"perfil {a.perfil} não encontrado")
    prof = next((p for p in d.get("professores", []) if p["id"] == a.prof), None)
    if not prof:
        sys.exit(f"professor {a.prof} não encontrado")
    if not os.path.exists(os.path.join(RAIZ, "dados", a.tipo, f"{a.id}.json")):
        sys.exit(f"dados/{a.tipo}/{a.id}.json não existe: salve o JSON antes de registrar")
    ents = prof.setdefault("entregas", [])
    if not any(e["id"] == a.id for e in ents):
        ents.append({"tipo": a.tipo, "id": a.id, "titulo": a.titulo})
    gravar(arq, d)
    print("ok")


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
v = sub.add_parser("video")
v.add_argument("perfil"); v.add_argument("prof")
v.add_argument("--video-id", required=True); v.add_argument("--titulo"); v.add_argument("--look"); v.add_argument("--roteiro")
v.add_argument("--status", choices=["processando", "pronto", "falhou"]); v.add_argument("--url"); v.add_argument("--duracao", type=float)
e = sub.add_parser("entrega")
e.add_argument("perfil"); e.add_argument("prof")
e.add_argument("--tipo", required=True, choices=["campanhas", "pesquisas", "cortes", "carrosseis"]); e.add_argument("--id", required=True); e.add_argument("--titulo", required=True)
a = ap.parse_args()
video(a) if a.cmd == "video" else entrega(a)
