"""Edição final dos cortes no Remotion: legenda animada, cortes de silêncio, zooms, gancho no topo e barra de progresso.

Entrada: o vídeo base 9:16 sem legenda (midia/<id>/cortes/NN-base.mp4, gerado por cortar.py) + transcrição com
tempo por palavra + o bloco `edicao` do corte (gancho_tela, destaques, enfases, cor), quando existir.
Saída: midia/<id>/cortes/NN.mp4 (o `arquivo` do corte passa a ser esse).

O projeto Remotion roda fora do OneDrive (C:/Users/<você>/.zero1/remotion); o código-fonte fica em
ferramentas/remotion/src e é copiado para lá antes de cada render.

Uso: python ferramentas/remotion/editar.py <id> [--so 1,3] [--sem-legenda] [--sem-gancho] [--sem-barra]
     [--manter-pausas] [--cor "#FFD400"]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "podcast"))
from comum import RAIZ, DADOS, limpar_palavras, pasta, para_segundos  # noqa: E402
sys.path.insert(0, str(AQUI))
import banco  # noqa: E402

RUNTIME = Path(os.environ.get("ZERO1_REMOTION", Path.home() / ".zero1" / "remotion"))
FPS = 30
PAUSA_MAX = 0.45      # pausa maior que isso vira corte seco
FOLGA = 0.12          # respiro mantido antes/depois da fala em cada corte
ZOOM_ALT = 1.09       # zoom alternado a cada corte seco (esconde o pulo)
STOP = set("a o e de da do das dos que em no na nos nas um uma para pra por com se não mas é eu você ele ela isso esse essa "
           "isto aqui lá então tá aí ao à as os já mais muito bem vai vou foi ser ter tem".split())


def preparar_runtime():
    """Copia o código para o projeto Remotion local e instala dependências na primeira vez."""
    if not (RUNTIME / "node_modules" / "@remotion" / "media").exists():
        RUNTIME.mkdir(parents=True, exist_ok=True)
        for f in ("package.json", "remotion.config.ts", "tsconfig.json"):
            shutil.copy2(AQUI / f, RUNTIME / f)
        print("== instalando o Remotion (primeira vez)…", flush=True)
        if subprocess.run("npm install --no-audit --no-fund", cwd=RUNTIME, shell=True).returncode != 0:
            sys.exit("Falhou a instalação do Remotion.")
    destino = RUNTIME / "src"
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(AQUI / "src", destino)
    shutil.copy2(AQUI / "remotion.config.ts", RUNTIME / "remotion.config.ts")


def palavras_base(transcricao, trechos):
    """Palavras do vídeo base (trechos emendados), com tempo relativo ao base."""
    todas = limpar_palavras([p for s in transcricao["segmentos"] for p in s.get("palavras", [])])
    saida, offset = [], 0.0
    for a, b in trechos:
        for p in todas:
            if p["s"] >= a - 0.05 and p["e"] <= b + 0.3:
                saida.append({"s": round(p["s"] - a + offset, 3), "e": round(min(p["e"], b) - a + offset, 3), "w": p["w"].strip()})
        offset += b - a
    return saida, offset


def segmentar(palavras, dur_base, manter_pausas):
    """Cortes secos nas pausas. Devolve segmentos [de, ate] do base e uma função base->final."""
    if manter_pausas or not palavras:
        return [[0.0, dur_base]]
    segs = []
    de = max(0.0, palavras[0]["s"] - FOLGA)
    for p, q in zip(palavras, palavras[1:]):
        if q["s"] - p["e"] > PAUSA_MAX:
            segs.append([de, p["e"] + FOLGA])
            de = q["s"] - FOLGA
    segs.append([de, min(dur_base, palavras[-1]["e"] + 0.35)])
    # junta segmentos minúsculos ao anterior (evita piscadas)
    final = []
    for s in segs:
        if final and s[1] - s[0] < 0.6:
            final[-1][1] = s[1]
        else:
            final.append(s)
    return final


def mapear(t, segs):
    """Tempo do base -> tempo final (depois de remover as pausas). None se caiu numa pausa removida."""
    acc = 0.0
    for de, ate in segs:
        if de <= t <= ate:
            return acc + (t - de)
        acc += ate - de
    return None


def normal(w):
    return re.sub(r"[^\wà-úÀ-Ú%]", "", w.lower())


def tempo_final(valor, trechos, segs):
    """Tempo do vídeo original (string ou número) -> tempo na linha do tempo final."""
    m = re.search(r"\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?", str(valor))
    try:
        ts = para_segundos(m.group(0)) if m else float(valor)
    except Exception:
        return None
    acc = 0.0
    for a, b in trechos:
        if a <= ts <= b:
            return mapear(acc + ts - a, segs)
        acc += b - a
    return None


def montar_broll(itens, trechos, segs, duracao, pub, pasta_broll):
    """B-roll do plano: gráficos animados (código) e imagens/vídeos de banco livre. Devolve lista para o Remotion."""
    saida, usados, creditos = [], set(), []
    for k, b in enumerate(itens or []):
        t = tempo_final(b.get("t") or b.get("inicio"), trechos, segs)
        if t is None or t < 2.8 or t > duracao - 1.0:     # não cobre o gancho nem o fim
            continue
        dur = max(1.2, min(float(b.get("dur") or 2.2), 3.5, duracao - t - 0.3))
        item = {"t": round(t, 3), "dur": round(dur, 2), "tipo": "grafico", "variante": b.get("variante") or "frase",
                "rotulo": b.get("rotulo"), "titulo": b.get("titulo"), "icone": b.get("icone")}
        if b.get("busca") and (b.get("tipo") or "estoque") != "grafico":
            achado = banco.buscar(b["busca"], pasta_broll / f"b{k + 1:02d}", usados)
            if achado:
                arq, tipo, credito = achado
                nome = f"broll-{k + 1:02d}{arq.suffix}"
                alvo = pub / nome
                alvo.unlink(missing_ok=True)
                try:
                    os.link(arq, alvo)
                except OSError:
                    shutil.copy2(arq, alvo)
                item = {"t": item["t"], "dur": item["dur"], "tipo": tipo, "src": nome}
                creditos.append(credito)
            elif not b.get("titulo"):
                continue
        elif not b.get("titulo"):
            continue
        if saida and item["t"] < saida[-1]["t"] + saida[-1]["dur"] + 1.5:   # respiro entre cenas
            continue
        saida.append(item)
    return saida, creditos


SFX = AQUI / "sfx"
# Som por evento (volume 0..1). Discretos: marca de saúde, nada de som de meme.
SOM_EVENTO = {
    "gancho": ("transicao.wav", 0.9),
    "broll": ("transicao.wav", 0.8),
    "erro": ("n-vine-boom.wav", 0.75),
    "alerta": ("impacto.wav", 0.7),
    "numero": ("impacto.wav", 0.7),
    "dica": ("n-ding.wav", 0.6),
    "frase": ("n-switch.wav", 0.6),
    "enfase": ("n-whip.wav", 0.55),
}


def montar_sfx(plano, pub, sons_ia=None):
    """Efeitos sonoros nos eventos da edição. sons_ia (opcional): [{t (final), som, volume}] vindos do plano."""
    eventos = []
    if plano.get("gancho"):
        eventos.append((0.05, "gancho"))
    for b in plano.get("broll") or []:
        eventos.append((b["t"], "broll"))
        if b.get("tipo") == "grafico" and b.get("variante") in SOM_EVENTO:
            eventos.append((b["t"] + 0.12, b["variante"]))
    cobertos = [(b["t"], b["t"] + b["dur"]) for b in plano.get("broll") or []]
    for e in plano.get("enfases") or []:
        if not any(a - 0.5 <= e["t"] <= z + 0.5 for a, z in cobertos):
            eventos.append((e["t"], "enfase"))
    saida, usados = [], set()
    for t, ev in sorted(eventos):
        som, vol = SOM_EVENTO[ev]
        if not (SFX / som).exists():
            continue
        if som not in usados:
            alvo = pub / som
            if not alvo.exists():
                shutil.copy2(SFX / som, alvo)
            usados.add(som)
        saida.append({"t": round(max(0.0, t), 3), "som": som, "volume": vol})
    return saida


def plano_corte(corte, transcricao, args):
    trechos = [(para_segundos(t["inicio"]), para_segundos(t["fim"])) for t in (corte.get("trechos") or [])]
    if not trechos:
        trechos = [(para_segundos(corte["inicio"]), para_segundos(corte["fim"]))]
    palavras, dur_base = palavras_base(transcricao, trechos)
    segs = segmentar(palavras, dur_base, args.manter_pausas)
    duracao = sum(b - a for a, b in segs)
    ed = corte.get("edicao") or {}

    # Destaques: os que a IA marcou + números. Se não houver nada, as 1-2 palavras mais longas e fortes de cada frase.
    destaques = {normal(x) for d in ed.get("destaques") or [] for x in str(d).split()}
    finais = []
    for p in palavras:
        t, f = mapear(p["s"], segs), mapear(p["e"], segs)
        if t is None:
            continue
        n = normal(p["w"])
        dest = bool(n) and (n in destaques or bool(re.search(r"\d", n)))
        finais.append({"t": round(t, 3), "f": round(f if f is not None else t + 0.25, 3), "w": p["w"], "destaque": dest})
    if not any(p["destaque"] for p in finais):
        frase = []
        for p in finais + [None]:
            if p is not None:
                frase.append(p)
            if p is None or re.search(r"[.?!]$", p["w"]):
                cand = [x for x in frase if normal(x["w"]) not in STOP and len(normal(x["w"])) >= 6]
                for x in sorted(cand, key=lambda x: -len(x["w"]))[:1]:
                    x["destaque"] = True
                frase = []

    # Zoom de ênfase: tempos da IA (no vídeo original) ou as palavras em destaque, no máximo 1 a cada 4 s.
    enf_t = []
    for e in ed.get("enfases") or []:
        bruto = str(e if not isinstance(e, dict) else e.get("t") or e.get("inicio") or "")
        m = re.search(r"\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?", bruto)
        try:
            ts = para_segundos(m.group(0)) if m else float(bruto)
        except Exception:
            continue
        acc = 0.0
        for a, b in trechos:
            if a <= ts <= b:
                m = mapear(acc + ts - a, segs)
                if m is not None:
                    enf_t.append(m)
            acc += b - a
    if not enf_t:
        enf_t = [p["t"] for p in finais if p["destaque"]]
    enfases, ultimo = [], -10.0
    for t in sorted(enf_t):
        if t - ultimo >= 4.0 and t > 1.0:
            enfases.append({"t": round(t, 3), "dur": 0.9})
            ultimo = t

    gancho_txt = ed.get("gancho_tela") or corte.get("titulo_capa") or corte.get("titulo") or ""
    gancho_txt = " ".join(str(gancho_txt).split()[:9])
    segmentos = [{"de": round(a, 3), "ate": round(b, 3), "zoom": 1.0 if i % 2 == 0 else ZOOM_ALT} for i, (a, b) in enumerate(segs)]
    return {
        "video": "base.mp4", "fps": FPS, "largura": 1080, "altura": 1920, "duracao": round(duracao, 3),
        "segmentos": segmentos, "palavras": finais if not args.sem_legenda else [], "enfases": enfases,
        "gancho": {"texto": gancho_txt, "ate": 3.2} if gancho_txt and not args.sem_gancho else None,
        "legenda": not args.sem_legenda, "barra": not args.sem_barra,
        "cor": ed.get("cor") or args.cor, "posLegenda": 0.70,
        "broll": [], "estilo": ed.get("estilo") or args.estilo,
        "_trechos": trechos, "_segs": segs, "_broll": ed.get("broll") or [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--so", default="")
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--sem-gancho", action="store_true")
    ap.add_argument("--sem-barra", action="store_true")
    ap.add_argument("--manter-pausas", action="store_true")
    ap.add_argument("--cor", default="#FFD400")
    ap.add_argument("--estilo", default="padrao", choices=["padrao", "safe"])
    ap.add_argument("--sem-broll", action="store_true")
    ap.add_argument("--sem-sfx", action="store_true", help="sem efeitos sonoros")
    args = ap.parse_args()

    arq_json = DADOS / "cortes" / f"{args.id}.json"
    dados = json.loads(arq_json.read_text(encoding="utf-8"))
    p = pasta(args.id)
    tj = p / "transcricao.json"
    transcricao = json.loads(tj.read_text(encoding="utf-8")) if tj.exists() else {"segmentos": []}
    escolhidos = {int(x) for x in args.so.split(",") if x.strip()}
    preparar_runtime()

    def gravar(n, info):
        # Grava cada corte assim que fica pronto: se o processo cair no meio, o que já saiu aparece no Studio.
        atual = json.loads(arq_json.read_text(encoding="utf-8"))
        for c in atual.get("cortes", []):
            if int(c["n"]) == n:
                c.update(info)
                c.pop("arquivo_sem_musica", None)
                c.pop("musica", None)
        arq_json.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")

    feitos = {}
    for c in dados.get("cortes", []):
        n = int(c["n"])
        if escolhidos and n not in escolhidos:
            continue
        nome = f"{n:02d}"
        base = p / "cortes" / f"{nome}-base.mp4"
        if not base.exists():
            print(f"[{nome}] sem vídeo base, pulei", flush=True)
            continue
        pronto = p / "cortes" / f"{nome}.mp4"
        if not escolhidos and c.get("motor") == "remotion" and pronto.exists()                 and pronto.stat().st_mtime > base.stat().st_mtime:
            print(f"[{nome}] já editado, pulei", flush=True)
            feitos[n] = None
            continue
        plano = plano_corte(c, transcricao, args)
        pub = p / "remotion" / nome
        pub.mkdir(parents=True, exist_ok=True)
        alvo = pub / "base.mp4"
        alvo.unlink(missing_ok=True)
        try:
            os.link(base, alvo)        # hard link: não duplica o arquivo
        except OSError:
            shutil.copy2(base, alvo)
        trechos, segs, itens = plano.pop("_trechos"), plano.pop("_segs"), plano.pop("_broll")
        creditos = []
        if itens and not args.sem_broll:
            print(f"[{nome}] buscando b-roll ({len(itens)} cenas)…", flush=True)
            plano["broll"], creditos = montar_broll(itens, trechos, segs, plano["duracao"], pub, p / "broll" / nome)
        sem_sfx = args.sem_sfx or (c.get("edicao") or {}).get("sfx") is False
        plano["sfx"] = [] if sem_sfx else montar_sfx(plano, pub)
        props = pub / "plano.json"
        props.write_text(json.dumps(plano, ensure_ascii=False), encoding="utf-8")
        saida = p / "cortes" / f"{nome}.mp4"
        print(f"[{nome}] remotion: {plano['duracao']:.0f}s, {len(plano['segmentos'])} cortes secos, "
              f"{len(plano['enfases'])} zooms, {sum(x['destaque'] for x in plano['palavras'])} destaques, "
              f"{len(plano['broll'])} b-roll, {len(plano['sfx'])} efeitos sonoros, estilo {plano['estilo']}", flush=True)
        cmd = (f'npx remotion render src/index.ts Edicao "{saida}" --props="{props}" --public-dir="{pub}" '
               f'--codec=h264 --crf=20 --concurrency={max(2, min(4, (os.cpu_count() or 4) // 4))} --log=error --overwrite')
        r = subprocess.run(cmd, cwd=RUNTIME, shell=True)
        if r.returncode != 0 or not saida.exists():
            print(f"   ERRO no Remotion (corte {nome})", flush=True)
            continue
        shutil.rmtree(pub, ignore_errors=True)
        feitos[n] = {"arquivo": saida.relative_to(RAIZ).as_posix(), "duracao_s": round(plano["duracao"], 1),
                     "motor": "remotion", "creditos_broll": creditos}
        gravar(n, feitos[n])

    print(f"OK {len(feitos)} vídeo(s) editados no Remotion", flush=True)
    if escolhidos and len(feitos) < len(escolhidos):
        sys.exit(1)


if __name__ == "__main__":
    main()
