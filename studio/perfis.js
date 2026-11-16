// Perfis (contas da marca) e professores: cadastro, pesquisa por especialidade e chat por professor.
// Dados:   dados/perfis/<perfil>.json              (perfil + lista de professores, o Studio lê daqui)
//          dados/perfis/<perfil>/chats/<prof>.json  (histórico + sessão do Claude)
// Memória: clientes/<perfil>/professores/<prof>.md  (o que os agentes leem; o chat acrescenta aprendizados)
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

module.exports = function criarPerfisApi({ RAIZ, DADOS, json, lerJSON, corpo, slug, criarJob }) {
  const PERFIS = path.join(DADOS, "perfis");
  fs.mkdirSync(PERFIS, { recursive: true });
  const valido = (s) => /^[a-z0-9-]{1,60}$/.test(s || "");
  const arqPerfil = (id) => path.join(PERFIS, `${id}.json`);
  const arqChat = (id, prof) => path.join(PERFIS, id, "chats", `${prof}.json`);
  const arqMemoria = (id, prof) => path.join(RAIZ, "clientes", id, "professores", `${prof}.md`);
  const salvar = (arq, d) => { fs.mkdirSync(path.dirname(arq), { recursive: true }); fs.writeFileSync(arq, JSON.stringify(d, null, 2)); };
  const agora = () => new Date().toISOString();
  const lista = (v) => (Array.isArray(v) ? v : String(v || "").split(/[,;\n]/)).map((x) => String(x).trim()).filter(Boolean);

  function memoriaInicial(perfil, p) {
    return `# ${p.nome} · ${p.especialidade}\n\nPerfil: ${perfil.nome} (${perfil.instagram || "sem @"})\n\n` +
      `## Quem é\n${p.bio || "(a preencher)"}\n\n## Público\n${p.publico || "(a preencher)"}\n\n## Tom de voz\n${p.tom_de_voz || "(a preencher)"}\n\n` +
      `## Temas que domina\n${lista(p.temas).map((t) => `- ${t}`).join("\n") || "(a preencher)"}\n\n## Evitar\n${lista(p.evitar).map((t) => `- ${t}`).join("\n") || "(nada ainda)"}\n\n` +
      `## Clone (HeyGen / ElevenLabs)\n- avatar_id: ${p.heygen?.avatar_id || "pendente"}\n- voice_id: ${p.heygen?.voice_id || "pendente"}\n- consentimento registrado: ${p.heygen?.consentimento ? "sim" : "não"}\n\n` +
      `## Aprendizados (o chat acrescenta aqui; prevalecem sobre o resto)\n`;
  }

  function contexto(perfil, p) {
    const mem = fs.existsSync(arqMemoria(perfil.id, p.id)) ? fs.readFileSync(arqMemoria(perfil.id, p.id), "utf-8") : "";
    let pesquisa = "";
    const d = p.pesquisa_id && lerJSON(path.join(DADOS, "pesquisas", `${p.pesquisa_id}.json`));
    if (d) {
      const top = (d.posts_referencia || []).slice().sort((a, b) => (b.outlier_score || 0) - (a.outlier_score || 0)).slice(0, 12);
      pesquisa = `\n\nPESQUISA DE MERCADO DA ÁREA (dados reais do Instagram, ${d.id}):\n${d.resumo || ""}\n` +
        `Padrões: ${(d.padroes || []).map((x) => `${x.titulo}: ${x.descricao}`).join(" | ")}\n` +
        `Formatos: ${(d.formatos || []).map((x) => `${x.formato} (${x.por_que_funciona || ""})`).join(" | ")}\n` +
        `Posts em alta:\n${top.map((x) => `- ${x.perfil}: "${x.gancho || ""}" (${x.outlier_score || "?"}x a média, ${x.views || "?"} views) ${x.url}`).join("\n")}`;
    }
    // Roteiros e estratégias já feitos para o professor: o chat conhece e não repete.
    let feitos = "";
    for (const e of p.entregas || []) {
      const x = lerJSON(path.join(DADOS, e.tipo, `${e.id}.json`));
      if (!x) continue;
      const pil = (x.estrategia?.pilares || []).map((y) => (typeof y === "string" ? y : y.nome)).filter(Boolean);
      feitos += `\n- ${e.id}${pil.length ? ` (pilares: ${pil.join(", ")})` : ""}: ${(x.roteiros || []).map((r) => `"${r.titulo}"`).join("; ")}`;
    }
    if (feitos) feitos = `\n\nROTEIROS JÁ ENTREGUES PARA ESTE PROFESSOR (não repita temas; continue a série):${feitos}`;
    return `Você é o assistente de conteúdo exclusivo de ${p.nome}, professor(a) de ${p.especialidade} do perfil ${perfil.nome} (${perfil.instagram || ""}) na Agência Zero1.
Fale direto com ${p.nome.split(" ")[0]}, em português do Brasil, sem jargão de IA, sem "não é X, é Y", sem travessão em excesso.
Sua função: ideias de conteúdo, roteiros de Reels/TikTok (com formato explícito, gancho nos 3 primeiros segundos, cenas, texto na tela e CTA), carrosséis, legendas e estratégia, sempre na especialidade e no jeito desse professor.
Os roteiros serão gravados pelo professor ou pelo clone dele no HeyGen; escreva falas que soem como ele.
Nunca invente números, estudos ou dados clínicos: se precisar de um dado, marque [DADO A CONFIRMAR]. Siga as regras de compliance médico (CFM) quando o tema for saúde.
APRENDA: quando o professor disser preferências, correções, o que gostou ou não, ou fatos sobre ele, registre na hora uma linha em "## Aprendizados" do arquivo ${path.relative(RAIZ, arqMemoria(perfil.id, p.id)).split(path.sep).join("/")} (formato: "- AAAA-MM-DD regra (motivo)") usando a ferramenta Edit, e avise em 1 linha que guardou.
Regras da agência para roteiros: leia conhecimento/roteirista/playbook.md se precisar.

VOCÊ EXECUTA, não só sugere. Quando o usuário pedir algo para este professor, faça e salve, sem pedir confirmação para o que é barato:
- Roteiros / série / estratégia: salve em dados/campanhas/<AAAA-MM-DD-slug>.json (schema de campanha do CLAUDE.md; roteiros no schema Roteiro, com formato e gancho) e registre na área do professor:
  python ferramentas/heygen/registrar.py entrega ${perfil.id} ${p.id} --tipo campanhas --id <id> --titulo "<título>"
  Valide antes com python -m json.tool. O Studio mostra os roteiros na tela do professor.
- Pesquisa de mercado: use o agente pesquisador (ferramenta Agent, subagent_type pesquisador) com briefing completo, sem transcrever vídeos (rápido).
- Vídeo com o clone no HeyGen (MCP heygen): ${p.heygen?.avatar_id ? `look padrão ${p.heygen.avatar_id}${(p.heygen.looks || []).length ? `; outros looks: ${(p.heygen.looks || []).map((l) => `${l.nome} = ${l.id}`).join(", ")}` : ""}; voz ${p.heygen.voice_id}` : "este professor ainda não tem clone: avise e não gere"}.
  Use create_video_from_avatar com o texto exato das falas, aspectRatio 9:16, voiceId do professor. Look de foto (photo_avatar) usa engine {"type":"avatar_v","reference_look_id":"${p.heygen?.avatar_id || ""}"} para herdar o movimento do vídeo original.
  Custo: vídeo gasta créditos. Gere 1 vídeo por pedido, com no máximo 60s, salvo se o usuário pedir mais. Antes de gerar, confira o texto (sem [DADO A CONFIRMAR] pendente).
  Logo depois de criar: python ferramentas/heygen/registrar.py video ${perfil.id} ${p.id} --video-id <id> --titulo "<título>" --look <look>
  Acompanhe com get_video a cada 30s (espere com: python -c "import time;time.sleep(30)") por até 8 min. Quando pronto: registrar.py video ... --video-id <id> --url <video_url> (baixa o mp4). Se falhar: --status falhou.
- Trocar roupa/cor do clone: create_image (nano-banana-2.1) editando a imagem de preview do look, mudando só a roupa; depois create_photo_avatar no mesmo grupo (${p.heygen?.avatar_group_id || "grupo do professor"}). Mostre a imagem ao usuário antes de gerar vídeo com ela.
- Ferramentas locais da agência: veja a seção "Ferramentas locais" do CLAUDE.md.
Leia arquivos com a ferramenta Read (nunca com cat/type no terminal, que corrompe acentos). O texto mandado ao HeyGen precisa ter os acentos certos.
Responda curto: o que fez, onde ficou e o próximo passo.

PERFIL DO PROFESSOR (memória; Aprendizados prevalecem):
${mem}${pesquisa}${feitos}`;
  }

  function lerPerfil(id) {
    const d = valido(id) && lerJSON(arqPerfil(id));
    if (!d) return null;
    d.professores = d.professores || [];
    return d;
  }

  async function rota(req, res, p) {
    const partes = p.split("/").filter(Boolean); // api perfis :id professores :prof [pesquisa]
    if (partes[1] === "perfis") {
      if (partes.length === 2 && req.method === "GET") {
        const itens = fs.readdirSync(PERFIS).filter((f) => f.endsWith(".json")).map((f) => lerJSON(path.join(PERFIS, f))).filter(Boolean)
          .map((d) => ({ id: d.id, nome: d.nome, instagram: d.instagram, seguidores: d.seguidores, descricao: d.descricao, professores: (d.professores || []).length }));
        return json(res, 200, itens.sort((a, b) => (b.professores - a.professores) || (b.seguidores || 0) - (a.seguidores || 0)));
      }
      const perfil = lerPerfil(partes[2]);
      if (!perfil) return json(res, 404, { erro: "Perfil não encontrado." });
      if (partes.length === 3 && req.method === "GET") {
        for (const prof of perfil.professores) {
          const ch = lerJSON(arqChat(perfil.id, prof.id));
          prof.mensagens = ch ? ch.mensagens.length : 0;
          const mem = arqMemoria(perfil.id, prof.id);
          prof.aprendizados = fs.existsSync(mem) ? (fs.readFileSync(mem, "utf-8").split("## Aprendizados")[1] || "").split("\n").filter((l) => /^- \d{4}/.test(l)).length : 0;
        }
        return json(res, 200, perfil);
      }
      if (partes.length === 3 && req.method === "POST") { // editar dados do perfil
        const b = await corpo(req);
        Object.assign(perfil, { descricao: b.descricao ?? perfil.descricao, publico: b.publico ?? perfil.publico });
        salvar(arqPerfil(perfil.id), perfil);
        return json(res, 200, perfil);
      }
      if (partes[3] === "professores" && req.method === "POST" && partes.length <= 5) {
        const b = await corpo(req);
        if (!b.nome || !b.especialidade) return json(res, 400, { erro: "Informe nome e especialidade." });
        let prof = partes[4] ? perfil.professores.find((x) => x.id === partes[4]) : null;
        const novo = !prof;
        if (novo) {
          let id = slug(b.nome), k = 2;
          while (perfil.professores.some((x) => x.id === id)) id = `${slug(b.nome)}-${k++}`;
          prof = { id, criado_em: agora(), pesquisa_id: null };
          perfil.professores.push(prof);
        }
        Object.assign(prof, {
          nome: b.nome.trim(), especialidade: b.especialidade.trim(), instagram: (b.instagram || "").trim(),
          bio: b.bio || "", publico: b.publico || "", tom_de_voz: b.tom_de_voz || "", temas: lista(b.temas), evitar: lista(b.evitar),
          heygen: { ...(prof.heygen || {}), avatar_id: (b.avatar_id || prof.heygen?.avatar_id || "").trim() || null, voice_id: (b.voice_id || prof.heygen?.voice_id || "").trim() || null,
            consentimento: !!(b.consentimento ?? prof.heygen?.consentimento) },
        });
        salvar(arqPerfil(perfil.id), perfil);
        const mem = arqMemoria(perfil.id, prof.id);
        if (!fs.existsSync(mem)) { fs.mkdirSync(path.dirname(mem), { recursive: true }); fs.writeFileSync(mem, memoriaInicial(perfil, prof)); }
        else { // atualiza a parte de cima e preserva os aprendizados
          const aprend = fs.readFileSync(mem, "utf-8").split("## Aprendizados")[1] || "";
          fs.writeFileSync(mem, memoriaInicial(perfil, prof).replace(/## Aprendizados[\s\S]*$/, "## Aprendizados" + (aprend || " (o chat acrescenta aqui; prevalecem sobre o resto)\n")));
        }
        return json(res, 200, prof);
      }
      const prof = perfil.professores.find((x) => x.id === partes[4]);
      if (!prof) return json(res, 404, { erro: "Professor não encontrado." });
      if (partes[5] === "pesquisa" && req.method === "POST") {
        const b = await corpo(req);
        const nicho = `${prof.especialidade}${b.foco ? ` (${b.foco})` : ""}`;
        const job = criarJob("pesquisa", { nicho, cliente: perfil.id, redes: ["instagram"], roteiros: b.roteiros || 6,
          perfis: [prof.instagram, ...(lista(b.perfis))].filter(Boolean).join(" "),
          contexto: `Pesquisa detalhada para ${prof.nome}, professor(a) de ${prof.especialidade} do ${perfil.nome}. Público do perfil: ${perfil.publico || perfil.descricao || "estudantes de medicina"}. Roteiros no tom do professor (veja ${path.relative(RAIZ, arqMemoria(perfil.id, prof.id)).split(path.sep).join("/")}).` });
        prof.pesquisa_id = job.entrega.id;
        salvar(arqPerfil(perfil.id), perfil);
        return json(res, 200, job);
      }
      if (partes[5] === "memoria" && req.method === "GET") {
        const mem = arqMemoria(perfil.id, prof.id);
        res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
        return res.end(fs.existsSync(mem) ? fs.readFileSync(mem, "utf-8") : "");
      }
      if (partes[5] === "videos" && req.method === "GET") return json(res, 200, lerJSON(path.join(PERFIS, perfil.id, "videos", `${prof.id}.json`)) || []);
      if (partes[5] === "chat" && req.method === "GET") return json(res, 200, lerJSON(arqChat(perfil.id, prof.id)) || { mensagens: [] });
      if (partes[5] === "chat" && req.method === "DELETE") { const a = arqChat(perfil.id, prof.id); if (fs.existsSync(a)) fs.unlinkSync(a); return json(res, 200, { ok: true }); }
      if (partes[5] === "chat" && req.method === "POST") return conversar(req, res, perfil, prof);
    }
    return json(res, 404, {});
  }

  // Chat: uma sessão do Claude por professor (--resume mantém a conversa); resposta em streaming (SSE).
  async function conversar(req, res, perfil, prof) {
    const b = await corpo(req);
    const msg = String(b.mensagem || "").trim();
    if (!msg) return json(res, 400, { erro: "Mensagem vazia." });
    const arq = arqChat(perfil.id, prof.id);
    const chat = lerJSON(arq) || { sessao: null, mensagens: [] };
    chat.mensagens.push({ papel: "professor", texto: msg, em: agora() });
    salvar(arq, chat);

    const memRel = path.relative(RAIZ, arqMemoria(perfil.id, prof.id)).split(path.sep).join("/");
    // O chat executa: salva roteiros, chama o pesquisador, gera vídeo no HeyGen e roda as ferramentas da agência.
    const ferramentas = ["Read", "Glob", "Grep", "Edit", "Write", "Agent", "WebSearch", "WebFetch",
      "Bash(python:*)", "Bash(ffmpeg:*)", "Bash(ffprobe:*)", "Bash(mkdir:*)", "Bash(ls:*)", "PowerShell(python:*)", "PowerShell(python *)", "mcp__heygen"].join(" ");
    const args = ["-p", "--model", "sonnet", "--permission-mode", "acceptEdits", "--output-format", "stream-json", "--verbose", "--include-partial-messages",
      "--allowedTools", `"${ferramentas}"`];
    if (chat.sessao) args.push("--resume", chat.sessao);
    // O contexto do professor vai na primeira mensagem (pelo stdin, sem limite de tamanho); a sessão guarda dali em diante.
    // Conversas antigas (de antes do modo executor) recebem o contexto novo uma vez.
    const entrada = chat.sessao && chat.modo === "executor" ? msg : `${contexto(perfil, prof)}\n\n---\n${chat.sessao ? "Contexto atualizado (agora você executa). Mensagem" : "Primeira mensagem"} do usuário:\n${msg}`;
    chat.modo = "executor";

    res.writeHead(200, { "Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache", Connection: "keep-alive" });
    const enviar = (ev, dados) => res.write(`event: ${ev}\ndata: ${JSON.stringify(dados)}\n\n`);
    const proc = spawn("claude", args, { cwd: RAIZ, shell: process.platform === "win32", windowsHide: true, env: { ...process.env, PYTHONUTF8: "1", PYTHONIOENCODING: "utf-8" } });
    proc.stdin.end(entrada);
    let buf = "", texto = "", parcial = false;
    proc.stdout.on("data", (chunk) => {
      buf += chunk.toString("utf-8");
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const linha = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
        if (!linha) continue;
        let ev; try { ev = JSON.parse(linha); } catch { continue; }
        if (ev.session_id && !chat.sessao) chat.sessao = ev.session_id;
        if (ev.type === "stream_event" && ev.event?.type === "content_block_delta" && ev.event.delta?.type === "text_delta" && !ev.parent_tool_use_id) {
          parcial = true; texto += ev.event.delta.text; enviar("delta", { texto: ev.event.delta.text });
        } else if (ev.type === "stream_event" && ev.event?.type === "message_start" && texto && !texto.endsWith("\n\n")) {
          texto += "\n\n"; enviar("delta", { texto: "\n\n" });
        } else if (ev.type === "assistant") {
          for (const c of ev.message?.content || []) {
            if (c.type === "tool_use") enviar("ferramenta", { nome: c.name, alvo: c.input?.file_path ? path.basename(c.input.file_path) : "", cmd: String(c.input?.command || c.input?.description || "").slice(0, 160) });
            if (c.type === "text" && !parcial) { texto += c.text; enviar("delta", { texto: c.text }); }
          }
        } else if (ev.type === "result") {
          if (ev.session_id) chat.sessao = ev.session_id;
          if (!texto && ev.result) { texto = ev.result; enviar("delta", { texto }); }
        }
      }
    });
    proc.stderr.on("data", () => {});
    proc.on("close", () => {
      chat.mensagens.push({ papel: "assistente", texto: texto.trim() || "(sem resposta)", em: agora() });
      salvar(arq, chat);
      enviar("fim", { ok: true });
      res.end();
    });
    req.on("close", () => { if (!res.writableEnded) proc.kill(); });
  }

  return rota;
};
