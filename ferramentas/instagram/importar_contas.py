"""Cria/atualiza um perfil no Studio (dados/perfis/<id>.json) para cada conta do Instagram ligada ao token.

Uso: python ferramentas/instagram/importar_contas.py
Atualiza nome, @, seguidores, bio e foto; nunca apaga professores já cadastrados.
"""
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from perfis import env  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def main():
    token, _ = env()
    q = urllib.parse.urlencode({"limit": 100, "access_token": token,
                                "fields": "name,instagram_business_account{id,username,name,followers_count,media_count,biography,profile_picture_url}"})
    d = json.load(urllib.request.urlopen(f"https://graph.facebook.com/v22.0/me/accounts?{q}", timeout=40))
    pasta = RAIZ / "dados" / "perfis"
    pasta.mkdir(parents=True, exist_ok=True)
    for pag in d.get("data", []):
        ig = pag.get("instagram_business_account")
        if not ig:
            continue
        pid = slug(ig["username"])
        arq = pasta / f"{pid}.json"
        atual = json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {
            "id": pid, "tipo": "perfil", "criado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"), "professores": [], "publico": ""}
        atual.update(nome=ig.get("name") or pag["name"], instagram="@" + ig["username"], ig_id=ig["id"], pagina=pag["name"],
                     seguidores=ig.get("followers_count"), posts=ig.get("media_count"), descricao=ig.get("biography") or "",
                     foto=ig.get("profile_picture_url"))
        arq.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{pid:22} {atual['instagram']:22} {atual['seguidores'] or 0:>7} seguidores  {len(atual['professores'])} professores")


if __name__ == "__main__":
    main()
