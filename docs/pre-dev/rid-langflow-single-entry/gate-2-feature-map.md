---
feature: rid-langflow-single-entry
gate: 2
date: 2026-04-05
status: draft
prd_ref: docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md
ux_criteria_ref: docs/pre-dev/rid-langflow-single-entry/gate-1.5-ux-criteria.md
topology:
  scope: fullstack
  api_pattern: bff
---

# Feature map — Entrada única autenticada para o editor de fluxos

## Overview

| Campo | Valor |
|-------|-------|
| PRD | `docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md` (Gate 1 — aprovado) |
| UX Criteria | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-ux-criteria.md` |
| Wireframes | `docs/pre-dev/rid-langflow-single-entry/gate-1.5-wireframes/` |
| Status | Draft — Gate 2 |
| Última actualização | 2026-04-05 |

---

## Feature inventory

### Core (MVP — bloqueia tudo o resto)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-001 | Perímetro único de autenticação | Toda entrada no editor exige sessão da plataforma activa; utilizadores não autenticados são redirecionados para login com retorno ao destino original | Garante que nenhum acesso ao editor acontece fora do controlo da plataforma | — | F-002, F-003, F-004, F-005 |
| F-002 | Endereço único e estável | O editor é acessível num único URL dentro do domínio da plataforma; deep links, refresh e partilha de URL funcionam nesse mesmo endereço | Elimina confusão entre dois URLs; partilha de links funciona para qualquer colega autenticado | F-001 | F-005 |
| F-004 | Isolamento por tenant | O acesso ao editor valida o tenant activo da sessão; utilizadores de tenants diferentes não acedem aos fluxos uns dos outros | Garante que dados e fluxos de um cliente enterprise não vazam para outro | F-001 | F-005 |

### Supporting (MVP — habilita ou complementa o core)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-003 | Página de indisponibilidade integrada | Quando o editor está indisponível, o utilizador vê uma página de erro com identidade visual da plataforma, mensagem clara e acções de recuperação (retry / voltar ao painel) | Mantém experiência coerente durante falhas; elimina erros genéricos de proxy | F-001 | — |
| F-005 | Auditoria de acesso ao perímetro | Cada acesso ao editor produz registo associado à sessão da plataforma (tenant, utilizador, timestamp, URL) | Permite a administradoras reportar acessos com completude e exactidão para fins de compliance | F-001, F-002, F-004 | — |

### Enhancement (Fase 2 — pós-MVP)

| ID | Nome | Descrição | Valor para o utilizador | Depende de | Bloqueia |
|----|------|-----------|------------------------|------------|---------|
| F-006 | Paridade de deploy com RockItDown | Editor servido directamente pelo servidor de aplicação da plataforma (sem proxy separado) | Operação simplificada; mesma topologia de referência | F-001, F-002 | — |

---

## Domain groupings

### Domínio 1 — Controlo de acesso

**Propósito:** Garantir que todo acesso ao editor passa pelo perímetro de identidade da plataforma e respeita os limites de tenant.

**Features:** F-001 (perímetro de autenticação), F-004 (isolamento por tenant)

**Owns:**
- Decisão de permitir ou negar acesso ao editor
- Validação de sessão activa da plataforma
- Validação de tenant da sessão vs tenant do recurso solicitado

**Provides para outros domínios:**
- Identidade verificada do utilizador → Domínio de Observabilidade (F-005)
- Garantia de acesso autorizado → Domínio de Experiência de Acesso (F-002, F-003)

**Consumes:**
- Sessão activa da plataforma (gerada pelo sistema de autenticação existente do RID)

**Integration points:**
- ← Sistema de autenticação da plataforma RID (sessão existente)
- ← Sistema de gestão de tenants da plataforma RID (django-tenants)
- → Domínio de Observabilidade: notifica cada acesso autorizado

---

### Domínio 2 — Experiência de acesso

**Propósito:** Garantir que a entrada no editor é previsível, estável e coerente para o utilizador — independentemente do ponto de entrada ou do estado do serviço.

**Features:** F-002 (endereço único e estável), F-003 (página de indisponibilidade integrada)

**Owns:**
- URL canónico do editor dentro do domínio da plataforma
- Comportamento de deep links, refresh e partilha de URL
- Experiência de erro quando o editor está indisponível
- Overlay de sessão expirada durante uso do editor

**Provides para outros domínios:**
- Ponto de entrada estável → usado pelo Domínio de Controlo de Acesso como destino de redirect pós-login

**Consumes:**
- Autorização do Domínio de Controlo de Acesso (só serve conteúdo se acesso autorizado)
- Estado de disponibilidade do editor (para decidir entre servir o editor ou a página de erro)

**Integration points:**
- ← Domínio de Controlo de Acesso: autorização de acesso
- ← Editor de fluxos interno (Langflow): resposta ao pedido de conteúdo
- → Utilizador: URL estável e página de erro branded

---

### Domínio 3 — Observabilidade de negócio

**Propósito:** Tornar os acessos ao editor visíveis e auditáveis dentro do sistema de registos da plataforma.

**Features:** F-005 (auditoria de acesso ao perímetro)

**Owns:**
- Registo de cada acesso autorizado ao editor (tenant, utilizador, timestamp, URL)
- Integração dos registos no sistema de auditoria existente da plataforma

**Provides:**
- Trilhos de auditoria completos → Administradoras de plataforma (persona Ana)

**Consumes:**
- Identidade verificada do utilizador e tenant do Domínio de Controlo de Acesso
- Evento de acesso autorizado (antes de encaminhar para o editor)

**Integration points:**
- ← Domínio de Controlo de Acesso: identidade + tenant do acesso autorizado
- → Sistema de auditoria existente da plataforma RID

---

## User journeys

### Journey 1 — Bruno acede ao editor a partir da plataforma (happy path)

**Utilizador:** Bruno (Builder de fluxos)
**Goal:** Aceder ao editor de fluxos para trabalhar num fluxo específico

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Clica em "Editor de fluxos" no painel ou usa bookmark | F-002 | Experiência de acesso | URL do editor é invocado |
| 2. Pedido chega ao perímetro da plataforma | F-001 | Controlo de acesso | Sessão validada — activa |
| 3. Tenant da sessão validado | F-004 | Controlo de acesso | Tenant correcto — acesso autorizado |
| 4. Acesso registado | F-005 | Observabilidade | Registo de auditoria criado |
| 5. Editor carregado | F-002 | Experiência de acesso | Bruno vê o editor de fluxos |

**Cross-domain interactions:** Controlo de Acesso → Observabilidade → Experiência de Acesso

**Resultado de sucesso:** Bruno acede ao editor sem interrupção.
**Resultado de falha:** Editor indisponível → Journey 4.

---

### Journey 2 — Bruno acede via deep link sem sessão activa (redirect flow)

**Utilizador:** Bruno (ou colega Clara que recebe link partilhado)
**Goal:** Aceder a um fluxo específico partilhado por colega

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Abre deep link para `/flows/<id>` sem sessão | F-001 | Controlo de acesso | Sessão ausente detectada |
| 2. Redirecionado para login com destino preservado | F-001, F-002 | Controlo de acesso | Página de login da plataforma (URL destino preservado) |
| 3. Autentica-se com credenciais | — | Sistema de autenticação existente | Sessão criada |
| 4. Redirecionado para o deep link original | F-002 | Experiência de acesso | Aterra no fluxo específico |
| 5. Pedido validado no perímetro | F-001, F-004 | Controlo de acesso | Sessão válida + tenant correcto |
| 6. Acesso registado | F-005 | Observabilidade | Registo de auditoria criado |
| 7. Editor carregado no fluxo específico | F-002 | Experiência de acesso | Bruno/Clara vê o fluxo destino |

**Cross-domain interactions:** Controlo de Acesso → sistema de auth externo → Controlo de Acesso → Observabilidade → Experiência de Acesso

**Resultado de sucesso:** Utilizador aterra no fluxo específico após login.
**Resultado de falha (credenciais inválidas):** permanece na página de login; URL destino preservado.

---

### Journey 3 — Sessão de Bruno expira durante trabalho no editor

**Utilizador:** Bruno (Builder de fluxos)
**Goal:** Continuar a trabalhar no editor sem perder contexto

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Sessão expira enquanto Bruno trabalha no editor | F-001 | Controlo de acesso | Próximo pedido ao perímetro retorna não autorizado |
| 2. Plataforma detecta sessão inválida | F-002 | Experiência de acesso | Overlay "Sessão expirada" apresentado sobre o editor |
| 3. Bruno clica "Entrar novamente" | F-002 | Experiência de acesso | Redirect para login com retorno a `/flows/` |
| 4. Autentica-se | — | Sistema de autenticação existente | Nova sessão criada |
| 5. Retorna ao editor | F-001, F-004 | Controlo de acesso | Sessão e tenant revalidados |
| 6. Acesso registado | F-005 | Observabilidade | Novo registo de auditoria |
| 7. Editor recarregado | F-002 | Experiência de acesso | Bruno continua o trabalho |

**Resultado de sucesso:** Bruno retorna ao editor após re-autenticação.

---

### Journey 4 — Editor indisponível

**Utilizador:** Bruno ou Ana
**Goal:** Aceder ao editor (qualquer ponto de entrada)

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Pedido autorizado pelo perímetro | F-001, F-004 | Controlo de acesso | Acesso autorizado |
| 2. Editor interno não responde | F-003 | Experiência de acesso | Erro de upstream detectado |
| 3. Página de erro branded apresentada | F-003 | Experiência de acesso | Utilizador vê mensagem clara com acções de recuperação |
| 4a. Utilizador clica "Tentar novamente" | F-003 | Experiência de acesso | Nova tentativa ao editor |
| 4b. Utilizador clica "Voltar ao painel" | F-002 | Experiência de acesso | Redirect para dashboard da plataforma |

**Resultado de sucesso (4a):** Editor recuperou → carregado normalmente.
**Resultado alternativo (4b):** Utilizador retorna ao painel e aguarda.

---

### Journey 5 — Ana verifica acessos ao editor (auditoria)

**Utilizador:** Ana (Administradora de plataforma)
**Goal:** Verificar que todos os acessos ao editor estão registados e são rastreáveis

| Passo | Feature tocada | Domínio | Resultado |
|-------|---------------|---------|-----------|
| 1. Ana acede ao painel de auditoria da plataforma | F-005 | Observabilidade | Registos de acesso ao editor visíveis |
| 2. Exporta relatório de acessos | F-005 | Observabilidade | Relatório inclui tenant, utilizador, timestamp, URL |
| 3. Confirma que todos os acessos passaram pelo perímetro | F-001 | Controlo de acesso | Nenhum acesso directo (sem sessão) nos registos |

**Resultado de sucesso:** Ana fecha o relatório de compliance com confiança.

---

## Feature interaction map

```
                    ┌─────────────────────────────────┐
                    │   SISTEMA DE AUTENTICAÇÃO RID   │
                    │   (existente — fora do scope)   │
                    └────────────────┬────────────────┘
                                     │ sessão activa
                                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DOMÍNIO: CONTROLO DE ACESSO                    │
