"""Transcreve midia/<id>/original.* com faster-whisper (palavra a palavra).

Gera:
  midia/<id>/transcricao.json  segmentos + palavras com tempo (usado para legendas)
  midia/<id>/transcricao.txt   [HH:MM:SS.s] texto  (para o editor escolher os cortes)

Uso: python ferramentas/podcast/transcrever.py <id> [--modelo small|medium|large-v3] [--idioma pt]
"""
import argparse
import os
import json
import subprocess
import time

from comum import pasta, original, ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--device", default="cpu", help="cpu (padrão) ou cuda, se o CUDA/cuBLAS estiver instalado")
    args = ap.parse_args()

    p = pasta(args.id)
    audio = p / "audio.wav"
    if not audio.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(original(args.id)), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)],
            check=True,
        )

    from faster_whisper import WhisperModel
    inicio = time.time()
    try:
        # Usa o modelo do cache sem consultar a internet (evita falhas de SSL/rede quando já está baixado).
        modelo = WhisperModel(args.modelo, device=args.device, compute_type="int8", cpu_threads=os.cpu_count() or 4, local_files_only=True)
    except Exception:
        modelo = WhisperModel(args.modelo, device=args.device, compute_type="int8", cpu_threads=os.cpu_count() or 4)
    # Lê o WAV (16 kHz mono, PCM 16 bits) com numpy: evita o decodificador do PyAV, que varia entre versões.
    import wave
    import numpy as np
    with wave.open(str(audio), "rb") as w:
        amostras = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segmentos, info = modelo.transcribe(
        amostras, language=args.idioma, word_timestamps=True, vad_filter=True, beam_size=5,
    )

    saida, linhas = [], []
    for seg in segmentos:
        palavras = [
            {"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
            for w in (seg.words or []) if w.word.strip()
        ]
        saida.append({"s": round(seg.start, 2), "e": round(seg.end, 2), "texto": seg.text.strip(), "palavras": palavras})
        linhas.append(f"[{ts(seg.start)}] {seg.text.strip()}")
        print(linhas[-1], flush=True)

    (p / "transcricao.json").write_text(json.dumps({"duracao_s": info.duration, "segmentos": saida}, ensure_ascii=False), encoding="utf-8")
    (p / "transcricao.txt").write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nOK {len(saida)} segmentos em {time.time() - inicio:.0f}s -> {p / 'transcricao.txt'}")


if __name__ == "__main__":
    main()
