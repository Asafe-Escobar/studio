// Studio da Agência Zero1: interface local que lê dados/ e dispara os fluxos.
// Uso: node studio/server.js  ->  http://localhost:4747
const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const RAIZ = path.resolve(__dirname, "..");
const DADOS = path.join(RAIZ, "dados");
const PUBLIC = path.join(__dirname, "public");
const JOBS = path.join(DADOS, "jobs");
const UPLOADS = path.join(RAIZ, "midia", "_uploads");
const PORTA = Number(process.env.PORTA || 4747);
const TIPOS = ["pesquisas", "cortes", "campanhas", "carrosseis"];
const PYTHON = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
fs.mkdirSync(JOBS, { recursive: true });
fs.mkdirSync(UPLOADS, { recursive: true });

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
  ".svg": "image/svg+xml", ".mp3": "audio/mpeg" };

// Ferramentas que os agentes podem usar quando o Studio dispara o Claude sem ninguém no terminal.
const FERRAMENTAS_CLAUDE = ["Read", "Write", "Edit", "Glob", "Grep", "Agent", "Skill", "WebSearch", "WebFetch",
  "Bash(python:*)", "Bash(ffmpeg:*)", "Bash(ffprobe:*)", "Bash(yt-dlp:*)", "Bash(mkdir:*)", "Bash(ls:*)",
  "mcp__apify", "mcp__muapi"].join(" ");

const hoje = () => new Date().toISOString().slice(0, 10);
const slug = (s) => String(s || "item").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
  .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48) || "item";

function novoId(tipo, base) {
  let id = `${hoje()}-${slug(base)}`;
  let k = 2;
  while (fs.existsSync(path.join(DADOS, tipo, `${id}.json`)) || fs.existsSync(path.join(RAIZ, "midia", id))) id = `${hoje()}-${slug(base)}-${k++}`;
  return id;
}

// Regra de velocidade anexada a todo fluxo com agentes: o usuário espera resultado em poucos minutos.
const RAPIDO = "\n\nVELOCIDADE (obrigatório): entregue em poucos minutos. Não transcreva vídeos de referência (Whisper em CPU" +
  " leva minutos por vídeo): use legenda, gancho, capa (.jpg) e métricas já coletados. Se o pedido for 'ver o estilo' de alguém," +
  " leia as legendas e no máximo 2 capas. Nada de downloads em massa, render ou etapas que o pedido não exige. Não fique" +
  " esperando tarefa em segundo plano: rode agentes independentes em paralelo." +
  " ENTREGA AO VIVO: o Studio mostra as partes antes do fim. Cada agente grava a sua parte assim que terminar em" +
  " midia/<id-da-entrega>/parciais/: estrategia.json ({\"estrategia\":{...}}), roteiros-<n>.json (array de roteiros)," +
  " calendario.json (array), copies.json (array). Mande isso no briefing de cada agente. No fim, junte tudo no JSON de dados/.";

// Biblioteca de música de fundo (só faixas livres de direitos ou próprias).
const MUSICAS = path.join(RAIZ, "midia", "musicas");
const EXT_MUSICA = [".mp3", ".m4a", ".wav", ".aac", ".ogg"];
const listarMusicas = () => (fs.existsSync(MUSICAS) ? fs.readdirSync(MUSICAS).filter((f) => EXT_MUSICA.includes(path.extname(f).toLowerCase())).sort() : []);
const musicaValida = (m) => !!m && listarMusicas().includes(m);
const volumeOk = (v) => Math.min(Math.max(Number(v) || 0.15, 0.03), 0.5);
function argsMusica(args, e) { if (musicaValida(e.musica)) args.push("--musica", e.musica, "--volume", String(volumeOk(e.volume))); }

const linha = (s) => String(s ?? "").replace(/[\r\n]+/g, " ").trim();
const cli = (e) => (e.cliente ? ` Cliente: ${linha(e.cliente)} (leia clientes/${slug(e.cliente)}/perfil.md se existir).` : "");

