import React, { useMemo } from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./fonte";
import type { Estilo, Palavra } from "./tipos";

type Pagina = { ini: number; fim: number; palavras: Palavra[] };

// Agrupa em páginas curtas (até 3 palavras), quebrando em pontuação e em pausas.
function paginar(palavras: Palavra[]): Pagina[] {
  const paginas: Pagina[] = [];
  let atual: Palavra[] = [];
  const fechar = () => {
    if (atual.length) paginas.push({ ini: atual[0].t, fim: atual[atual.length - 1].f, palavras: atual });
    atual = [];
  };
  for (const p of palavras) {
    const ultima = atual[atual.length - 1];
    if (ultima && p.t - ultima.f > 0.35) fechar();
    atual.push(p);
    const chars = atual.reduce((n, x) => n + x.w.length, 0);
    if (atual.length >= 3 || chars > 16 || /[.?!,:;]$/.test(p.w)) fechar();
  }
  fechar();
  return paginas;
}

const limpar = (w: string) => w.replace(/[.,;:]+$/, "").toUpperCase();

const PaginaLegenda: React.FC<{ pagina: Pagina; cor: string; pos: number; estilo: Estilo }> = ({ pagina, cor, pos, estilo }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const agora = pagina.ini + frame / fps;
  const entrada = interpolate(frame, [0, 4], [0.85, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.2, 1.4, 0.4, 1) });
  const tamanho = Math.round(width * 0.08);
  const contorno = Math.max(6, Math.round(tamanho / 10));
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: `${pos * 100}%`,
          translate: "0 -50%",
          width: width - 160,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          columnGap: Math.round(tamanho * 0.3),
          rowGap: Math.round(tamanho * 0.12),
          scale: entrada,
          fontFamily,
          fontWeight: 900,
          fontSize: tamanho,
          lineHeight: 1.1,
          textAlign: "center",
        }}
      >
        {pagina.palavras.map((p, i) => {
          const ativa = agora >= p.t && agora < Math.max(p.f, p.t + 0.12);
          const local = (agora - p.t) * fps;
          const pulo = ativa ? interpolate(local, [0, 3, 7], [1, 1.12, 1.05], { extrapolateRight: "clamp" }) : 1;
          // safe: palavra falada ganha caixa vermelha; destaque fica vermelho. padrao: destaque na cor, sem caixa.
          const caixa = estilo === "safe" && ativa;
          const corTexto = caixa ? "#FFFFFF" : p.destaque ? cor : "#FFFFFF";
          return (
            <span
              key={i}
              style={{
                display: "inline-block",
                scale: pulo,
                color: corTexto,
                padding: caixa ? "2px 16px 6px" : "0 2px",
                borderRadius: 14,
                background: caixa ? cor : "transparent",
                WebkitTextStroke: caixa ? undefined : `${contorno}px #000`,
                paintOrder: "stroke fill",
                textShadow: caixa ? "none" : "0 6px 18px rgba(0,0,0,0.6)",
                boxShadow: caixa ? "0 10px 26px rgba(0,0,0,0.35)" : undefined,
              }}
            >
              {limpar(p.w)}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Legenda: React.FC<{ palavras: Palavra[]; cor: string; pos: number; estilo: Estilo }> = ({ palavras, cor, pos, estilo }) => {
  const { fps } = useVideoConfig();
  const paginas = useMemo(() => paginar(palavras), [palavras]);
  return (
    <AbsoluteFill>
      {paginas.map((pg, i) => {
        const prox = paginas[i + 1];
        const de = Math.round(pg.ini * fps);
        const ate = Math.round(Math.min(prox ? prox.ini : Infinity, pg.fim + 0.5) * fps);
        if (ate - de <= 0) return null;
        return (
          <Sequence key={i} from={de} durationInFrames={ate - de} layout="none">
            <PaginaLegenda pagina={pg} cor={cor} pos={pos} estilo={estilo} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
