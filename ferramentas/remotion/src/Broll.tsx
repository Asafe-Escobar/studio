import React from "react";
import { AbsoluteFill, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { fontFamily } from "./fonte";
import type { Broll as BrollT } from "./tipos";

const SAIDA = (frame: number, total: number) =>
  interpolate(frame, [0, 3, total - 4, total], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

// Imagem/vídeo de apoio cobrindo a tela com Ken Burns.
const Midia: React.FC<{ b: BrollT; i: number }> = ({ b, i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = b.dur * fps;
  const escala = interpolate(frame, [0, 6, total], [1.18, 1.06, 1.16], { extrapolateRight: "clamp", easing: Easing.bezier(0.33, 1, 0.68, 1) });
  const deriva = interpolate(frame, [0, total], i % 2 ? ["-2% 0%", "2% -1%"] : ["2% 1%", "-2% -1%"], { extrapolateRight: "clamp" });
  const estilo: React.CSSProperties = { width: "100%", height: "100%", objectFit: "cover" };
  return (
    <AbsoluteFill style={{ opacity: SAIDA(frame, total), backgroundColor: "#000" }}>
      <AbsoluteFill style={{ scale: escala, translate: deriva }}>
        {b.tipo === "video" ? <Video src={staticFile(b.src || "")} muted style={estilo} /> : <Img src={staticFile(b.src || "")} style={estilo} />}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 100%)" }} />
    </AbsoluteFill>
  );
};

const ICONE: Record<string, string> = { erro: "✕", dica: "✓", alerta: "!", numero: "", frase: "" };

// Gráfico animado feito em código: fundo escuro com grade em movimento e brilho na cor da marca,
// selo com ícone, rótulo e título grande. A fala continua por baixo; a legenda fica por cima.
const Grafico: React.FC<{ b: BrollT; cor: string; i: number }> = ({ b, cor, i }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const total = b.dur * fps;
  const v = b.variante || "frase";
  const corV = v === "dica" ? "#22C55E" : v === "alerta" ? "#F59E0B" : cor;
  const mola = (atraso: number) =>
    interpolate(frame - atraso, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.2, 1.45, 0.4, 1) });
  const grade = interpolate(frame, [0, total], [0, 60]);
  const brilho = interpolate(frame, [0, total], i % 2 ? [30, 70] : [70, 30]);
  const selo = mola(0);
  const texto = mola(4);
  const rotulo = mola(2);
  const icone = b.icone || ICONE[v];
  return (
    <AbsoluteFill style={{ opacity: SAIDA(frame, total), backgroundColor: "#0A0A0C", overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.06) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.06) 2px, transparent 2px)`,
          backgroundSize: "90px 90px",
          backgroundPosition: `${grade}px ${grade}px`,
        }}
      />
      <AbsoluteFill style={{ background: `radial-gradient(circle at ${brilho}% 35%, ${corV}55 0%, transparent 55%)` }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: height * 0.18 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 34, width: width - 160 }}>
          {v === "numero" ? (
            <div style={{ fontFamily, fontWeight: 900, fontSize: width * 0.32, lineHeight: 1, color: corV, scale: selo, textShadow: `0 0 60px ${corV}88` }}>
              {b.titulo?.split(" ")[0]}
            </div>
          ) : icone ? (
            <div
              style={{
                width: width * 0.28,
                height: width * 0.28,
                borderRadius: "50%",
                background: corV,
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                fontFamily,
                fontWeight: 900,
                fontSize: width * 0.17,
                color: "#fff",
                scale: selo,
                rotate: `${interpolate(selo, [0, 1], [-25, 0])}deg`,
                boxShadow: `0 0 0 18px ${corV}33, 0 30px 80px rgba(0,0,0,0.5)`,
              }}
            >
              {icone}
            </div>
          ) : null}
          {b.rotulo && (
            <div
              style={{
                fontFamily,
                fontWeight: 800,
                fontSize: width * 0.05,
                letterSpacing: 6,
                color: "#0A0A0C",
                background: "#FFFFFF",
                padding: "10px 26px",
                borderRadius: 12,
                textTransform: "uppercase",
                opacity: rotulo,
                translate: `0 ${interpolate(rotulo, [0, 1], [30, 0])}px`,
              }}
            >
              {b.rotulo}
            </div>
          )}
          {b.titulo && (
            <div
              style={{
                fontFamily,
                fontWeight: 900,
                fontSize: width * ((b.titulo.length > 30 ? 0.075 : 0.092)),
                lineHeight: 1.05,
                color: "#FFFFFF",
                textAlign: "center",
                textTransform: "uppercase",
                opacity: texto,
                translate: `0 ${interpolate(texto, [0, 1], [40, 0])}px`,
              }}
            >
              {v === "numero" ? b.titulo.split(" ").slice(1).join(" ") : b.titulo}
            </div>
          )}
          <div style={{ height: 10, width: interpolate(texto, [0, 1], [0, width * 0.3]), background: corV, borderRadius: 5 }} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const Brolls: React.FC<{ itens: BrollT[]; cor: string }> = ({ itens, cor }) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {itens.map((b, i) => (
        <Sequence key={i} from={Math.round(b.t * fps)} durationInFrames={Math.max(1, Math.round(b.dur * fps))} premountFor={fps}>
          {b.tipo === "grafico" ? <Grafico b={b} cor={cor} i={i} /> : <Midia b={b} i={i} />}
        </Sequence>
      ))}
    </>
  );
};
