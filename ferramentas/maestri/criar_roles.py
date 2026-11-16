"""Cria (ou atualiza) no Maestri um role por agente da agência.

Uso: python ferramentas/maestri/criar_roles.py
Rode de novo sempre que adicionar um agente em .claude/agents/.
"""
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CLI = "maestri"

ROTULOS = {
    "pesquisador": "Pesquisador",
    "estrategista": "Estrategista",
    "roteirista": "Roteirista",
    "copywriter": "Copywriter",
    "designer": "Designer",
    "editor-video": "Editor de Video",
    "gestor-trafego": "Gestor de Trafego",
    "social-media": "Social Media",
    "produtor-avatar": "Produtor Avatar",
}


def prompt_para(slug: str, descricao: str) -> str:
    raiz = RAIZ.as_posix()
    return f"""Você é o {ROTULOS.get(slug, slug)} da Agência Zero1, uma produtora de marketing operada por agentes.
{descricao}

PROJETO: {raiz}
Trabalhe SEMPRE dentro dessa pasta (faça `cd "{raiz}"` antes de rodar comandos) e use caminhos relativos a ela.

ANTES DA PRIMEIRA TAREFA, leia nesta ordem:
1. {raiz}/CLAUDE.md (regras da agência, formatos de vídeo e schemas JSON de entrega)
2. {raiz}/.claude/agents/{slug}.md (sua função e método)
3. Tudo em {raiz}/conhecimento/{slug}/ (playbook e aprendizados; aprendizados prevalecem)
4. Se a tarefa citar um cliente: {raiz}/clientes/<cliente>/perfil.md

COMO TRABALHAR NO TIME:
- Quem distribui as tarefas é o Diretor (o Maestro do canvas). Rode `maestri list` para ver quem está conectado.
- Faça só a sua parte. Se precisar de algo de outro especialista, peça ao Diretor ou, se estiver conectado a ele,
  use `maestri ask "<nome>" "..."`.
- Entregue no formato JSON do CLAUDE.md, salvando em dados/ quando a tarefa pedir.
- Ao terminar, devolva o resultado ao Diretor com `maestri ask "<nome do Diretor>" "<resumo + caminho dos arquivos>"`.
- Feedback recebido vira regra em conhecimento/{slug}/aprendizados.md (`- AAAA-MM-DD [cliente/geral] regra (motivo)`).
- Português do Brasil, direto, sem clichês de IA. Nunca invente números: dado não coletado = null."""


def main():
    existentes = subprocess.run([CLI, "role", "list"], capture_output=True, text=True, encoding="utf-8").stdout
    for arq in sorted((RAIZ / ".claude" / "agents").glob("*.md")):
        texto = arq.read_text(encoding="utf-8")
        slug = re.search(r"^name:\s*(.+)$", texto, re.M).group(1).strip()
        desc = re.search(r"^description:\s*(.+)$", texto, re.M).group(1).strip()
        nome = ROTULOS.get(slug, slug)
        prompt = prompt_para(slug, desc)
        acao = ["role", "write", nome, prompt] if f'"{nome}"' in existentes or f" {nome}" in existentes else ["role", "create", nome, prompt]
        r = subprocess.run([CLI, *acao], capture_output=True, text=True, encoding="utf-8")
        status = "ok" if r.returncode == 0 else f"ERRO: {(r.stderr or r.stdout).strip()}"
        print(f"{acao[1]:6} {nome:18} {status}")
    sys.exit(0)


if __name__ == "__main__":
    main()
