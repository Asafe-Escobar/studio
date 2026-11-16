"""Descobre quem está falando em cada momento e devolve para onde o recorte 9:16 deve apontar.

Como funciona:
  - analisa ~10 quadros por segundo; acha os rostos (YuNet, OpenCV) com olhos, nariz e cantos da boca;
  - mede o movimento da região da boca de cada rosto, descontando o movimento da cabeça;
  - quem mexe mais a boca de forma sustentada é o falante; a troca exige ~0,6 s de vantagem (sem pulos);
  - corte de câmera no vídeo original (mudança brusca de imagem) reinicia o rastreamento e o recorte pula junto.

Uso (teste): python ferramentas/podcast/enquadrar.py <arquivo> <inicio_s> <fim_s>
No pipeline: cortar.py --modo crop chama trajetoria() e move o recorte com sendcmd do ffmpeg.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

MODELO = Path(__file__).resolve().parents[1] / "modelos" / "face_detection_yunet_2023mar.onnx"
LARG_ANALISE = 640
FPS_ANALISE = 10


def _roi(cinza, x0, y0, x1, y1, tam=(32, 24)):
    h, w = cinza.shape
    x0, x1 = max(0, int(x0)), min(w, int(x1))
    y0, y1 = max(0, int(y0)), min(h, int(y1))
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    return cv2.resize(cinza[y0:y1, x0:x1], tam, interpolation=cv2.INTER_AREA).astype(np.float32)


def trajetoria(arquivo, ini, fim):
    """Lista de (t_relativo_s, centro_x_normalizado 0..1). Vazia se não achar rostos."""
    if not MODELO.exists():
        return []
    cap = cv2.VideoCapture(str(arquivo))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    H = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    escala = LARG_ANALISE / W
    tam = (LARG_ANALISE, int(H * escala))
    det = cv2.FaceDetectorYN.create(str(MODELO), "", tam, 0.7)
    passo = max(1, round(fps / FPS_ANALISE))

    cap.set(cv2.CAP_PROP_POS_MSEC, ini * 1000)
    total = int((fim - ini) * fps)
    amostras = []          # (t, [faces]) faces = dict(cx, w, boca, cabeca)
    anterior_hist = None
    trilhas = []           # dict(cx, roi_boca, roi_face, energia)
    for k in range(total):
        if k % passo:
            if not cap.grab():
                break
            continue
        ok, quadro = cap.read()
        if not ok:
            break
        t = k / fps
        peq = cv2.resize(quadro, tam, interpolation=cv2.INTER_AREA)
        cinza = cv2.cvtColor(peq, cv2.COLOR_BGR2GRAY)

        # corte de câmera: histograma muda muito
        hist = cv2.calcHist([cinza], [0], None, [32], [0, 256])
        cv2.normalize(hist, hist)
        corte = anterior_hist is not None and cv2.compareHist(anterior_hist, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.35
        anterior_hist = hist
        if corte:
            trilhas = []

        _, faces = det.detect(peq)
        atuais = []
        for f in (faces if faces is not None else []):
            x, y, w, h = f[:4]
            nariz_y = f[9]
            bd_x, bd_y, be_x, be_y = f[10], f[11], f[12], f[13]
            boca_y = (bd_y + be_y) / 2
            alt = max(boca_y - nariz_y, h * 0.08)
            roi_boca = _roi(cinza, min(bd_x, be_x) - w * 0.1, nariz_y + alt * 0.3, max(bd_x, be_x) + w * 0.1, boca_y + alt * 1.4)
            roi_face = _roi(cinza, x, y, x + w, y + h * 0.55)
            cx = (x + w / 2) / tam[0]
            # associa à trilha mais próxima
            tr = min(trilhas, key=lambda r: abs(r["cx"] - cx), default=None)
            if tr is None or abs(tr["cx"] - cx) > 0.12:
                tr = {"cx": cx, "roi_boca": None, "roi_face": None, "energia": 0.0, "id": len(trilhas) + len(amostras) * 10}
                trilhas.append(tr)
            mov = 0.0
            if roi_boca is not None and tr["roi_boca"] is not None and roi_face is not None and tr["roi_face"] is not None:
                d_boca = float(np.mean(np.abs(roi_boca - tr["roi_boca"])))
                d_face = float(np.mean(np.abs(roi_face - tr["roi_face"])))
                mov = max(0.0, d_boca - 0.6 * d_face)
            tr.update(cx=cx, roi_boca=roi_boca, roi_face=roi_face, energia=0.75 * tr["energia"] + 0.25 * mov)
            atuais.append({"cx": cx, "w": w / tam[0], "energia": tr["energia"], "id": tr["id"]})
        trilhas = [r for r in trilhas if any(a["id"] == r["id"] for a in atuais)]
        amostras.append((t, atuais, corte))
    cap.release()
    if not any(a for _, a, _ in amostras):
        return []

    # escolhe o falante com histerese
    pontos, atual_id, desafiante, cont, x_suave, ultimo_x = [], None, None, 0, None, 0.5
    for t, faces, corte in amostras:
        if corte:
            atual_id, x_suave = None, None
        if not faces:
            pontos.append((t, x_suave if x_suave is not None else ultimo_x, bool(corte)))
            continue
        if len(faces) == 1:
            alvo = faces[0]
        else:
            melhor = max(faces, key=lambda f: f["energia"])
            vigente = next((f for f in faces if f["id"] == atual_id), None)
            if vigente is None:
                alvo = melhor
            elif melhor["id"] != vigente["id"] and melhor["energia"] > vigente["energia"] * 1.4 + 0.15:
                cont = cont + 1 if desafiante == melhor["id"] else 1
                desafiante = melhor["id"]
                alvo = melhor if cont >= 6 else vigente
            else:
                cont, desafiante, alvo = 0, None, vigente
        trocou = alvo["id"] != atual_id or corte
        atual_id = alvo["id"]
        x_suave = alvo["cx"]
        ultimo_x = x_suave
        pontos.append((t, x_suave, trocou))
    return estabilizar(pontos)


def estabilizar(pontos, zona=0.06, janela=9):
    """Câmera parada: mediana para tirar ruído, segura enquanto o rosto fica na zona central e só desliza
    (com suavização) quando ele sai dela. Troca de falante ou corte de câmera = pulo seco."""
    if not pontos:
        return []
    brutos = [(p[0], p[1], p[2] if len(p) > 2 else False) for p in pontos]
    # mediana por plano (não mistura antes e depois de um pulo)
    filtrado, bloco = [], []
    def fechar():
        xs = [b[1] for b in bloco]
        for k, (t, _, salto) in enumerate(bloco):
            viz = sorted(xs[max(0, k - janela // 2): k + janela // 2 + 1])
            filtrado.append((t, viz[len(viz) // 2], salto))
    for p in brutos:
        if p[2] and bloco:
            fechar()
            bloco = []
        bloco.append(p)
    if bloco:
        fechar()

    saida, cam, alvo_mov = [], None, None
    for t, x, salto in filtrado:
        if cam is None or salto:
            cam, alvo_mov = x, None
        elif alvo_mov is not None:
            cam += (alvo_mov - cam) * 0.18
            if abs(alvo_mov - cam) < 0.008:
                cam, alvo_mov = alvo_mov, None
        elif abs(x - cam) > zona:
            alvo_mov = x
        saida.append((t, cam))
    return saida


if __name__ == "__main__":
    arq, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    pts = trajetoria(arq, a, b)
    print(f"{len(pts)} pontos")
    for t, x in pts[:: max(1, len(pts) // 25)]:
        print(f"{t:6.1f}s  x={x:.2f}  " + " " * int(x * 60) + "█")