// Cada fluxo devolve { titulo, entrega:{tipo,id}, claude: prompt } ou { ..., python: [args] }
const FLUXOS = {
  pesquisa(e) {
    if (!e.nicho) throw new Error("Informe o nicho.");
    const id = /^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$/.test(e.id || "") ? e.id : novoId("pesquisas", e.nicho);
    const redes = (e.redes || ["instagram", "tiktok"]).join(" e ");
    return { titulo: `Pesquisa: ${e.nicho}`, entrega: { tipo: "pesquisas", id },
      claude: `/pesquisa-nicho ${linha(e.nicho)}.${cli(e)} Redes: ${redes}.` +
        (e.perfis ? ` Perfis de referência: ${linha(e.perfis).split(/[\s,;]+/).filter(Boolean).map((x) => "@" + x.replace(/^@/, "").replace(/\/$/, "").split("/").pop()).join(" ")}.` : "") +
        (e.contexto ? ` Contexto: ${linha(e.contexto)}` : "") +
        ` Entregue ${Number(e.roteiros) || 6} roteiros. Use o id ${id} e salve em dados/pesquisas/${id}.json.` };
  },
  estrategia(e) {
    if (!e.objetivo && !e.base) throw new Error("Escolha uma pesquisa base ou descreva o objetivo.");
    const id = novoId("campanhas", e.cliente || e.objetivo || "estrategia");
    const base = e.base ? ` Base: dados/pesquisas/${linha(e.base)}.json (use os formatos, padrões e posts de referência dela).` : "";
    const formatos = (e.formatos || []).length ? ` Formatos preferidos: ${e.formatos.join(", ")}.` : " Escolha os formatos pelo que a pesquisa mostrou.";
    return { titulo: `Estratégia: ${e.cliente || e.objetivo || e.base}`, entrega: { tipo: "campanhas", id },
      claude: `Você é o Diretor da Agência Zero1. Monte uma estratégia de conteúdo orgânico com roteiros.${cli(e)}${base}` +
        ` Objetivo: ${linha(e.objetivo) || "definir a partir da pesquisa"}. Rede principal: ${linha(e.rede) || "instagram"}.` +
        ` Quantidade de roteiros: ${Number(e.roteiros) || 6}.${formatos}` +
        ` Delegue: estrategista (posicionamento, pilares, funil); assim que ela sair, salve o JSON já com a estrategia e chame em paralelo, na mesma mensagem, roteiristas em lotes de até 3 roteiros (cada um já entrega legenda, hashtags, CTA e 2 ganchos_alternativos; não chame copywriter) e social-media (calendário de 4 semanas).` +
        ` Salve em dados/campanhas/${id}.json no schema Campanha do CLAUDE.md com tipo "campanha", preenchendo estrategia, roteiros e calendario; copies de anúncio e trafego podem ficar vazios. Valide com python -m json.tool.` };
  },
  campanha(e) {
    if (!e.cliente) throw new Error("Informe o cliente ou produto.");
    const id = novoId("campanhas", e.cliente);
    return { titulo: `Campanha: ${e.cliente}`, entrega: { tipo: "campanhas", id },
      claude: `/campanha ${linha(e.cliente)} ${linha(e.objetivo)}. Salve com id ${id} em dados/campanhas/${id}.json.` };
  },
  "cortes-ia"(e) {
    if (!e.fonte) throw new Error("Informe o link ou envie o arquivo.");
    const id = /^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$/.test(e.id || "") ? e.id
      : novoId("cortes", e.titulo || (/^https?:/.test(e.fonte) ? "podcast" : path.parse(e.fonte).name) || "podcast");
    // Pipeline local (baixa, transcreve, IA escolhe numa chamada só, renderiza): não depende de agente segurando processo.
    const args = ["ferramentas/podcast/cortes_ia.py", e.fonte, id, "--quantidade", String(Number(e.quantidade) || 8),
      "--min", String(Number(e.min) || 30), "--max", String(Number(e.max) || 75), "--modo", e.modo || "crop"];
    if (e.legenda === false) args.push("--sem-legenda");
    if (e.temas) args.push("--temas", linha(e.temas));
    if (e.titulo) args.push("--titulo", linha(e.titulo));
    if (e.nicho) args.push("--nicho", linha(e.nicho));
    if (/^[a-z0-9-]+$/.test(e.pesquisa || "")) args.push("--pesquisa", e.pesquisa);
    return { titulo: `Cortes (IA): ${e.titulo || e.fonte}`, entrega: { tipo: "cortes", id }, python: args };
  },
  "cortes-manual"(e) {
    if (!e.fonte) throw new Error("Informe o link ou envie o arquivo.");
    const cortes = (e.cortes || []).filter((c) => c.inicio && c.fim);
    if (!cortes.length) throw new Error("Adicione ao menos um trecho com início e fim.");
    const id = novoId("cortes", e.titulo || path.parse(e.fonte).name || "podcast");
    const args = ["ferramentas/podcast/manual.py", e.fonte, id, "--cortes", JSON.stringify(cortes), "--modo", e.modo || "crop"];
    if (e.titulo) args.push("--titulo", e.titulo);
    if (e.legenda === false) args.push("--sem-legenda");
    argsMusica(args, e);
    return { titulo: `Cortes (${cortes.length} trechos): ${e.titulo || path.basename(e.fonte)}`, entrega: { tipo: "cortes", id }, python: args };
  },
  editar(e) {
    if (!e.fonte) throw new Error("Envie o vídeo ou cole o link.");
    const id = novoId("cortes", e.titulo || path.parse(e.fonte).name || "video");
    const args = ["ferramentas/podcast/manual.py", e.fonte, id, "--edicao", "--modo", e.modo || "crop"];
    if (e.titulo) args.push("--titulo", e.titulo);
    if (e.inicio) args.push("--inicio", e.inicio);
    if (e.fim) args.push("--fim", e.fim);
    if (e.legenda === false) args.push("--sem-legenda");
    if (linha(e.pedido)) args.push("--pedido", linha(e.pedido).slice(0, 2000));
    argsMusica(args, e);
    return { titulo: `Edição: ${e.titulo || path.basename(e.fonte)}`, entrega: { tipo: "cortes", id }, python: args };
  },
  musica(e) {
    if (!/^[a-z0-9-]+$/.test(e.id || "")) throw new Error("Vídeo inválido.");
    const args = ["ferramentas/podcast/musica.py", e.id];
    if (e.remover) args.push("--remover");
    else if (!musicaValida(e.musica)) throw new Error("Escolha uma música da biblioteca.");
    else args.push("--musica", e.musica, "--volume", String(volumeOk(e.volume)));
    if (e.so) args.push("--so", String(e.so).replace(/[^0-9,]/g, ""));
    return { titulo: e.remover ? "Tirar música" : `Música: ${e.musica}`, entrega: { tipo: "cortes", id: e.id }, python: args };
  },
  feedback(e) {
    if (!e.texto) throw new Error("Escreva o feedback.");
    return { titulo: `Treino: ${e.texto.slice(0, 60)}`, entrega: null, claude: `/feedback ${linha(e.texto)}` };
  },
};


