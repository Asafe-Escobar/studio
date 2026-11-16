"""Utilidades compartilhadas pelas ferramentas de podcast."""
from pathlib import Path
import json
import re
import shutil
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[2]
MIDIA = RAIZ / "midia"
DADOS = RAIZ / "dados"

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def limpar_palavra(w):
    """Texto de legenda limpo: desfaz &gt;/&amp; do VTT do YouTube, tira o '>>' (troca de quem fala) e marcas como [Música].
    Devolve '' quando não sobra palavra (o chamador descarta)."""
    import html
    w = html.unescape(html.unescape(str(w or "")))
    w = re.sub(r"\[[^\]]*\]", " ", w)          # [Música], [Aplausos]
    w = w.replace(">>", " ").replace(">", " ").replace("<", " ")
    return re.sub(r"\s+", " ", w).strip()


def limpar_palavras(palavras):
    saida = []
    for p in palavras:
        w = limpar_palavra(p.get("w"))
        if w:
            saida.append({**p, "w": w})
    return saida


def pasta(id_: str) -> Path:
    p = MIDIA / id_
    p.mkdir(parents=True, exist_ok=True)
    return p


def original(id_: str) -> Path:
    candidatos = sorted(pasta(id_).glob("original.*"))
    if not candidatos:
        sys.exit(f"Nenhum arquivo original em {pasta(id_)}. Rode baixar.py primeiro.")
    return candidatos[0]


def ts(segundos: float) -> str:
    h = int(segundos // 3600)
    m = int(segundos % 3600 // 60)
    s = segundos % 60
    return f"{h:02d}:{m:02d}:{s:04.1f}"


def para_segundos(valor) -> float:
    if isinstance(valor, (int, float)):
        return float(valor)
    partes = [float(x) for x in str(valor).replace(",", ".").split(":")]
    total = 0.0
    for parte in partes:
        total = total * 60 + parte
    return total


def duracao(arquivo: Path) -> float:
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(arquivo)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(saida)["format"]["duration"])


def dimensoes(arquivo: Path):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "json", str(arquivo)],
        capture_output=True, text=True,
    ).stdout
    streams = json.loads(saida or "{}").get("streams") or []
    if not streams:
        return None
    return streams[0]["width"], streams[0]["height"]


def exige(binario: str):
    if not shutil.which(binario):
        sys.exit(f"'{binario}' não encontrado no PATH.")
