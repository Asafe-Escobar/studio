"""Baixa um vídeo (YouTube, Instagram, etc.) ou copia um arquivo local para midia/<id>/original.<ext>.

Uso: python ferramentas/podcast/baixar.py <url-ou-caminho> <id>
"""
import argparse
import shutil
from pathlib import Path

from comum import pasta, duracao, ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonte")
    ap.add_argument("id")
    ap.add_argument("--max-altura", type=int, default=1080)
    args = ap.parse_args()

    destino = pasta(args.id)
    for antigo in destino.glob("original.*"):
        antigo.unlink()

    local = Path(args.fonte)
    if local.exists():
        final = destino / f"original{local.suffix.lower()}"
        shutil.copy2(local, final)
    else:
        import yt_dlp
        opcoes = {
            "outtmpl": str(destino / "original.%(ext)s"),
            "format": f"bv*[height<={args.max_altura}]+ba/b[height<={args.max_altura}]/b",
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": False,
        }
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(args.fonte, download=True)
            (destino / "info.txt").write_text(
                f"titulo: {info.get('title')}\ncanal: {info.get('uploader')}\nurl: {args.fonte}\n",
                encoding="utf-8",
            )
        final = next(destino.glob("original.*"))

    print(f"OK {final} ({ts(duracao(final))})")


if __name__ == "__main__":
    main()
