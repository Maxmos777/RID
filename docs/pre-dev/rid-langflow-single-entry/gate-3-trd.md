---
feature: rid-langflow-single-entry
gate: 3
date: 2026-04-05
status: draft
topology:
  structure: multi-repo
  target_repo: /home/RID
  reference_repo: /home/RockItDown
  scope: fullstack
  api_pattern: bff
  arch_style: modular_monolith
  edge: reverse_proxy
  edge_router: traefik
---

# TRD — Entrada única autenticada para o editor de fluxos (RID)

## Resumo executivo

Este documento define os requisitos técnicos para fechar a segunda entrada pública ao editor de fluxos do RID, estabelecendo um Auth Gate baseado em Reverse Proxy com sub-request de validação para o Application Server. A solução reutiliza o sistema de sessão existente da plataforma sem modificar o Editor Interno, e é extensível para paridade operacional total com o padrão de referência em Fase 2. O perímetro de autenticação resultante cobre autenticação, isolamento de tenant e auditoria de acesso num único ponto de controlo.

---

## 1. Contexto e decisões herdadas

### 1.1 Requisitos funcionais herdados do PRD (Gate 1)

| ID | Requisito | Critério de aceitação técnico |
|----|-----------|------------------------------|
| RF-001 | Perímetro único de autenticação | Nenhum path sob `/flows/*` responde sem sessão válida da plataforma |
| RF-002 | Endereço único e estável | Um único URL canónico sob o domínio da plataforma; deep links, refresh e partilha de URL funcionam |
| RF-003 | Página de indisponibilidade integrada | Em upstream 5xx/timeout, 100% dos acessos recebem Error Page Template com identidade da plataforma |
| RF-004 | Isolamento por tenant | Auth Check Endpoint valida tenant da sessão antes de autorizar; resposta 403 em tenant inválido |
| RF-005 | Auditoria de acesso alinhada ao perímetro | Cada acesso autorizado produz registo no sistema de auditoria da plataforma (tenant, utilizador, timestamp, URL) |

### 1.2 Decisões de design herdadas (Gate 1.5 — Design Validation)

| ID | Decisão | Impacto técnico |
|----|---------|----------------|
| DD-001 | Sessão expirada: overlay em vez de redirect imediato | O Auth Gate devolve 401 JSON durante uso activo; o shell da Frontend SPA detecta e apresenta overlay sem navegar |
| DD-002 | Estado transitório: HTTP 302 directo | Sem página intermédia; redirect imediato ao detectar sessão ausente |
| DD-003 | Página de erro: dois CTAs com identidade da plataforma | Error Page Template servida pelo Application Server; sem dependência de assets do Editor Interno |
| DD-004 | UI Library: componentes React 18 nativos + CSS plano | Sem biblioteca de componentes externa nos novos componentes |
| DD-005 | Acessibilidade: WCAG 2.1 AA | Contraste mínimo 4.5:1, touch targets 44×44px em mobile; aplicado a todos os componentes novos |

### 1.3 Estilo arquitectural

**Modular Monolith com Container-native Edge Router (Traefik) como borda.**

O Application Server (Django) permanece o único ponto de validação de identidade. O Container-native Edge Router actua como borda de infraestrutura que delega a decisão de autorização ao Application Server via forwardAuth middleware. O Editor Interno é um serviço interno sem exposição pública. O Async API Runtime (FastAPI) não participa na validação de sessão — recebe apenas tráfego já autorizado.

A Fase 2 futura (F-006) poderá eliminar o Edge Router como componente separado, servindo o Editor Interno directamente pelo Application Server, em paridade total com o padrão de referência.

---

## 2. Componentes

### Componente 1 — Container-native Edge Router

**Responsabilidade:** Única entrada pública para `/flows/*`. Delega a decisão de autorização ao Auth Check Endpoint antes de encaminhar qualquer pedido.

**Comportamento por resposta do Auth Check Endpoint:**

| Resposta do Auth Check | Acção do Auth Gate |
|------------------------|-------------------|
| 200 (sessão válida + tenant correcto) | Encaminha request para o Editor Interno |
| 401 (sessão ausente ou expirada) | Redirect HTTP 302 para `/login/?next=<url-encoded>` |
| 403 (tenant inválido) | Responde com 403 ao cliente |
| 5xx ou timeout do upstream | Serve Error Page Template (ver Componente 4) |