// ---- Ações sobre um roteiro já entregue (botões do Studio) ----
function lerRoteiro(e) {
  const arq = String(e.arquivo || "").split("\\").join("/");
  if (!/^dados\/(pesquisas|cortes|campanhas)\/[a-z0-9-]+\.json$/.test(arq)) throw new Error("Roteiro de origem inválido.");
  const d = lerJSON(path.join(RAIZ, arq));
  const r = d && (d.roteiros || [])[Number(e.indice)];
  if (!r) throw new Error("Roteiro não encontrado.");
  return { arq, d, r, i: Number(e.indice) };
}
const REF = ({ arq, i, r }) => `o roteiro de índice ${i} (título "${linha(r.titulo)}") em ${arq}`;

Object.assign(FLUXOS, {
  carrossel(e) {
    const o = lerRoteiro(e);
    const id = novoId("carrosseis", o.r.titulo || "carrossel");
    const arroba = linha(e.arroba || "");
    const origem = { arquivo: o.arq, indice: o.i };
    if (o.r.formato === "carrossel" && (o.r.cenas || []).length >= 3) {
      const args = ["ferramentas/design/carrossel.py", id, "--de-roteiro", o.arq, "--indice", String(o.i)];
      if (arroba) args.push("--arroba", arroba);
      return { titulo: `Carrossel: ${o.r.titulo}`, entrega: { tipo: "carrosseis", id }, origem, python: args };
    }
    return { titulo: `Carrossel: ${o.r.titulo}`, entrega: { tipo: "carrosseis", id }, origem, modelo: "sonnet",
      claude: `Faça você mesmo, sem delegar e sem skills. Transforme ${REF(o)} em um carrossel de Instagram de 6 a 8 slides.` +
        ` Siga conhecimento/copywriter/playbook.md e a convenção de carrossel de conhecimento/roteirista/playbook.md: slide 1 = gancho forte (até 8 palavras), slides do meio = 1 ideia cada (título curto + texto de até 25 palavras), último = CTA (tipo "cta", texto do botão curto).` +
        ` Salve dados/carrosseis/${id}.json no schema descrito no topo de ferramentas/design/carrossel.py, com origem {"arquivo":"${o.arq}","indice":${o.i}}, arroba "${arroba}", legenda e hashtags. Depois rode: python ferramentas/design/carrossel.py ${id}` };
  },
  adaptar(e) {
    const o = lerRoteiro(e);
    return { titulo: `Adaptar para redes: ${o.r.titulo}`, entrega: { tipo: o.arq.split("/")[1], id: path.basename(o.arq, ".json") }, origem: { arquivo: o.arq, indice: o.i }, modelo: "sonnet",
      claude: `Faça você mesmo, sem delegar e sem skills. Você é o social media da agência: leia conhecimento/social-media/playbook.md e plataformas.md.` +
        ` Adapte ${REF(o)} para Instagram, TikTok, YouTube Shorts e LinkedIn. Grave no próprio objeto do roteiro a chave "adaptacoes": {"instagram":{"legenda","hashtags"},"tiktok":{"legenda","hashtags","texto_tela"},"shorts":{"titulo","descricao"},"linkedin":{"texto"}}.` +
        ` Leia o arquivo, altere só esse roteiro, grave e valide com python -m json.tool.` };
  },
  variacoes(e) {
    const o = lerRoteiro(e);
    return { titulo: `Variações: ${o.r.titulo}`, entrega: { tipo: o.arq.split("/")[1], id: path.basename(o.arq, ".json") }, origem: { arquivo: o.arq, indice: o.i }, modelo: "sonnet",
      claude: `Faça você mesmo, sem delegar e sem skills. Você é o roteirista da agência: leia conhecimento/roteirista/playbook.md.` +
        ` Escreva 2 variações de ${REF(o)}: mesma ideia central, ganchos e ângulos diferentes (uma pode trocar de formato para outro dos 14 do CLAUDE.md).` +
        ` Cada variação é um objeto Roteiro completo com "variacao_de": ${o.i}. Leia o arquivo, acrescente as 2 no FINAL do array roteiros (não mexa nos existentes), grave e valide com python -m json.tool.` };
  },
  anuncio(e) {
    const o = lerRoteiro(e);
    const id = novoId("campanhas", `anuncio ${o.r.titulo}`);
    return { titulo: `Anúncio: ${o.r.titulo}`, entrega: { tipo: "campanhas", id }, origem: { arquivo: o.arq, indice: o.i },
      claude: `Você é o Diretor. Transforme ${REF(o)} em anúncio para Meta Ads.` + cli(e) +
        ` Delegue em paralelo: copywriter (3 textos primários, 5 títulos, 2 descrições, com angulo e compliance) e gestor-trafego (estrutura de teste com 1 campanha, públicos e regra de corte; orçamento null se não informado).` +
        ` O roteiro original entra em roteiros e vira criativos[] (versão vídeo e versão estática). Salve dados/campanhas/${id}.json no schema Campanha do CLAUDE.md e valide com python -m json.tool.` };
  },
});