│                                                                    │
│   F-001 Perímetro ──────────────── F-004 Isolamento por tenant    │
│   (auth gate)          valida          (tenant check)             │
│       │                               │                           │
│       │ acesso autorizado             │                           │
└───────┼───────────────────────────────┼───────────────────────────┘
        │                               │
        │ identidade + tenant           │ acesso autorizado
        ▼                               ▼
┌───────────────────────┐    ┌──────────────────────────────────────┐
│  DOMÍNIO: OBS.        │    │    DOMÍNIO: EXPERIÊNCIA DE ACESSO    │
│  DE NEGÓCIO           │    │                                       │
│                       │    │  F-002 Endereço único                 │
│  F-005 Auditoria      │    │  (URL canónico + deep links)          │
│  (registo de acesso)  │    │       │                               │
│                       │    │       │ upstream indisponível         │
│  → sistema auditoria  │    │       ▼                               │
│    da plataforma      │    │  F-003 Página de erro branded         │
│                       │    │  (retry / voltar ao painel)           │
└───────────────────────┘    └──────────────────────────────────────┘
                                       │
                                       │ pedido autorizado
                                       ▼
                    ┌─────────────────────────────────┐
                    │   EDITOR DE FLUXOS INTERNO      │
                    │   (Langflow — fora do scope)    │
                    └─────────────────────────────────┘