**WebSocket:**
- Validação de sessão ocorre no handshake HTTP inicial (upgrade request).
- Após upgrade bem-sucedido, a conexão WebSocket é mantida aberta sem revalidação por frame.
- Headers `Upgrade` e `Connection` são passados explicitamente pelo Edge Router para o Editor Interno.
- Limitação conhecida (MVP): conexões WebSocket abertas não são terminadas quando a sessão Django expira durante o uso. O overlay de sessão (DD-001) é activado por heartbeat periódico, não por frames WebSocket.

**Configuração necessária:**
- forwardAuth middleware para Auth Check Endpoint em cada pedido para `/flows/*` (incluindo assets e WebSocket upgrade).
- Configurado via labels Docker no serviço — sem ficheiros de configuração externos.
- Passa o header `Host` original ao Auth Check Endpoint (necessário para resolução de tenant pelo middleware multi-tenant).
- Timeout longo para conexões WebSocket (documentar valor no runbook operacional).
- Sem porta do Editor Interno exposta no host em staging/produção.

> Nota: a escolha concreta de implementação do Edge Router está documentada em ADR-012 e no Dependency Map (Gate 6).

---

### Componente 2 — Auth Check Endpoint (no Application Server)

**Responsabilidade:** Endpoint leve de validação de sessão e tenant, exclusivamente no Application Server (Django).

**Localização:** Application Server. O Async API Runtime (FastAPI) não implementa nem replica esta lógica.

**Lógica de validação:**

```
1. Ler cookie de sessão da plataforma do pedido de sub-request
2. Verificar sessão activa (não expirada, não invalidada)
3. Verificar tenant da sessão vs tenant esperado
4. Se válido: registar evento de acesso (async fire-and-forget) → responder 200
5. Se sessão ausente/expirada: responder 401
6. Se tenant inválido: responder 403
```

**Contrato de resposta:**

| Código | Condição |
|--------|----------|
| 200 | Sessão activa + tenant correcto |
| 401 | Sessão ausente ou expirada |
| 403 | Tenant inválido (utilizador não pertence ao tenant do pedido) |

**Auditoria (F-005):**
- Após resposta 200, regista evento de acesso no sistema de auditoria da plataforma.
- Implementado como async fire-and-forget: falha no registo não bloqueia o acesso ao editor.
- Campos mínimos do registo: tenant, utilizador, timestamp, URL do pedido original.

**Reutilização do contexto de tenant:**
- Usa o middleware multi-tenant existente da plataforma (django-tenants) para ler o tenant activo.
- Não duplica lógica de resolução de tenant.

**Performance target:** p95 < 20ms (leitura de sessão sem I/O pesado; resposta deve ser stateless).

---

### Componente 3 — Session Expiry Overlay (Frontend SPA)

**Responsabilidade:** Informar o utilizador de sessão expirada durante uso activo do editor, sem causar navegação involuntária.

**Localização:** Shell da Frontend SPA (RID). Não implementado no Editor Interno.

**Comportamento:**

Shell React faz polling periódico (heartbeat a cada 2-3 minutos) ao Auth Check Endpoint. Se receber 401, apresenta o overlay antes de qualquer acção do utilizador forçar redirect. O Edge Router retorna 302 para navegação de browser — o overlay é activado pelo cliente, não pelo proxy.

1. Heartbeat periódico (a cada 2-3 minutos) ao Auth Check Endpoint detecta sessão expirada proactivamente.
2. Apresenta overlay "Sessão expirada" por cima do conteúdo do editor — sem navegar para fora da página.
3. CTA "Entrar novamente" → redirect para `/login/?next=/flows/`.
4. A decisão de apresentar o overlay é tomada no cliente (Frontend SPA); o Edge Router retorna 302 para navegação de browser inicial.
5. Heartbeat deve ser cancelado quando o utilizador sai do editor.

**Implementação (DD-001, DD-004):**
- Componente React 18 com inline styles ou CSS plano.
- Acessibilidade: `role="alertdialog"`, `aria-modal="true"`, navegação por teclado (Tab, Enter, Escape).
- `aria-live="assertive"` para leitura imediata por screen reader.

**Nota:** A detecção de expiração de sessão por WebSocket frames está fora do escopo do MVP (ver limitação conhecida no Componente 1).

---

### Componente 4 — Error Page Template

**Responsabilidade:** Página de erro com identidade da plataforma, servida pelo Auth Gate Reverse Proxy quando o Editor Interno está indisponível.