// Mostra na hora o que já existe em midia/<id>/: ranking de perfis da coleta e roteiros parciais dos roteiristas.
function enriquecer(d, id) {
  const resumo = lerJSON(path.join(RAIZ, "midia", id, "bruto", "resumo.json"));
  if (resumo && !Array.isArray(d.perfis)) d.perfis = resumo.perfis;
  // Mídia baixada dos posts em alta (ferramentas/instagram/videos.py): liga pelo shortcode da URL.
  const refs = path.join(RAIZ, "midia", id, "refs");
  if (fs.existsSync(refs) && Array.isArray(d.posts_referencia)) {
    const arquivos = new Set(fs.readdirSync(refs));
    for (const p of d.posts_referencia) {
      const c = (String(p.url || "").match(/\/(?:p|reel|reels|tv)\/([A-Za-z0-9_-]+)/) || [])[1];
      if (!c) continue;
      p.codigo = c;
      if (arquivos.has(`${c}.mp4`)) p.video = `midia/${id}/refs/${c}.mp4`;
      if (arquivos.has(`${c}.jpg`)) p.imagem = `midia/${id}/refs/${c}.jpg`;
    }
  }
  for (const c of d.cortes || []) {
    try { if (c.arquivo) c.versao = Math.round(fs.statSync(path.join(RAIZ, c.arquivo)).mtimeMs); } catch {}
  }
  // Partes soltas que os agentes gravam antes do JSON final: midia/<id>/*.json e midia/<id>/parciais/*.json.
  const partes = [];
  for (const dir of [path.join(RAIZ, "midia", id), path.join(RAIZ, "midia", id, "parciais")]) {
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".json")).sort()) partes.push([f, lerJSON(path.join(dir, f))]);
  }
  const titulos = new Set((d.roteiros || []).map((r) => r.titulo));
  for (const [f, p] of partes) {
    if (!p) continue;
    if (/^roteiros/.test(f) || p.roteiros) {
      for (const r of [].concat(p.roteiros || p)) {
        if (r && r.titulo && !titulos.has(r.titulo)) { titulos.add(r.titulo); (d.roteiros = d.roteiros || []).push({ ...r, _parcial: true }); }
      }
    }
    if (!d.estrategia && (p.estrategia || /^estrategia/.test(f))) d.estrategia = p.estrategia || p;
    if (!(d.calendario || []).length && (p.calendario || /^calendario/.test(f))) {
      const c = p.calendario || p; if (Array.isArray(c)) d.calendario = c;
    }
    if (!(d.copies || []).length && (p.copies || /^copies/.test(f))) {
      const c = p.copies || p; if (Array.isArray(c)) d.copies = c;
    }
  }
  return d;
}

