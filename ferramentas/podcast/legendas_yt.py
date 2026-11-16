"""Usa a legenda automática do YouTube (com tempo por palavra) no lugar da transcrição do Whisper.

Leva segundos em vez de minutos. Gera os mesmos arquivos que transcrever.py:
  midia/<id>/transcricao.json  segmentos + palavras com tempo (usado na legenda queimada)
  midia/<id>/transcricao.txt   [HH:MM:SS.s] texto (para a IA escolher os cortes)

Uso: python ferramentas/podcast/legendas_yt.py <url> <id>
Sai com código 2 se o vídeo não tiver legenda em português (aí use transcrever.py).
"""
import argparse
import json
import re
import sys
from pathlib import Path

from comum import limpar_palavras, pasta, para_segundos, ts

TAG = re.compile(r"<(\d\d:\d\d:\d\d\.\d{3})>")


def baixar_vtt(url, destino):
    import yt_dlp
    for langs in (["pt"], ["pt-BR"], ["pt-orig"], ["pt.*"]):
        opcoes = {"skip_download": True, "writeautomaticsub": True, "writesubtitles": True, "subtitleslangs": langs,
                  "subtitlesformat": "vtt", "outtmpl": str(destino / "legenda"), "quiet": True, "no_warnings": True,
                  "ignoreerrors": True}
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([url])
        achados = sorted(destino.glob("legenda*.vtt"))
        if achados:
            return achados[0]
    return None


def palavras_do_vtt(texto):
    """Lê só as linhas com marcação por palavra (<00:00:04.000><c> palavra</c>)."""
    palavras = []
    blocos = texto.split("\n\n")
    for bloco in blocos:
        linhas = bloco.strip().splitlines()
        if not linhas or "-->" not in linhas[0]:
            continue
        ini_cue, fim_cue = [para_segundos(x.split()[0]) for x in linhas[0].split("-->")]
        for linha in linhas[1:]:
            if "<c>" not in linha:
                continue
            # primeira palavra começa no início do cue; as seguintes trazem o próprio tempo antes
            partes = TAG.split(linha)
            t = ini_cue
            primeira = re.sub(r"</?c>", "", partes[0]).strip()
            if primeira:
                palavras.append([primeira, t])
            for k in range(1, len(partes), 2):
                t = para_segundos(partes[k])
                w = re.sub(r"</?c>", "", partes[k + 1]).strip()
                if w:
                    palavras.append([w, t])
            palavras.append([None, fim_cue])  # marca o fim do cue
    saida = []
    for i, (w, s) in enumerate(palavras):
        if w is None:
            continue
        prox = next((p[1] for p in palavras[i + 1:]), s + 0.4)
        saida.append({"w": w, "s": round(s, 2), "e": round(max(prox, s + 0.08), 2)})
    return limpar_palavras(saida)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("id")
    args = ap.parse_args()
    p = pasta(args.id)
    for velho in p.glob("legenda*.vtt"):
        velho.unlink()
    vtt = baixar_vtt(args.url, p)
    if not vtt:
        print("Sem legenda automática em português.")
        sys.exit(2)
    palavras = palavras_do_vtt(vtt.read_text(encoding="utf-8"))
    if len(palavras) < 20:
        print("Legenda sem marcação por palavra.")
        sys.exit(2)

    # segmentos de ~frase: quebra em pontuação final ou a cada ~12s
    segs, atual = [], []
    for w in palavras:
        atual.append(w)
        if w["w"][-1:] in ".?!" or (w["e"] - atual[0]["s"]) > 12:
            segs.append(atual)
            atual = []
    if atual:
        segs.append(atual)
    segmentos = [{"s": g[0]["s"], "e": g[-1]["e"], "texto": " ".join(x["w"] for x in g), "palavras": g} for g in segs]
    (p / "transcricao.json").write_text(json.dumps({"duracao_s": segmentos[-1]["e"], "fonte": "youtube-auto", "segmentos": segmentos},
                                                   ensure_ascii=False), encoding="utf-8")
    (p / "transcricao.txt").write_text("\n".join(f"[{ts(s['s'])}] {s['texto']}" for s in segmentos), encoding="utf-8")
    print(f"OK legenda do YouTube: {len(palavras)} palavras, {len(segmentos)} segmentos -> {p / 'transcricao.txt'}")


if __name__ == "__main__":
    main()