**Trigger:** Upstream (Editor Interno) responde com 5xx ou atinge timeout.

**Requisitos:**
- Bundle isolado sem dependência de assets do Editor Interno.
- Servida pelo Application Server e cacheável pelo Auth Gate Reverse Proxy.
- Conforme DD-003 (identidade RID, mensagem em pt-BR) e DD-005 (WCAG 2.1 AA).

**CTAs obrigatórias:**
- "Tentar novamente" (primário): faz GET `/flows/` via JavaScript; navega apenas se a resposta for 200. Mostra estado de loading durante a tentativa.
- "Voltar ao painel" (secundário): link para o dashboard da plataforma.

**Performance target:** Tempo de resposta < 200ms, independente do estado do Editor Interno.

**Acessibilidade (DD-005):**
- Contraste mínimo 4.5:1.
- Touch targets 44×44px em mobile.
- `role="main"`, `aria-label` nas CTAs.

---

### Componente 5 — Editor Interno

**Responsabilidade:** Serviço de edição de fluxos. Não modificado por este feature.

**Restrições de exposição:**
- Sem porta exposta no host em staging e produção.
- Acessível exclusivamente pelo Auth Gate Reverse Proxy na rede interna de containers.
- Recebe apenas tráfego já autorizado pelo Auth Gate — não valida sessão internamente para pedidos provenientes do proxy.

**Configuração actual a alterar (docker-compose.yml):**
- Remover ou restringir o mapeamento `7861:7860` em staging/produção.
- O serviço permanece na rede interna; o Auth Gate encaminha tráfego via nome de serviço interno.

**Compatibilidade WebSocket:** headers `Upgrade` e `Connection` devem ser passados explicitamente pelo Auth Gate (ver Componente 1).

---

## 3. Modelo de segurança

### 3.1 Threat model

| Ameaça | Mitigação |
|--------|-----------|
| Acesso directo ao Editor Interno sem autenticação | Remoção da porta pública; Editor Interno acessível apenas via Auth Gate na rede interna |
| Session fixation | Nova sessão criada após login (comportamento padrão do auth framework da plataforma) |
| Open redirect via parâmetro `next` | Validar que `next` é path interno (começa com `/`); rejeitar URLs absolutas e schemeful URLs |
| Tenant cross-access | Auth Check Endpoint valida tenant da sessão antes de autorizar; 403 em caso de mismatch |
| Host header manipulado no forwardAuth | Edge Router valida e passa apenas o Host original; Auth Check Endpoint não aceita Host headers de origens não confiáveis |

### 3.2 OWASP relevante

- **A01 — Broken Access Control:** mitigado pelo Auth Gate (forwardAuth middleware obrigatório) e pela remoção da porta pública do Editor Interno.
- **A07 — Identification and Authentication Failures:** mitigado pela validação exclusiva no Application Server e pelo comportamento de nova sessão após login.

### 3.3 Validação do parâmetro `next`

```python
# Lógica de validação obrigatória no Application Server
def is_safe_next_url(next_url: str) -> bool:
    # Aceitar apenas paths internos
    return (
        next_url.startswith("/")
        and not next_url.startswith("//")
        and "://" not in next_url
    )
```

---

## 4. Integration Patterns

### 4.1 Padrão: BFF (Backend for Frontend)

O Container-native Edge Router actua como BFF do Editor Interno: a Frontend SPA comunica com a plataforma RID; o Edge Router é o único ponto de entrada para o Editor Interno a partir da rede pública.

### 4.2 Data flow

```
Frontend SPA
    │
    ▼
Container-native Edge Router  (forwardAuth para Auth Check)
    │                              │
    │                              ▼
    │                    Auth Check Endpoint
    │                    (Application Server)
    │                              │
    │            200 ◄─────────────┘
    ▼
Editor Interno
```

### 4.3 WebSocket

- O upgrade WebSocket ocorre após validação HTTP no handshake inicial.
- O Auth Gate passa os headers `Upgrade: websocket` e `Connection: Upgrade` para o Editor Interno.
- Após upgrade, a conexão é bidirecional e não revalidada por frame (limitação conhecida do MVP).

---

## 5. Backend Integration Points