// Entrega que ainda não tem JSON final, mas tem um job rodando: devolve um esqueleto para o Studio já mostrar as partes.
function esqueleto(tipo, id) {
  if (!fs.existsSync(JOBS)) return null;
  for (const f of fs.readdirSync(JOBS).filter((x) => x.endsWith(".json")).sort().reverse()) {
    const j = lerJSON(path.join(JOBS, f));
    if (j?.entrega?.id === id && j.entrega.tipo === tipo && j.status === "rodando") {
      return { id, tipo: tipo.replace(/s$/, ""), titulo: (j.titulo || "").replace(/^[^:]+:\s*/, ""), status: "produzindo",
        resumo: "Em produção. As partes aparecem aqui conforme cada agente termina." };
    }
  }
  return null;
}

function json(res, status, corpo) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(corpo));
}

function lerJSON(arq) {
  try { return JSON.parse(fs.readFileSync(arq, "utf-8")); } catch { return null; }
}

function todos() {
  const itens = [];
  for (const tipo of TIPOS) {
    const pasta = path.join(DADOS, tipo);
    if (!fs.existsSync(pasta)) continue;
    for (const f of fs.readdirSync(pasta).filter((x) => x.endsWith(".json"))) {
      const d = lerJSON(path.join(pasta, f));
      if (d) itens.push({ tipo, d, f, mtime: fs.statSync(path.join(pasta, f)).mtime.toISOString() });
    }
  }
  return itens;
}

function listar() {
  return todos().map(({ tipo, d, f, mtime }) => {
    const capa = (d.cortes || []).find((c) => c.arquivo)?.arquivo || (d.slides || [])[0]?.arquivo || null;
    return {
      id: d.id || f.replace(/\.json$/, ""), tipo, origem: d.origem || null,
      titulo: d.nicho || d.titulo || d.cliente || f, criado_em: d.criado_em || mtime, resumo: d.resumo || "",
      capa, formatos: [...new Set((d.roteiros || []).map((r) => r.formato).filter(Boolean))].slice(0, 6),
      contagem: { roteiros: (d.roteiros || []).length, cortes: (d.cortes || []).length, slides: (d.slides || []).length },
    };
  }).sort((a, b) => String(b.criado_em).localeCompare(String(a.criado_em)));
}

function roteiros() {
  const out = [];
  for (const { tipo, d, f } of todos()) {
    (d.roteiros || []).forEach((r, i) => out.push({ ...r, _origem: { tipo, id: d.id || f.replace(/\.json$/, ""), titulo: d.nicho || d.titulo || d.cliente, i, arquivo: `dados/${tipo}/${f}` } }));
  }
  return out;
}

function listarJobs() {
  return fs.readdirSync(JOBS).filter((f) => f.endsWith(".json"))
    .map((f) => lerJSON(path.join(JOBS, f))).filter(Boolean)
    .sort((a, b) => b.inicio.localeCompare(a.inicio)).slice(0, 30);
}


// Traduz o stream-json do Claude em linhas legíveis no log e na "etapa" do job (o Studio mostra ao vivo).
const NOME_AGENTE = { pesquisador: "Pesquisador", estrategista: "Estrategista", roteirista: "Roteirista", copywriter: "Copywriter",
  designer: "Designer", "editor-video": "Editor de vídeo", "gestor-trafego": "Gestor de tráfego", "social-media": "Social media", "produtor-avatar": "Produtor avatar" };
