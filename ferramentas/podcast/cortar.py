"""Renderiza os cortes definidos em dados/cortes/<id>.json.

Modos:
  blur      vertical 1080x1920, vídeo inteiro no centro sobre fundo desfocado (2+ pessoas)
  crop      vertical 1080x1920, recorte central (1 rosto centralizado)
  original  mantém o enquadramento original

Legenda: palavra a palavra (2-4 por vez), grande, centro-baixo, a partir de midia/<id>/transcricao.json.

Motor (--motor): "remotion" (padrão no 9:16) gera aqui só o vídeo base enquadrado (NN-base.mp4) e a edição final
(legenda animada, cortes de silêncio, zooms, gancho, barra) sai de ferramentas/remotion/editar.py. "ffmpeg" é a
edição simples antiga (legenda karaokê queimada) e é o reserva se o Remotion falhar.

Uso: python ferramentas/podcast/cortar.py <id> [--modo blur|crop|original] [--sem-legenda] [--so 1,3,5] [--motor remotion|ffmpeg]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from comum import RAIZ, DADOS, limpar_palavras, pasta, original, para_segundos, dimensoes

ESTILO_ASS = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Leg,Arial Black,{fs},&H00FFFFFF,&H0000E5FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,{ol},2,2,60,60,{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def tempo_ass(t: float) -> str:
    t = max(t, 0)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def gerar_ass(palavras, ini, fim, w, h, destino):
    dentro = [p for p in palavras if p["s"] >= ini - 0.05 and p["e"] <= fim + 0.3]
    grupos, atual = [], []
    for p in dentro:
        atual.append(p)
        termina_frase = p["w"][-1:] in ".?!,"
        if len(atual) >= 3 or termina_frase:
            grupos.append(atual)
            atual = []
    if atual:
        grupos.append(atual)

    vertical = h > w
    fs = int(w * (0.075 if vertical else 0.045))
    linhas = [ESTILO_ASS.format(w=w, h=h, fs=fs, ol=max(4, fs // 12), mv=int(h * (0.28 if vertical else 0.08)))]
    for i, g in enumerate(grupos):
        s = g[0]["s"] - ini
        e = (grupos[i + 1][0]["s"] - ini) if i + 1 < len(grupos) else g[-1]["e"] - ini
        e = min(e, g[-1]["e"] - ini + 0.6)
        # palavra falada no momento fica amarela (karaokê)
        partes = []
        for p in g:
            dur = int(max(p["e"] - p["s"], 0.05) * 100)
            texto = p["w"].upper().replace("{", "").replace("}", "")
            partes.append(f"{{\\kf{dur}}}{texto}")
        linhas.append(f"Dialogue: 0,{tempo_ass(s)},{tempo_ass(e)},Leg,,0,0,0,,{' '.join(partes)}")
    destino.write_text("\n".join(linhas), encoding="utf-8")


def filtro_seguindo(fonte, ini, fim, arq_cmd):
    """Recorte 9:16 que acompanha quem está falando (enquadrar.py) via sendcmd do ffmpeg. None se não achar rostos."""
    try:
        from enquadrar import trajetoria
        pontos = trajetoria(fonte, ini, fim)
    except Exception as e:
        print(f"   rastreamento indisponível ({e}); usando recorte central", flush=True)
        return None
    dim = dimensoes(fonte)
    if not pontos or not dim:
        return None
    larg = round(dim[0] * 1920 / dim[1] / 2) * 2          # largura após escalar para 1920 de altura
    maximo = max(0, larg - 1080)
    linhas, ultimo = [], None
    for t, cx in pontos:
        x = int(min(max(cx * larg - 540, 0), maximo))
        if ultimo is None or abs(x - ultimo) >= 2:
            linhas.append(f"{t:.2f} crop@c x {x};")
            ultimo = x
    arq_cmd.write_text("\n".join(linhas), encoding="utf-8")
    x0 = linhas[0].split()[-1].rstrip(";")
    print(f"   seguindo quem fala: {len(linhas)} ajustes de enquadramento", flush=True)
    return f"[0:v]scale=-2:1920,sendcmd=f={arq_cmd.name},crop@c=1080:1920:{x0}:0[v]"


def filtro_video(modo: str):
    if modo == "blur":
        return ("[0:v]split[a][b];"
                "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:2,eq=brightness=-0.08[bg];"
                "[b]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"), (1080, 1920)
    if modo == "crop":
        return "[0:v]scale=-2:1920,crop=1080:1920[v]", (1080, 1920)
    return "[0:v]null[v]", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--modo", default="crop", choices=["blur", "crop", "original"])
    ap.add_argument("--sem-legenda", action="store_true")
    ap.add_argument("--centro", action="store_true", help="no modo crop, recorte fixo no centro (sem seguir quem fala)")
    ap.add_argument("--so", default="", help="números dos cortes, ex.: 1,3")
    ap.add_argument("--motor", default="remotion", choices=["remotion", "ffmpeg"])
    args = ap.parse_args()
    if args.modo == "original":
        args.motor = "ffmpeg"          # o Remotion edita em 9:16

    arq_json = DADOS / "cortes" / f"{args.id}.json"
    if not arq_json.exists():
        sys.exit(f"{arq_json} não existe.")
    dados = json.loads(arq_json.read_text(encoding="utf-8"))
    fonte = original(args.id)
    p = pasta(args.id)
    pasta_cortes = p / "cortes"
    pasta_cortes.mkdir(exist_ok=True)

    palavras = []
    tj = p / "transcricao.json"
    if tj.exists() and not args.sem_legenda and args.motor == "ffmpeg":
        for seg in json.loads(tj.read_text(encoding="utf-8"))["segmentos"]:
            palavras.extend(limpar_palavras(seg["palavras"]))

    filtro, tamanho = filtro_video(args.modo)
    if tamanho is None:
        tamanho = dimensoes(fonte) or (1920, 1080)

    escolhidos = {int(x) for x in args.so.split(",") if x.strip()}
    def fazer(corte):
        n = int(corte["n"])
        ini, fim = para_segundos(corte["inicio"]), para_segundos(corte["fim"])
        nome = f"{n:02d}"
        saida = pasta_cortes / (f"{nome}-base.mp4" if args.motor == "remotion" else f"{nome}.mp4")
        # Edição com pedaços removidos: "trechos" = partes mantidas, renderizadas e emendadas na ordem.
        pedacos = [(para_segundos(t["inicio"]), para_segundos(t["fim"])) for t in corte.get("trechos") or []]
        pedacos = [(a, b) for a, b in pedacos if b > a] or [(ini, fim)]

        def render(a, b, nome_arq, rotulo):
            cadeia = filtro
            if args.modo == "crop" and not args.centro:
                cadeia = filtro_seguindo(fonte, a, b, pasta_cortes / f"{rotulo}.cmd") or filtro
            if palavras:
                gerar_ass(palavras, a, b, tamanho[0], tamanho[1], pasta_cortes / f"{rotulo}.ass")
                cadeia = cadeia.replace("[v]", "[v0]") + f";[v0]subtitles={rotulo}.ass[v]"
            cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.2f}", "-to", f"{b:.2f}", "-i", str(fonte),
                   "-filter_complex", cadeia, "-map", "[v]", "-map", "0:a?",
                   "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                   "-movflags", "+faststart", nome_arq]
            return subprocess.run(cmd, cwd=pasta_cortes).returncode == 0

        total_s = sum(b - a for a, b in pedacos)
        print(f"[{nome}] {corte.get('titulo', '')} ({total_s:.0f}s{f', {len(pedacos)} trechos' if len(pedacos) > 1 else ''})", flush=True)
        if len(pedacos) == 1:
            ok = render(pedacos[0][0], pedacos[0][1], saida.name, nome)
        else:
            partes = []
            ok = True
            for k, (a, b) in enumerate(pedacos, 1):
                parte = f"{nome}-p{k}.mp4"
                if not render(a, b, parte, f"{nome}-p{k}"):
                    ok = False
                    break
                partes.append(parte)
            if ok:
                lista = pasta_cortes / f"{nome}-lista.txt"
                lista.write_text("".join(f"file '{p}'\n" for p in partes), encoding="utf-8")
                ok = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista.name,
                                     "-c", "copy", "-movflags", "+faststart", saida.name], cwd=pasta_cortes).returncode == 0
                for p in partes:
                    (pasta_cortes / p).unlink(missing_ok=True)
        if not ok:
            print(f"   ERRO no corte {nome}", flush=True)
            return False
        corte["arquivo"] = saida.relative_to(RAIZ).as_posix()
        corte["duracao_s"] = round(total_s, 1)
        corte.pop("arquivo_sem_musica", None)
        return True

    # Vários cortes ao mesmo tempo: cada ffmpeg/enquadramento usa poucos núcleos, a máquina aguenta 3 juntos.
    from concurrent.futures import ThreadPoolExecutor
    fila = [c for c in dados.get("cortes", []) if not escolhidos or int(c["n"]) in escolhidos]
    with ThreadPoolExecutor(max_workers=3) as ex:
        feitos = sum(ex.map(fazer, fila))

    # Remotion: edição final em cima dos vídeos base. Se falhar, refaz no ffmpeg (legenda simples).
    if args.motor == "remotion" and feitos:
        lista = ",".join(str(int(c["n"])) for c in dados.get("cortes", []) if (not escolhidos or int(c["n"]) in escolhidos))
        extra = ["--sem-legenda"] if args.sem_legenda else []
        print("\n== editando no Remotion", flush=True)
        r = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "remotion" / "editar.py"), args.id, "--so", lista, *extra], cwd=RAIZ)
        if r.returncode != 0:
            print("aviso: o Remotion falhou; refazendo com a edição simples do ffmpeg", flush=True)
            cmd = [sys.executable, __file__, args.id, "--modo", args.modo, "--motor", "ffmpeg", "--so", lista]
            if args.sem_legenda:
                cmd.append("--sem-legenda")
            if args.centro:
                cmd.append("--centro")
            subprocess.run(cmd, cwd=RAIZ)
        return

    # Relê antes de gravar: legendas_ig.py pode ter escrito as legendas em paralelo. Só atualiza arquivo e duração.
    renderizados = {int(c["n"]): c for c in dados.get("cortes", [])}
    atual = json.loads(arq_json.read_text(encoding="utf-8"))
    for c in atual.get("cortes", []):
        r = renderizados.get(int(c["n"]))
        if r:
            c["arquivo"], c["duracao_s"] = r.get("arquivo"), r.get("duracao_s")
            if "arquivo_sem_musica" not in r:
                c.pop("arquivo_sem_musica", None)
                c.pop("musica", None)
    arq_json.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK {feitos} cortes em {pasta_cortes}")


if __name__ == "__main__":
    main()
