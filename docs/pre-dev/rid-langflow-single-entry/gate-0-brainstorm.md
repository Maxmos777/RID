# Brainstorm Ring — `rid-langflow-single-entry` (adequação no RID)

**Facilitação:** dinâmica alinhada à biblioteca **Ring** em `/home/RID/ring` (ver `README.md` local, secção *Specialized Agents*): **Developer Agents (dev-team)** e **Product Research Agents (ring-pm-team)**.

**Artefacto em avaliação:** `RockItDown/docs/pre-dev/rid-langflow-single-entry/gate-0-research.md` (Gate 0, repositório RockItDown; alvo de implementação: **RID**).

**Formato:** transcrição sintética de rodadas (saídas orquestradas via agentes `ring:devops-engineer`, `ring:frontend-engineer`, `ring:product-designer`).

---

## Rodada 0 — Enquadramento (PM / pesquisa)

**Product Research (síntese do `gate-0-research.md`):**  
A proposta do Gate 0 é clara: o problema não é a bridge `auto-login`, é a **topologia** — RID publica Langflow em `7861:7860`, criando uma segunda entrada. Alinhar ao RockItDown significa **fechar o atalho de rede** e, se necessário, **proxy ou embed** no mesmo domínio com validação de sessão. A pesquisa já lista nginx `auth_request`, Traefik `forwardAuth`, CORS, WebSockets e a tensão Django 6 / FastAPI para “mesma sessão”.

**Pergunta para a mesa:** isto é aceite como **épico de plataforma** (infra + frontend + contrato Langflow), não como “pequeno ajuste na bridge”?

---

## Rodada 1 — Dev Team (engenharia)

### DevOps (`ring:devops-engineer`)

- **Compose / produção:** remover mapeamento público `7861:7860` em staging/prod; Langflow só na rede interna; `LANGFLOW_BASE_URL` aponta para hostname interno; na borda, **um** host/path com `auth_request` ou `forwardAuth` antes do upstream Langflow; rever `LANGFLOW_CORS_*` e possível **BASENAME / rebuild** da UI Langflow se houver subpath.
- **WebSockets:** `Upgrade` / `Connection`, timeouts; se houver réplicas, **sticky sessions** ou um backend Langflow até o modelo WS estar claro.
- **TLS / headers:** terminar TLS no edge; `X-Forwarded-Proto`, `Host`, `X-Forwarded-Prefix`; alinhar Django (`SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_*`) e comportamento do Langflow atrás do proxy.
- **MVP:** rede interna + sem porta pública + gate no proxy + ajuste mínimo de URLs/CORS; manter a bridge para credenciais **depois** de fechado o atalho `:7861`.
- **Endurecimento:** paridade estilo RockItDown (SPA no mesmo domínio), políticas por tenant, observabilidade, critério explícito “zero porta Langflow no host”.
- **`auth_check`:** preferir endpoint leve no **Django** (sessão + tenant já lá) com **200/401/403** para o proxy; evitar duplicar validação de sessão no FastAPI salvo delegação fina — reduz risco async/sync entre duas stacks.

### Frontend (`ring:frontend-engineer`)

- **CORS / fetch:** `useLangflowAuth` com `credentials: "include"` mantém-se same-origin com o backend RID; com proxy por prefixo, o bundle Langflow deixa de depender de `:7861` como origem separada — CORS move-se para **proxy ↔ Langflow interno**.
- **`langflow_base_url` (ex. `@rid/shared` / `AppConfig`):** passa a ser URL **pública no mesmo host** (ex. `/flows/` ou `https://app/.../flows/`), não `http://host:7861`; Vite proxy em dev deve espelhar produção.
- **Deep links / router Langflow:** alinhar `basename` / `PUBLIC_URL` ao prefixo; refresh e partilha de URL em `/flows/...` exigem contrato explícito com o shell RID (uma app na barra de URL vs iframe).
- **WebSockets:** eliminar `ws://…:7861`; usar `wss` + mesmo host + subpath com upgrade no proxy; preferir derivar de `window.location` pós-deploy unificado.
- **Bridge vs UI:** a bridge continua fonte de token/API key em memória; pode ser necessária **segunda fase** (injeção na carga inicial do Langflow) — contrato entre shell RID e SPA Langflow.
- **Trade-off proxy-only vs SPA Django (RockItDown):** proxy-only = menos mudanças no Django, mais disciplina em `base`/`assetPrefix` em **dois** builds; SPA Django = `LoginRequiredMixin` + estáticos, mais pipeline collectstatic e clareza entre painel RID e `/flows/*`.

---

## Rodada 2 — PM Team (produto / PRD)

### Product Designer (`ring:product-designer`, lente ux-research / PRD)

**Priorização das perguntas abertas do `gate-0-research.md`:**

1. **Primeiro — “Zero porta Langflow no host” (antiga Q3):** fixa o **perímetro** e risco (auditoria, compliance) antes de debater *como* entregar a UI.  
2. **Segundo — Proxy + rede interna vs SPA Django (antiga Q1):** define escopo, custo de build/deploy e paridade; desbloqueia roadmap e donos.  
3. **Terceiro — WebSockets: mesmo path vs serviço separado (antiga Q2):** detalhe dependente da topologia já escolhida.

**Novas perguntas para stakeholders:**

- **Operação / SLO:** dono de uptime do caminho Langflow atrás do gate; comportamento esperado quando o upstream falhar (mensagem, retry, fallback).  
- **Multi-tenant:** um path/host com isolamento por credenciais/RBAC basta, ou há requisito de **separação explícita por tenant** (path, hostname, rede).

**Definition of done (resumo):**

- **Administradoras enterprise:** política formal de **sem** exposição pública da UI Langflow fora do perímetro RID; gate alinhado ao IdP; trilhos de auditoria mostram acesso só pela entrada única acordada.  
- **Builders:** **uma URL** da app para o Langflow; refresh, deep links e WS no **mesmo host**; fim da confusão com `:7861` (bloqueio ou redirect documentado); sessão RID previsível.

---

## Rodada 3 — Convergência (mesa mista)

| Tema | Consenso emergente |
|------|-------------------|
| **Adequação da pesquisa ao RID** | **Alta:** o `gate-0-research.md` identifica corretamente lacuna (porta + origem) vs RockItDown; implementação é **majoritariamente infra + URL contract + possível rebuild Langflow**, não só API. |
| **Caminho mínimo viável** | **Proxy + rede interna + `auth_check` no Django** + ajuste de `LANGFLOW_BASE_URL` / frontend / CORS; bridge mantida. |
| **Paridade RockItDown completa** | **Opcional / fase 2:** SPA servida pelo Django se o produto quiser o mesmo padrão operacional do RockItDown (mais trabalho de build). |
| **Próximo artefacto Ring** | **Gate 1 (PRD)** com decisão explícita nas perguntas Q3→Q1→Q2 e respostas às duas perguntas novas de stakeholders; depois **TRD** com diagrama de rede e matriz de rotas (HTTP + WS). |

---

## Referências Ring (plugins)

- **dev-team:** `ring:devops-engineer`, `ring:frontend-engineer` (e outros em `/home/RID/ring/README.md` § Developer Agents).  
- **ring-pm-team:** `ring:product-designer`, `ring:repo-research-analyst`, etc. (§ Product Research Agents).  
- **Brainstorming estruturado:** skill `ring:brainstorming` (fases Understanding → Exploration → Design) pode seguir este documento como input da **Fase 1**.

---

*Documento gerado a partir de brainstorm orquestrado com agentes Ring; revisão humana recomendada antes de compromissos de roadmap.*
