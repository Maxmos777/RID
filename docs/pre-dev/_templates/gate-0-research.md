---
feature: {feature-slug}
gate: 0
date: {date}
research_mode: {research-mode}
# Valores possíveis: integration | greenfield | migration | optimization
agents_dispatched: {number-of-agents}
topology:
  scope: {scope}
  # Valores possíveis: fullstack | backend | frontend | infra
  structure: {structure}
  # Valores possíveis: monorepo | multi-repo
  reference_repo:
    path: {reference-repo-path}
    role: {reference-repo-role}
    # Exemplo: "padrão de referência (implementação existente do padrão alvo)"
  target_repo:
    path: {target-repo-path}
    role: {target-repo-role}
    # Exemplo: "plataforma a alinhar"
  api_pattern: {api-pattern}
  # Valores possíveis: bff | rest | graphql | rpc
---

# Pesquisa Gate 0 — {feature-name}

## Resumo executivo

<!-- 2-4 frases: qual o problema central, o que foi descoberto na pesquisa, e qual a direcção recomendada.
     Exemplo: "O {sistema-a} faz X de forma Y. O {sistema-b} faz X de forma Z. Alinhar os dois implica
     mudar A, B e C — não apenas D." -->

{resumo-executivo}

---

## Modo de pesquisa

**{research-mode}** — {justificativa-do-modo}

<!-- Exemplo para "integration": "ligar dois sistemas com o mesmo modelo de confiança que {referência} já assume" -->

---

## Pesquisa no código (Repo Research Analyst)

### {sistema-referencia} — padrões a replicar

<!-- Tabela com os padrões relevantes encontrados no repositório de referência -->

| Tema | Referência |
|------|------------|
| {tema-1} | `{caminho/ficheiro:linha}` — {descrição} |
| {tema-2} | `{caminho/ficheiro:linha}` — {descrição} |
| {tema-3} | `{caminho/ficheiro:linha}` — {descrição} |

### {sistema-alvo} — estado actual

<!-- Tabela com o estado actual no repositório alvo -->

| Tema | Referência |
|------|------------|
| {tema-1} | `{caminho/ficheiro:linha}` — {descrição} |
| {tema-2} | `{caminho/ficheiro:linha}` — {descrição} |

### Lacuna principal ({sistema-alvo} vs {sistema-referencia})

<!-- Descrever em 2-4 bullets a diferença central entre os dois sistemas no contexto deste feature -->

- {lacuna-1}
- {lacuna-2}
- {lacuna-3}

---

## Boas práticas externas (Best Practices Researcher)

<!-- Tabela com fontes externas relevantes: documentação oficial, RFCs, artigos técnicos -->

| Tema | Fonte |
|------|--------|
| {tema-1} | {url-ou-referencia} |
| {tema-2} | {url-ou-referencia} |
| {tema-3} | {url-ou-referencia} |

---

## Documentação de frameworks (Framework Docs Researcher)

<!-- Versões do stack relevante e apontamentos sobre comportamentos importantes para este feature -->

- **{framework-1}** (`{caminho/ficheiro-de-deps}`): versão {versão} — {nota-relevante}
- **{framework-2}**: versão {versão} — {nota-relevante}
- **{framework-3}**: versão {versão} — {nota-relevante}

---

## Pesquisa de produto / UX (Product Designer, modo ux-research)

- **Problema:** {descrição-do-problema-validado}
- **Personas:** (1) **{persona-1}** — {job-to-be-done}; (2) **{persona-2}** — {job-to-be-done}
- **Padrão de mercado:** {padrão-observado-em-produtos-similares}
- **Restrições de desenho:** {restrições-relevantes-para-o-ux}
- **Métricas sugeridas:** {metricas-propostas}

---

## Síntese (para PRD/TRD)

### Padrões a seguir ({sistema-referencia} + indústria)

<!-- Lista numerada dos padrões e práticas recomendados para este feature -->

1. {padrao-1}
2. {padrao-2}
3. {padrao-3}

### Restrições identificadas

<!-- Restrições técnicas, operacionais ou de produto descobertas na pesquisa -->

- **{restricao-1}:** {descricao}
- **{restricao-2}:** {descricao}

### Perguntas abertas (para PRD)

<!-- Perguntas que a pesquisa não conseguiu responder e que devem ser decididas no Gate 1 -->

1. {pergunta-aberta-1}?
2. {pergunta-aberta-2}?
3. {pergunta-aberta-3}?

---

**Agentes utilizados (ring-pm-team / Gate 0):** {lista-de-agentes-utilizados}

<!-- Exemplo: `ring:repo-research-analyst`, `ring:best-practices-researcher`,
     `ring:framework-docs-researcher`, `ring:product-designer` (ux-research) -->

**Nota multi-repo:** *(remover se monorepo)* {nota-sobre-repositorios-envolvidos}
