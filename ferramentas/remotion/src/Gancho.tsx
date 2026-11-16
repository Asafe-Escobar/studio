import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./fonte";
import type { Estilo } from "./tipos";

// Título de gancho no topo nos primeiros segundos.
// padrao: caixa branca com borda colorida. safe: texto branco grande com sombra escura (como os Reels do Safe Internato).
export const Gancho: React.FC<{ texto: string; ate: number; cor: string; estilo: Estilo }> = ({ texto, ate, cor, estilo }) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const fim = ate * fps;
  const entrada = interpolate(frame, [0, 6], [0.6, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.2, 1.5, 0.4, 1) });
  const opacidade = interpolate(frame, [0, 3, fim - 6, fim], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  if (estilo === "safe") {
    const tamanho = Math.round(width * (texto.length > 28 ? 0.085 : 0.1));
    return (
      <AbsoluteFill style={{ alignItems: "center" }}>
        <div
          style={{
            position: "absolute",
            top: "4%",
            maxWidth: width - 120,
            fontFamily,
            fontWeight: 900,
            fontSize: tamanho,
            lineHeight: 1.02,
            color: "#FFFFFF",
            textAlign: "center",
            textTransform: "uppercase",
            letterSpacing: 1,
            textShadow: "0 0 30px rgba(0,0,0,0.95), 0 0 60px rgba(0,0,0,0.8), 0 6px 0 rgba(0,0,0,0.6)",
            scale: entrada,
            opacity: opacidade,
          }}
        >
          {texto}
          <div style={{ height: 12, width: "38%", margin: "16px auto 0", background: cor, borderRadius: 6 }} />
        </div>
      </AbsoluteFill>
    );
  }

  const tamanho = Math.round(width * (texto.length > 32 ? 0.062 : 0.072));
  return (
    <AbsoluteFill style={{ alignItems: "center" }}>
      <div
        style={{
          position: "absolute",
          top: "11%",
          maxWidth: width - 140,
          padding: "22px 34px",
          background: "#FFFFFF",
          borderRadius: 22,
          borderBottom: `10px solid ${cor}`,
          boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
          fontFamily,
          fontWeight: 900,
          fontSize: tamanho,
          lineHeight: 1.1,
          color: "#0B0B0B",
          textAlign: "center",
          textTransform: "uppercase",
          scale: entrada,
          opacity: opacidade,
        }}
      >
        {texto}
      </div>
    </AbsoluteFill>
  );
};