```

### Dependency matrix

| Feature | Depende de | Bloqueia | Opcional |
|---------|-----------|---------|---------|
| F-001 Perímetro de autenticação | Sistema auth existente da plataforma | F-002, F-003, F-004, F-005 | — |
| F-002 Endereço único | F-001 | F-005 | — |
| F-003 Página de erro | F-001 | — | — |
| F-004 Isolamento por tenant | F-001, sistema tenants existente | F-005 | — |
| F-005 Auditoria de acesso | F-001, F-002, F-004 | — | — |
| F-006 Paridade RockItDown (fase 2) | F-001, F-002 | — | F-003, F-005 |

---

## Backend integration points

**Topologia:** Fullstack | **Padrão de API:** BFF

### Dependências por feature

| Feature | Dependência de backend | Direcção de dados | Notas |
|---------|----------------------|-------------------|-------|
| F-001 Perímetro de autenticação | Sistema de sessão da plataforma RID | Leitura (validação) | Gate lê sessão activa; não a cria |
| F-001 Perímetro de autenticação | Sistema de autenticação RID (login) | Escrita (redirect) | Gate redireciona para login com parâmetro `next` |
| F-004 Isolamento por tenant | Sistema de gestão de tenants (django-tenants) | Leitura | Gate lê tenant da sessão activa |
| F-005 Auditoria | Sistema de auditoria da plataforma | Escrita | Gate escreve evento de acesso após autorização |
| F-002 Endereço único | Editor de fluxos interno (Langflow) | Proxy (bidirecional) | Gate encaminha request/response entre utilizador e Langflow |
| F-003 Página de erro | Nenhuma (servida directamente) | — | Página estática/template servida pelo servidor da plataforma |

### Dependências externas ao scope (sistemas existentes)

| Sistema | Papel | Interacção com este feature |
|---------|-------|----------------------------|
| Sistema de autenticação RID | Gere sessões e login | F-001 lê sessões existentes; redireciona para login existente |
| django-tenants | Gestão de multi-tenancy | F-004 valida tenant da sessão |
| Sistema de auditoria da plataforma | Registo de eventos | F-005 escreve eventos de acesso |
| Editor de fluxos (Langflow) | Serviço interno alvo do proxy | F-002 encaminha tráfego após autorização |

### Fluxo de dados resumido

| Ponto de entrada | → | Gate (este feature) | → | Destino |
|-----------------|---|---------------------|---|---------|
| `/flows/*` (utilizador autenticado) | → | Valida sessão + tenant → regista auditoria | → | Editor de fluxos interno |
| `/flows/*` (sem sessão) | → | Detecta ausência de sessão | → | `/login/?next=<url>` |
| `/flows/*` (upstream indisponível) | → | Detecta falha do upstream | → | Página de erro branded |
| `/flows/*` (sessão expirada no editor) | → | Detecta 401 | → | Overlay "Sessão expirada" |

### Riscos de integração

| Feature | Dependência | Risco | Mitigação |
|---------|------------|-------|-----------|
| F-001 | Sistema de sessão RID | Sessão Django e FastAPI podem não ser partilhadas automaticamente | Gate deve validar sessão num único ponto (Django) — não duplicar em FastAPI |
| F-002 | Editor de fluxos (Langflow) | WebSocket upgrade pode não passar pelo gate correctamente | Configuração explícita de headers `Upgrade`/`Connection` no proxy |
| F-002 | Editor de fluxos (Langflow) | Router do Langflow pode usar hash-based routing (# não chega ao servidor) | Investigar no TRD — pode afectar preservação do `next` param |
| F-005 | Sistema de auditoria da plataforma | Registo assíncrono pode falhar silenciosamente e bloquear o request | Registo deve ser não-bloqueante — falha no log não deve impedir acesso ao editor |

---

## Phasing strategy

### Fase 1 — MVP (prioridade máxima)

**Goal:** Fechar a segunda entrada pública e garantir que todo acesso ao editor passa pelo perímetro RID.

**Features:** F-001, F-002, F-004, F-003, F-005

**Valor entregue:**
- Administradoras: zero acessos ao editor fora do perímetro; trilhos de auditoria completos.
- Builders: um único URL estável; deep links e partilha de URL funcionam.
- Operações: página de erro branded em caso de falha do editor.

**Critérios de sucesso:**
- Zero acessos ao editor sem sessão RID válida (verificável por teste)
- 100% dos acessos ao editor produzem registo de auditoria
- Página de erro RID em 100% dos cenários de indisponibilidade do editor
- URL antigo (`:7861`) não acessível em staging/produção

**Trigger para próxima fase:** MVP em produção e estável por ≥ 30 dias.

---

### Fase 2 — Paridade operacional com RockItDown (opcional)

**Goal:** Editor servido directamente pelo servidor de aplicação da plataforma, eliminando o proxy como componente separado.

**Features:** F-006

**Valor entregue:**
- Operações: topologia simplificada; sem componente de proxy separado para gerir.
- Paridade com o padrão de referência interno (RockItDown).

**Critérios de sucesso:** Editor acessível via Django sem proxy reverso como intermediário.

**Trigger:** Decisão de produto/infra — não é bloqueante para o negócio após Fase 1.

---

## Scope boundaries

### Incluído

- Perímetro de autenticação no ponto de entrada do editor
- Endereço único dentro do domínio da plataforma
- Redirect para login com preservação do URL destino
- Overlay de sessão expirada com CTA para `/flows/`
- Isolamento de acesso por tenant
- Página de erro branded com retry e link para painel
- Auditoria de acesso integrada no sistema existente da plataforma
- Suporte a WebSockets no mesmo path e política de autenticação

### Excluído (explicitamente)

| Item excluído | Motivo |
|---------------|--------|
| Redesenho da UI do editor de fluxos | Langflow não é modificado por este feature |
| Novas funcionalidades de criação ou execução de fluxos | Fora do escopo da entrada única |
| Instâncias separadas do editor por tenant | Fase 2 futura — decisão de negócio pendente |
| Dashboard de negócio para métricas do editor | Infraestrutura — cobertura por stack de observabilidade existente |
| SPA do editor servida directamente pelo Django | Fase 2 futura (F-006) |
| Provisioning self-service de editor por tenant | Fora do escopo |

---

## Risk assessment

### Riscos de complexidade de feature

| Feature | Complexidade | Razão | Mitigação |
|---------|-------------|-------|-----------|
| F-001 Perímetro de autenticação | Alta | Dois runtimes (Django + FastAPI) no RID — sessão Django não é automaticamente partilhada | Validar sessão exclusivamente no Django; TRD deve definir o ponto único de validação |
| F-002 Endereço único | Média | WebSockets + hash routing do Langflow podem complicar a preservação de URL | Investigar router do Langflow antes do TRD |
| F-004 Isolamento por tenant | Baixa | django-tenants já resolve o contexto de tenant — gate só precisa de lê-lo | Confirmar API de leitura do tenant activo no TRD |
| F-003 Página de erro | Baixa | Componente independente, sem dependências de runtime externas | Implementação directa |
| F-005 Auditoria | Baixa-Média | Registo deve ser não-bloqueante para não afectar latência do acesso | Padrão de registo assíncrono a definir no TRD |

### Riscos de integração

Ver secção "Riscos de integração" em Backend Integration Points acima.

---

## Gate 2 validation

| Categoria | Requisito | Estado |
|-----------|-----------|--------|
| Completude de features | Todas as features do PRD (RF-001 a RF-005) mapeadas | ✅ |
| Categorização | Core/Supporting/Enhancement definidas | ✅ |
| Domínios | 3 domínios com fronteiras claras e coerentes | ✅ |
| Jornadas de utilizador | 5 jornadas documentadas (happy path, redirect, sessão expirada, erro, auditoria) | ✅ |
| Pontos de integração | Todos identificados e documentados com direcção | ✅ |
| Prioridade e faseamento | Fase 1 (MVP) e Fase 2 (opcional) definidas com critérios | ✅ |
| Sem detalhes técnicos | Sem tecnologias, frameworks, schemas ou protocolos | ✅ |
| Backend integration points | Documentados (topologia fullstack) | ✅ |

**Resultado:** ✅ PASS → Gate 3 (TRD)

**Próximo passo:** `ring-pm-team:pre-dev-trd-creation`
