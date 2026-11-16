// Plano de edição que o Python (ferramentas/remotion/editar.py) monta e o Remotion renderiza.
// Todos os tempos em segundos. "de/ate" são do vídeo base; o resto é na linha do tempo final.

export type Segmento = { de: number; ate: number; zoom: number };
export type Palavra = { t: number; f: number; w: string; destaque: boolean };
export type Enfase = { t: number; dur: number };
// B-roll: imagem ou vídeo que cobre a tela enquanto a fala continua.
export type Broll = {
  t: number;
  dur: number;
  tipo: "imagem" | "video" | "grafico";
  src?: string; // imagem/vídeo dentro do public-dir
  // gráfico animado (feito em código): erro = ✕ vermelho, dica = ✓, numero = número grande, alerta = ⚠, frase = frase de impacto
  variante?: "erro" | "dica" | "numero" | "alerta" | "frase";
  rotulo?: string; // ex.: "ERRO Nº 1"
  titulo?: string; // texto principal (até ~6 palavras)
  icone?: string; // emoji opcional
};
// padrao = caixa branca no título e palavra amarela; safe = título branco com sombra e palavra em caixa vermelha.
export type Estilo = "padrao" | "safe";

// Efeito sonoro: arquivo dentro do public-dir, tocado no tempo t (s) da linha final.
export type Sfx = { t: number; som: string; volume: number };

export type EdicaoProps = {
  video: string; // arquivo dentro do public-dir
  fps: number;
  largura: number;
  altura: number;
  duracao: number; // duração final (s)
  segmentos: Segmento[];
  palavras: Palavra[];
  enfases: Enfase[];
  gancho: { texto: string; ate: number } | null;
  legenda: boolean;
  barra: boolean;
  cor: string; // cor de destaque
  posLegenda: number; // 0..1, altura do centro da legenda
  broll: Broll[];
  estilo: Estilo;
  sfx: Sfx[];
};

export const PADRAO: EdicaoProps = {
  video: "base.mp4",
  fps: 30,
  largura: 1080,
  altura: 1920,
  duracao: 5,
  segmentos: [{ de: 0, ate: 5, zoom: 1 }],
  palavras: [],
  enfases: [],
  gancho: { texto: "Título de gancho", ate: 3 },
  legenda: true,
  barra: true,
  cor: "#FFD400",
  posLegenda: 0.7,
  broll: [],
  estilo: "padrao",
  sfx: [],
};