| Feature | Componente | Sistema integrado | Direcção |
|---------|-----------|------------------|---------|
| F-001 Auth | Auth Check Endpoint | Sistema de sessão da plataforma (Application Server) | Leitura |
| F-004 Tenant | Auth Check Endpoint | Middleware multi-tenant (django-tenants) | Leitura |
| F-005 Auditoria | Auth Check Endpoint | Sistema de auditoria da plataforma | Escrita async |
| F-002 URL único | Container-native Edge Router | Editor Interno | Proxy bidirecional |
| F-003 Error Page | Error Page Template | Application Server | Servida directamente |

### 5.1 Sistemas externos ao escopo (dependências existentes)

| Sistema | Papel | Interacção |
|---------|-------|-----------|
| Sistema de autenticação da plataforma | Gere sessões e login | Auth Check lê sessões; Auth Gate redireciona para login existente |
| Middleware multi-tenant (django-tenants) | Gestão de multi-tenancy | Auth Check valida tenant da sessão activa |
| Sistema de auditoria da plataforma | Registo de eventos | Auth Check escreve eventos de acesso (fire-and-forget) |
| Editor Interno | Serviço interno alvo do proxy | Edge Router encaminha tráfego após autorização |

### 5.2 Relação com o bridge existente

O bridge de auto-login existente (`/api/v1/langflow/auth/auto-login` no Async API Runtime) é um componente de provisioning de credenciais Langflow para utilizadores da plataforma. Este feature não o substitui nem o remove — são camadas complementares:

- **Auth Gate (este feature):** controla o acesso à UI do Editor Interno via sessão da plataforma.
- **Bridge de auto-login (existente):** provisiona credenciais Langflow (JWT + API key) para chamadas à API do Editor Interno.

O Auth Gate não usa o bridge de auto-login na sua lógica de forwardAuth.

---

## 6. Topologia de deployment (lógica)

```
Internet
    │
    ▼
[Container-native Edge Router]  ← única entrada pública para /flows/*
    │           │                  (container Docker, rede rid-network)
    │ 200       │ 5xx/timeout       configuração via labels Docker
    ▼           ▼
[Editor   [Error Page
 Interno]  Template]
    ↑
[Auth Check Endpoint]  ← forwardAuth middleware
    ↑
[Application Server]  ← sistema de sessão + tenant + auditoria
```

**Rede interna:** O Editor Interno não tem porta exposta no host em staging/produção. O Edge Router comunica com o Editor Interno via nome de serviço na rede interna de containers (`rid-network`).

**Alteração necessária em docker-compose.yml:**
- Remover ou tornar condicional (apenas perfil `local`) o mapeamento de porta `7861:7860` do serviço do Editor Interno.
- O serviço Edge Router é adicionado ao perfil `langflow` do docker-compose, na rede `rid-network`, com acesso ao socket Docker para descoberta de serviços.
- Configuração de routing e forwardAuth via labels Docker — versionada no docker-compose.yml, sem ficheiros de configuração externos.

---

## 7. Issues técnicas conhecidas

### 7.1 Hash routing e parâmetro `next`

Hashes (`#fragment`) não chegam ao servidor — são processados exclusivamente pelo browser. O parâmetro `next` preserva apenas o pathname e a query string (`/flows/path?query=value`), não o fragment.

Se o Editor Interno usar hash-based routing internamente, a preservação de deep links após redirect de login é limitada ao pathname. Esta é uma limitação aceite no MVP. Documentar no runbook de onboarding.

### 7.2 Sessão do Application Server vs Async API Runtime

A validação de sessão acontece exclusivamente no Application Server (Django). O Async API Runtime (FastAPI) não valida sessão de plataforma — recebe apenas pedidos já autorizados pelo Auth Gate ou provenientes de chamadas autenticadas de API (bridge de auto-login, ADR-009).

Não duplicar lógica de validação de sessão no Async API Runtime.

### 7.3 WebSocket e sessão expirada (limitação conhecida do MVP)

Conexões WebSocket abertas não são terminadas automaticamente quando a sessão Django expira durante o uso do Editor Interno. O Session Expiry Overlay (Componente 3) é activado pelo heartbeat periódico HTTP, não por frames WebSocket.

**Comportamento esperado:** utilizador com sessão expirada continua a ter a conexão WebSocket activa até o heartbeat detectar o 401 e activar o overlay, ou até fechar/recarregar o editor.

Esta limitação é documentada e aceite no MVP. O heartbeat periódico (Componente 3) mitiga parcialmente o problema ao detectar a expiração proactivamente.

---

### 7.4 Host header no forwardAuth (Edge Router)