function acompanhar(stdout, log, meta, arqMeta) {
  const agentes = {}; // tool_use_id da delegação -> nome do agente
  let buf = "", ultimaGravacao = 0;
  const escrever = (linha, etapa) => {
    const hora = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    fs.writeSync(log, `[${hora}] ${linha}` + "\n");
    if (etapa) {
      meta.etapa = etapa;
      if (Date.now() - ultimaGravacao > 1500) { ultimaGravacao = Date.now(); fs.writeFileSync(arqMeta, JSON.stringify(meta, null, 2)); }
    }
  };
  const curto = (s, n = 140) => String(s || "").replace(/\s+/g, " ").trim().slice(0, n);
  stdout.on("data", (chunk) => {
    buf += chunk.toString("utf-8");
    let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const linha = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
      if (!linha) continue;
      let ev; try { ev = JSON.parse(linha); } catch { escrever(curto(linha, 300)); continue; }
      const quem = ev.parent_tool_use_id ? (agentes[ev.parent_tool_use_id] || "Agente") : "Diretor";
      if (ev.type === "assistant") {
        for (const c of ev.message?.content || []) {
          if (c.type === "text" && c.text.trim()) escrever(`${quem}: ${curto(c.text, 400)}`);
          if (c.type !== "tool_use") continue;
          const inp = c.input || {};
          if (c.name === "Agent" || c.name === "Task") {
            const nome = NOME_AGENTE[inp.subagent_type] || inp.subagent_type || "agente";
            agentes[c.id] = nome;
            escrever(`→ ${nome}: ${curto(inp.description || inp.prompt, 120)}`, `${nome}: ${curto(inp.description || "trabalhando", 60)}`);
          } else if (c.name === "Bash") {
            const cmd = curto(inp.command, 160);
            const etapa = /perfis\.py/.test(cmd) ? "coletando perfis no Instagram" : /json\.tool/.test(cmd) ? "validando o JSON" : /cortar\.py/.test(cmd) ? "renderizando cortes" : /transcrever\.py/.test(cmd) ? "transcrevendo" : /baixar\.py/.test(cmd) ? "baixando o vídeo" : null;
            escrever(`${quem} $ ${cmd}`, etapa && `${quem}: ${etapa}`);
          } else if (c.name === "WebSearch") escrever(`${quem} busca: ${curto(inp.query)}`, `${quem}: pesquisando na web`);
          else if (c.name === "WebFetch") escrever(`${quem} lendo: ${curto(inp.url)}`, `${quem}: lendo páginas`);
          else if (c.name === "Write" || c.name === "Edit") escrever(`${quem} salvou ${path.relative(RAIZ, inp.file_path || "") || "arquivo"}`, `${quem}: escrevendo`);
          else if (c.name === "Skill") escrever(`${quem} iniciou o fluxo /${inp.skill}`, "planejando");
          else if (c.name === "Read") escrever(`${quem} leu ${path.basename(inp.file_path || "")}`);
          else escrever(`${quem} usou ${c.name}`);
        }
      } else if (ev.type === "user") {
        for (const c of ev.message?.content || []) {
          if (c.type === "tool_result" && agentes[c.tool_use_id]) escrever(`✓ ${agentes[c.tool_use_id]} entregou`, `${agentes[c.tool_use_id]} entregou`);
        }
      } else if (ev.type === "result") {
        const min = ev.duration_ms ? (ev.duration_ms / 60000).toFixed(1) : "?";
        escrever(`${ev.is_error ? "✗ Falhou" : "✓ Concluído"} em ${min} min${ev.total_cost_usd != null ? ` · custo US$ ${ev.total_cost_usd.toFixed(2)}` : ""}`);
        if (ev.result) escrever(curto(ev.result, 1200));
        meta.etapa = ev.is_error ? "falhou" : "pronto";
      }
    }
  });
}

