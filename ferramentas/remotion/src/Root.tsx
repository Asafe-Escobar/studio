import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import { Edicao } from "./Edicao";
import { PADRAO, type EdicaoProps } from "./tipos";

const metadados: CalculateMetadataFunction<EdicaoProps> = ({ props }) => ({
  durationInFrames: Math.max(1, Math.round(props.duracao * props.fps)),
  fps: props.fps,
  width: props.largura,
  height: props.altura,
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Edicao"
    component={Edicao}
    durationInFrames={150}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={PADRAO}
    calculateMetadata={metadados}
  />
);