O Edge Router deve ser configurado para passar o header `Host` original ao Auth Check Endpoint no sub-request de forwardAuth. Sem esta configuração, o `TenantMainMiddleware` recebe o hostname interno do container (`backend:8000`) e falha a resolver o tenant.

Configuração necessária: `trustForwardHeader: true` no middleware forwardAuth e `X-Forwarded-Host` passado ao backend.

---

## 8. Targets de performance e qualidade

| Componente | Métrica | Target |
|-----------|---------|--------|
| Auth Check Endpoint | Latência p95 | < 20ms |
| Auth Gate Reverse Proxy | Overhead vs acesso directo | < 30ms |
| Error Page Template | Tempo de resposta | < 200ms (independente do estado do Editor Interno) |
| Redirect para login | Latência após detecção de sessão inválida | < 100ms |

### 8.1 Qualidade

- Cobertura de testes unitários para Auth Check Endpoint: validação de sessão, validação de tenant, validação do parâmetro `next`.
- Teste de integração: acesso sem sessão → redirect → login → retorno ao editor.
- Teste de indisponibilidade: upstream 5xx → Error Page Template (não erro genérico de proxy).
- Teste de tenant cross-access: utilizador de tenant A não acede ao editor de tenant B.
- WCAG 2.1 AA verificado em Error Page Template e Session Expiry Overlay.

---

## 9. Riscos técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Editor Interno usa hash routing | Média | Médio | Deep links preservam pathname; fragment perdido é aceitável no MVP; documentar no runbook |
| WebSocket timeout no Auth Gate Reverse Proxy | Baixa | Alto | Configurar timeout longo no proxy; documentar valor no runbook operacional |
| Auth Check Endpoint como bottleneck | Baixa | Alto | Resposta stateless e cacheable (sessão válida → 200 por N segundos); sem I/O pesado no hot path |
| Auditoria bloqueante atrasa acesso | Média | Médio | Implementar como fire-and-forget; falha no log não bloqueia acesso ao editor |
| Remoção da porta pública quebra workflows existentes | Média | Alto | Comunicar mudança aos utilizadores antes do deploy; redirect 301 de `:7861` para `/flows/` durante período de transição |

---

## 10. Gate 3 — Validation Checklist

| Categoria | Verificação | Estado |
|-----------|-------------|--------|
| **Rastreabilidade** | Todos os RF (RF-001 a RF-005) mapeados para componentes | PASS |
| **Rastreabilidade** | Todas as decisões de design (DD-001 a DD-005) endereçadas | PASS |
| **Arquitectura** | Estilo arquitectural declarado (Modular Monolith + Container-native Edge Router) | PASS |
| **Componentes** | 5 componentes descritos com responsabilidades, comportamentos e contratos | PASS |
| **Segurança** | Threat model com 4 ameaças e mitigações documentadas | PASS |
| **Segurança** | OWASP A01 e A07 endereçados | PASS |
| **Segurança** | Validação do parâmetro `next` especificada | PASS |
| **Integração** | Padrão BFF declarado e data flow documentado | PASS |
| **Integração** | Backend integration points por feature (tabela) | PASS |
| **Integração** | Relação com bridge existente esclarecida | PASS |
| **Deployment** | Topologia lógica documentada | PASS |
| **Deployment** | Alteração necessária no Container Orchestration identificada (porta pública) | PASS |
| **Performance** | Targets de latência definidos para todos os componentes críticos | PASS |
| **Qualidade** | Critérios de teste especificados | PASS |
| **Issues técnicas** | Hash routing documentado como limitação conhecida | PASS |
| **Issues técnicas** | Sessão Application Server vs Async API Runtime clarificada | PASS |
| **Issues técnicas** | Limitação de WebSocket + sessão expirada documentada | PASS |
| **Issues técnicas** | Host header no forwardAuth e resolução de tenant documentados | PASS |
| **Riscos** | Tabela de riscos com probabilidade, impacto e mitigação | PASS |
| **Abstracção** | Arquitectura descrita de forma abstracta; escolha concreta documentada em ADR-012 e Dependency Map (Gate 6) [^1] | PASS |
| **ADR** | ADR-012 criado para a decisão arquitectural principal | PASS |
| **Arquitectura** | Decisão de edge router (container Docker) documentada com forwardAuth e Host header | PASS |

[^1]: Escolha concreta de implementação (Traefik) documentada em ADR-012 e Dependency Map (Gate 6).

**Resultado: PASS — Pronto para task breakdown e implementação.**
