"""Coloca música de fundo nos cortes já renderizados, sem refazer o vídeo (só o áudio é recodificado).

A música entra baixa, abaixa sozinha quando alguém fala (ducking), faz fade no início e no fim e repete se for curta.
O vídeo com música vira o `arquivo` do corte; o original fica em `arquivo_sem_musica`.

Biblioteca: midia/musicas/ (mp3, m4a, wav). Use só música livre de direitos ou sua.
Uso: python ferramentas/podcast/musica.py <id> --musica <arquivo ou nome em midia/musicas> [--volume 0.15] [--so 1,3] [--remover]
"""
import argparse
import json
import subprocess
import sys

from comum import RAIZ, DADOS, MIDIA

BIBLIOTECA = MIDIA / "musicas"


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def achar_musica(nome):
    from pathlib import Path
    for c in (Path(nome), RAIZ / nome, BIBLIOTECA / nome):
        if c.is_file():
            return c.resolve()
    sys.exit(f"Música não encontrada: {nome} (coloque em {BIBLIOTECA})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--musica", default="")
    ap.add_argument("--volume", type=float, default=0.15, help="volume da música com a voz parada (0.05 a 0.5)")
    ap.add_argument("--so", default="", help="números dos cortes, ex.: 1,3")
    ap.add_argument("--remover", action="store_true", help="volta para o vídeo sem música")
    args = ap.parse_args()

    arq_json = DADOS / "cortes" / f"{args.id}.json"
    if not arq_json.exists():
        sys.exit(f"{arq_json} não existe.")
    dados = json.loads(arq_json.read_text(encoding="utf-8"))
    escolhidos = {int(x) for x in args.so.split(",") if x.strip()}
    musica = None if args.remover else achar_musica(args.musica)
    vol = min(max(args.volume, 0.02), 1.0)

    feitos = 0
    for c in dados.get("cortes", []):
        if escolhidos and int(c["n"]) not in escolhidos:
            continue
        base_rel = c.get("arquivo_sem_musica") or c.get("arquivo")
        if not base_rel:
            print(f"[{int(c['n']):02d}] ainda não renderizado, pulei", flush=True)
            continue
        base = RAIZ / base_rel
        if args.remover:
            c["arquivo"] = base_rel
            c.pop("arquivo_sem_musica", None)
            c.pop("musica", None)
            feitos += 1
            continue
        dur = duracao(base) or c.get("duracao_s") or 60
        saida = base.with_name(f"{base.stem}-musica.mp4")
        fade_fim = max(dur - 1.5, 0)
        # [0:a] voz, [1:a] música em loop. A voz comprime a música (ducking) e as duas são somadas.
        filtro = (f"[1:a]volume={vol},afade=t=in:d=1,afade=t=out:st={fade_fim:.2f}:d=1.5,atrim=0:{dur:.2f}[m];"
                  "[0:a]asplit=2[voz][chave];"
                  "[m][chave]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mduck];"
                  "[voz][mduck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(base), "-stream_loop", "-1", "-i", str(musica),
               "-filter_complex", filtro, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "160k", "-t", f"{dur:.2f}", "-movflags", "+faststart", str(saida)]
        print(f"[{int(c['n']):02d}] música: {musica.name} (volume {vol})", flush=True)
        if subprocess.run(cmd).returncode != 0:
            print(f"   ERRO no corte {c['n']}", flush=True)
            continue
        c["arquivo_sem_musica"] = base_rel
        c["arquivo"] = saida.relative_to(RAIZ).as_posix()
        c["musica"] = {"arquivo": musica.name, "volume": vol}
        feitos += 1

    # Relê antes de gravar para não apagar o que outro processo escreveu.
    por_n = {int(c["n"]): c for c in dados.get("cortes", [])}
    atual = json.loads(arq_json.read_text(encoding="utf-8"))
    for c in atual.get("cortes", []):
        r = por_n.get(int(c["n"]))
        if r:
            for k in ("arquivo", "arquivo_sem_musica", "musica"):
                if k in r:
                    c[k] = r[k]
                else:
                    c.pop(k, None)
    arq_json.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK música em {feitos} corte(s)")


if __name__ == "__main__":
    main()
