import React from "react";
import { AbsoluteFill, Easing, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio, Video } from "@remotion/media";
import { Legenda } from "./Legenda";
import { Gancho } from "./Gancho";
import { Brolls } from "./Broll";
import type { EdicaoProps, Enfase } from "./tipos";

// Zoom de ênfase: aproxima rápido no ponto forte, segura e volta devagar.
function zoomEnfase(t: number, enfases: Enfase[]): number {
  let extra = 0;
  for (const e of enfases) {
    const v = interpolate(t, [e.t - 0.05, e.t + 0.18, e.t + e.dur, e.t + e.dur + 0.45], [0, 0.13, 0.13, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.33, 1, 0.68, 1),
    });
    extra = Math.max(extra, v);
  }
  return extra;
}

export const Edicao: React.FC<EdicaoProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // Linha do tempo: cada segmento do vídeo base vira um bloco; entre eles, o "pulo" fica escondido pela troca de zoom.
  let inicio = 0;
  const blocos = props.segmentos.map((s, i) => {
    const dur = Math.max(1, Math.round((s.ate - s.de) * fps));
    const bloco = { ...s, from: inicio, dur, i };
    inicio += dur;
    return bloco;
  });
  const extra = zoomEnfase(t, props.enfases);
  const progresso = Math.min(1, t / props.duracao);

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {blocos.map((b) => (
        <Sequence key={b.i} from={b.from} durationInFrames={b.dur} premountFor={fps}>
          <AbsoluteFill style={{ scale: b.zoom + extra, transformOrigin: "50% 38%" }}>
            <Video
              src={staticFile(props.video)}
              trimBefore={Math.round(b.de * fps)}
              trimAfter={Math.round(b.de * fps) + b.dur}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </Sequence>
      ))}

      {(props.broll || []).length > 0 && <Brolls itens={props.broll} cor={props.cor} />}

      {props.legenda && props.palavras.length > 0 && (
        <Legenda palavras={props.palavras} cor={props.cor} pos={props.posLegenda} estilo={props.estilo || "padrao"} />
      )}

      {props.gancho && props.gancho.texto && (
        <Sequence durationInFrames={Math.round(props.gancho.ate * fps)} layout="none">
          <Gancho texto={props.gancho.texto} ate={props.gancho.ate} cor={props.cor} estilo={props.estilo || "padrao"} />
        </Sequence>
      )}

      {(props.sfx || []).map((s, i) => (
        <Sequence key={`sfx-${i}`} from={Math.max(0, Math.round(s.t * fps))} layout="none">
          <Audio src={staticFile(s.som)} volume={s.volume} />
        </Sequence>
      ))}

      {props.barra && (
        <AbsoluteFill>
          <div style={{ position: "absolute", left: 0, bottom: 0, height: 12, width: "100%", background: "rgba(255,255,255,0.18)" }} />
          <div style={{ position: "absolute", left: 0, bottom: 0, height: 12, width: `${progresso * 100}%`, background: props.cor }} />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