function criarJob(acao, entrada) {
  const montar = FLUXOS[acao];
  if (!montar) throw new Error("ação desconhecida");
  const plano = montar(entrada);
  const id = `${new Date().toISOString().replace(/[:.]/g, "-")}-${acao}`;
  const meta = { id, acao, titulo: plano.titulo, entrega: plano.entrega, origem: plano.origem || null, motor: plano.python ? "python" : "agentes",
    prompt: plano.claude || plano.python.join(" "), inicio: new Date().toISOString(), status: "rodando" };
  const arqMeta = path.join(JOBS, `${id}.json`);
  const arqLog = path.join(JOBS, `${id}.log`);
  fs.writeFileSync(arqMeta, JSON.stringify(meta, null, 2));
  const log = fs.openSync(arqLog, "a");

  let proc;
  const env = { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUNBUFFERED: "1" };
  if (plano.python) {
    proc = spawn(PYTHON, plano.python, { cwd: RAIZ, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true });
    // Etapa ao vivo a partir da saída dos scripts.
    const etapas = [[/== baixar/, "baixando o vídeo"], [/== legenda do YouTube/, "lendo a legenda do YouTube"], [/== mercado/, "vendo o que está em alta no nicho"], [/coletando o mercado|^coletando @/, "coletando perfis do nicho no Instagram"], [/escrevendo \d+ legendas/, "escrevendo as legendas do Instagram"], [/== transcrever|^\[\d\d:\d\d:\d\d/, "transcrevendo"], [/IA escolhendo/, "IA escolhendo os melhores momentos"], [/IA lendo o pedido/, "IA planejando a edição"], [/buscando b-roll/, "buscando imagens e vídeos de apoio"], [/== editando no Remotion|remotion:/, "editando no Remotion (legenda, zoom, gráficos, sons)"], [/== música de fundo/, "colocando a música"],
      [/== cortar|^\[\d\d\]/, "renderizando"], [/^slide \d+/, "renderizando slides"]];
    let ultima = 0;
    const ler = (chunk) => {
      const txt = chunk.toString("utf-8");
      fs.writeSync(log, txt);
      for (const linha of txt.split(/\r?\n/)) {
        const e = etapas.find(([re]) => re.test(linha.trim()));
        if (!e) continue;
        const corte = linha.match(/^\[(\d\d)\]/);
        const transc = linha.match(/^\[(\d\d:\d\d:\d\d)/);
        meta.etapa = corte ? `renderizando corte ${Number(corte[1])}` : transc ? `transcrevendo (${transc[1]} do episódio)` : e[1];
      }
      if (Date.now() - ultima > 1500) { ultima = Date.now(); fs.writeFileSync(arqMeta, JSON.stringify(meta, null, 2)); }
    };
    proc.stdout.on("data", ler); proc.stderr.on("data", ler);
  } else {
    // O prompt vai pelo stdin, nunca pela linha de comando.
    proc = spawn("claude", ["-p", "--permission-mode", "acceptEdits", "--allowedTools", `"${FERRAMENTAS_CLAUDE}"`,
      "--output-format", "stream-json", "--verbose", ...(plano.modelo ? ["--model", plano.modelo] : [])], { cwd: RAIZ, env, shell: process.platform === "win32", stdio: ["pipe", "pipe", log], windowsHide: true });
    proc.stdin.end(plano.claude + RAPIDO);
    acompanhar(proc.stdout, log, meta, arqMeta);
  }
  proc.on("close", (codigo) => {
    meta.status = codigo === 0 ? "concluido" : "erro";
    // Nunca dizer "pronto" sem a entrega existir de verdade.
    if (meta.status === "concluido" && meta.entrega && !fs.existsSync(path.join(DADOS, meta.entrega.tipo, `${meta.entrega.id}.json`))) {
      meta.status = "erro"; meta.etapa = "terminou sem gerar a entrega (veja o log)";
      try { fs.writeSync(log, "\n✗ O processo terminou, mas a entrega não foi gerada.\n"); } catch {}
    }
    if (meta.motor === "python" && meta.status === "concluido") meta.etapa = "pronto";
    if (meta.motor === "python" && codigo !== 0) meta.etapa = "falhou (veja o log)";
    meta.fim = new Date().toISOString();
    fs.writeFileSync(arqMeta, JSON.stringify(meta, null, 2));
    try { fs.closeSync(log); } catch {}
  });
  proc.on("error", (e) => fs.appendFileSync(arqLog, `\nFalha ao iniciar: ${e.message}\n`));
  return meta;
}

function arquivoSeguro(base, rel) {
  const alvo = path.resolve(base, rel);
  return alvo.startsWith(base + path.sep) ? alvo : null;
}

function servirArquivo(req, res, arq) {
  if (!arq || !fs.existsSync(arq) || !fs.statSync(arq).isFile()) { res.writeHead(404); return res.end("não encontrado"); }
  const tipo = MIME[path.extname(arq).toLowerCase()] || "application/octet-stream";
  const st = fs.statSync(arq);
  const tamanho = st.size;
  // Vídeo re-renderizado mantém o nome (01.mp4): o navegador revalida pela data e nunca mostra a versão antiga.
  const versao = { "Cache-Control": "no-cache", "Last-Modified": st.mtime.toUTCString(), "ETag": `"${tamanho}-${st.mtimeMs}"` };
  const range = req.headers.range;
  if (range) {
    const [i, f] = range.replace("bytes=", "").split("-");
    const ini = parseInt(i, 10);
    const fim = f ? parseInt(f, 10) : tamanho - 1;
    res.writeHead(206, { "Content-Range": `bytes ${ini}-${fim}/${tamanho}`, "Accept-Ranges": "bytes",
      "Content-Length": fim - ini + 1, "Content-Type": tipo, ...versao });
    return fs.createReadStream(arq, { start: ini, end: fim }).pipe(res);
  }
  // HTML/JS/JSON sem cache: o Studio muda o tempo todo e o navegador não pode mostrar versão antiga.
  const semCache = /\.(html|js|json|css)$/i.test(arq) ? { "Cache-Control": "no-store, must-revalidate" } : {};
  res.writeHead(200, { "Content-Type": tipo, "Content-Length": tamanho, "Accept-Ranges": "bytes", ...versao, ...semCache });
  fs.createReadStream(arq).pipe(res);
}

function corpo(req) {
  return new Promise((ok, falha) => {
    let s = "";
    req.on("data", (c) => { s += c; if (s.length > 1e6) req.destroy(); });
    req.on("end", () => { try { ok(JSON.parse(s || "{}")); } catch (e) { falha(e); } });
  });
}

function receberUpload(req, res, nome) {
  const ext = path.extname(nome || "").toLowerCase();
  if (![".mp4", ".mov", ".mkv", ".webm", ".m4a", ".mp3", ".wav"].includes(ext)) return json(res, 400, { erro: "Formato não aceito." });
  const destino = path.join(UPLOADS, `${Date.now()}-${slug(path.parse(nome).name)}${ext}`);
  const out = fs.createWriteStream(destino);
  req.pipe(out);
  out.on("finish", () => json(res, 200, { caminho: destino, nome }));
  out.on("error", (e) => json(res, 500, { erro: e.message }));
}

const perfisApi = require("./perfis")({ RAIZ, DADOS, json, lerJSON, corpo, slug, criarJob });

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = decodeURIComponent(url.pathname);
  try {
    if (p === "/api/itens") return json(res, 200, listar());
    if (p === "/api/roteiros") return json(res, 200, roteiros());
    if (p.startsWith("/api/item/")) {
      const [, , , tipo, id] = p.split("/");
      if (!TIPOS.includes(tipo)) return json(res, 404, {});
      const arq = arquivoSeguro(path.join(DADOS, tipo), `${id}.json`);
      const d = (arq && lerJSON(arq)) || (/^[a-z0-9-]+$/.test(id) ? esqueleto(tipo, id) : null);
      if (d) enriquecer(d, id);
      return d ? json(res, 200, d) : json(res, 404, {});
    }
    if (p.startsWith("/api/perfis")) return perfisApi(req, res, p);
    if (p === "/api/clientes") {
      const pasta = path.join(RAIZ, "clientes");
      return json(res, 200, fs.existsSync(pasta) ? fs.readdirSync(pasta, { withFileTypes: true })
        .filter((d) => d.isDirectory() && !d.name.startsWith("_")).map((d) => d.name) : []);
    }
    if (p === "/api/musicas" && req.method === "GET") return json(res, 200, listarMusicas());
    if (p === "/api/musicas" && req.method === "POST") {
      const nome = url.searchParams.get("nome") || "";
      const ext = path.extname(nome).toLowerCase();
      if (!EXT_MUSICA.includes(ext)) return json(res, 400, { erro: "Envie MP3, M4A, WAV, AAC ou OGG." });
      fs.mkdirSync(MUSICAS, { recursive: true });
      const final = `${slug(path.parse(nome).name)}${ext}`;
      const out = fs.createWriteStream(path.join(MUSICAS, final));
      req.pipe(out);
      out.on("finish", () => json(res, 200, { nome: final }));
      out.on("error", (er) => json(res, 500, { erro: er.message }));
      return;
    }
    if (p === "/api/upload" && req.method === "POST") return receberUpload(req, res, url.searchParams.get("nome"));
    if (p === "/api/jobs" && req.method === "GET") return json(res, 200, listarJobs());
    if (p === "/api/jobs" && req.method === "POST") {
      const b = await corpo(req);
      try { return json(res, 200, criarJob(b.acao, b.entrada || {})); } catch (e) { return json(res, 400, { erro: e.message }); }
    }
    if (p.startsWith("/api/jobs/") && p.endsWith("/log")) {
      const id = p.split("/")[3];
      const arq = arquivoSeguro(JOBS, `${id}.log`);
      res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
      return res.end(arq && fs.existsSync(arq) ? fs.readFileSync(arq, "utf-8").slice(-20000) : "");
    }
    if (p === "/api/agentes") {
      const pasta = path.join(RAIZ, ".claude", "agents");
      const ag = fs.readdirSync(pasta).filter((f) => f.endsWith(".md")).map((f) => {
        const t = fs.readFileSync(path.join(pasta, f), "utf-8");
        const nome = ((t.match(/^name:\s*(.+)$/m) || [])[1] || f).trim();
        const desc = ((t.match(/^description:\s*(.+)$/m) || [])[1] || "").trim();
        const pastaC = path.join(RAIZ, "conhecimento", nome);
        const apr = path.join(pastaC, "aprendizados.md");
        const regras = fs.existsSync(apr) ? (fs.readFileSync(apr, "utf-8").match(/^- \d{4}/gm) || []).length : 0;
        const arquivos = fs.existsSync(pastaC) ? fs.readdirSync(pastaC).filter((x) => x.endsWith(".md")) : [];
        return { nome, descricao: desc, aprendizados: regras, arquivos };
      });
      return json(res, 200, ag);
    }
    if (p.startsWith("/midia/")) return servirArquivo(req, res, arquivoSeguro(path.join(RAIZ, "midia"), p.slice(7)));
    const estatico = p === "/" ? "index.html" : p.slice(1);
    return servirArquivo(req, res, arquivoSeguro(PUBLIC, estatico));
  } catch (e) {
    return json(res, 500, { erro: e.message });
  }
}).listen(PORTA, "127.0.0.1", () => console.log(`Studio Zero1 em http://localhost:${PORTA}`));
