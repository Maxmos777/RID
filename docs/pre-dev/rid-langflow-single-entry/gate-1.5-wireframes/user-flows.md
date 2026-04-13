---
feature: rid-langflow-single-entry
gate: 1
document: user-flows
date: 2026-04-05
author: ring:product-designer
prd_ref: docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md
---

# User flows — Entrada única autenticada para o editor de fluxos

**Nota de topologia:** Este feature é um proxy/auth gate de infraestrutura. A Langflow SPA não é modificada. Os fluxos documentados aqui descrevem o comportamento do perímetro de autenticação — o que o utilizador experiencia antes de aterrar no editor, e o que vê quando o editor está indisponível.

---

## Flow 1: Acesso autenticado ao editor (happy path)

### Entry points
- Utilizador clica em link "Editor de Fluxos" no painel da plataforma RID (sessão activa).
- Utilizador abre bookmark do URL do editor (sessão activa no browser).
- Utilizador acede a deep link partilhado por colega (sessão activa).

### Happy path
1. Utilizador navega para o URL do editor (`/flows/` ou deep link `/flows/<id>`).
2. Gate de autenticação valida sessão RID — sessão válida encontrada.
3. Gate regista acesso nos trilhos de auditoria (tenant, utilizador, timestamp, URL).
4. Gate verifica isolamento de tenant — utilizador pertence ao tenant do path.
5. Gate encaminha request para o upstream Langflow interno.
6. Langflow responde com a SPA ou o fluxo específico.
7. Utilizador vê o editor de fluxos directamente, sem interrupção.

### Alternative paths
- **Se utilizador actualiza a página:** passos 2–7 repetem-se; sessão ainda válida → editor recarrega.
- **Se utilizador acede ao URL antigo (`:7861`):** em produção/staging retorna 404 ou redirect permanente (301) para `/flows/`.

### Exit points
- **Success:** Utilizador trabalha no editor de fluxos.
- **Abandon:** Utilizador fecha a tab — sem impacto no fluxo.

### Diagram

```mermaid
flowchart TD
    A([Utilizador acede a /flows/ ou deep link]) --> B{Sessão RID válida?}
    B -->|Sim| C{Tenant correcto?}
    C -->|Sim| D[Regista acesso em auditoria]
    D --> E[Encaminha para Langflow interno]
    E --> F{Langflow disponível?}
    F -->|Sim| G([Editor de fluxos carregado])
    F -->|Não| H([Página de erro RID])
    C -->|Não| I([Erro 403 — acesso negado])
    B -->|Não| J[[Flow 2: Redirect para login]]
```

---

## Flow 2: Utilizador não autenticado acede ao editor (redirect flow)

### Entry points
- Utilizador não autenticado tenta aceder ao URL do editor (sem sessão, sessão expirada, ou novo browser).
- Utilizador recebe deep link de colega e não tem sessão activa.
- Utilizador tenta aceder ao editor a partir de link em email ou documentação.

### Happy path
1. Utilizador navega para `/flows/` ou `/flows/<id>` sem sessão RID válida.
2. Gate de autenticação detecta ausência ou invalidade de sessão.
3. Gate devolve redirect HTTP 302 para `/login/?next=<url-original-encoded>`.
4. Browser do utilizador carrega a página de login da plataforma RID.
5. Utilizador insere as suas credenciais e submete o formulário de login.
6. Plataforma RID autentica o utilizador e cria sessão.
7. Plataforma RID lê o parâmetro `next` e redireciona para o URL original.
8. Gate de autenticação valida a nova sessão — válida.
9. Gate regista acesso em auditoria.
10. Utilizador aterra no editor (ou no fluxo específico do deep link).

### Alternative paths
- **Se login falhar (credenciais incorrectas):** utilizador permanece na página de login com mensagem de erro; parâmetro `next` é preservado para nova tentativa.
- **Se utilizador abandona o login:** parâmetro `next` não é consumido; utilizador retorna ao painel da plataforma (ou página de login sem `next`).
- **Se URL de destino for inválido (fluxo apagado):** utilizador aterra no editor com o erro nativo do Langflow para fluxo não encontrado — fora do escopo deste feature.

### Exit points
- **Success:** Utilizador autenticado aterra no editor com o conteúdo destino.
- **Failure (login falha):** Utilizador permanece na página de login.
- **Abandon:** Utilizador fecha o browser ou navega para outra página.

### Diagram

```mermaid
flowchart TD
    A([Utilizador acede a /flows/<path> sem sessão]) --> B[Gate detecta sessão ausente/inválida]
    B --> C[Redirect 302 para /login/?next=<url-encoded>]
    C --> D([Página de login RID])
    D --> E{Credenciais válidas?}
    E -->|Não| F[Mensagem de erro no login]
    F --> D
    E -->|Sim| G[Plataforma cria sessão RID]
    G --> H[Redirect para URL original via parâmetro next]
    H --> I{Sessão válida no gate?}
    I -->|Sim| J[Regista acesso em auditoria]
    J --> K([Editor de fluxos — conteúdo destino])
    I -->|Não| C
    D --> L{Utilizador abandona?}
    L -->|Sim| M([Painel da plataforma ou sessão encerrada])
```

---

## Flow 3: Sessão expira durante uso do editor

### Entry points
- Utilizador está a trabalhar no editor de fluxos quando a sessão RID expira.

### Trigger
- Expiração natural da sessão Django (timeout configurado na plataforma).
- Sessão invalidada administrativamente (logout remoto, rotação de token).

### Behavior (a definir no TRD — HIGH severity issue)

**Estado actual do PRD:** não especificado. O comportamento depende da implementação do gate:

- **Opção A (redirect imediato):** o próximo request ao gate retorna 401 → redirect para login com `next=<url-actual>`. Utilizador perde estado não guardado no editor.
- **Opção B (overlay de sessão expirada):** o shell RID detecta expiração e apresenta overlay "Sessão expirada — faça login para continuar" sem navegar para fora do editor. Após re-autenticação, sessão é restaurada.

**Decisão:** Opção B — overlay "Sessão expirada" com botão "Entrar novamente" que redireciona para `/flows/` após re-autenticação. Evita perda de estado e mantém o utilizador no contexto do editor.

### Diagram

```mermaid
flowchart TD
    A([Utilizador no editor — sessão expira]) --> B{Tipo de gate}
    B -->|Redirect imediato| C[Próximo request ao gate → 401]
    C --> D[Redirect para /login/?next=<url-actual>]
    D --> E[[Flow 2: Redirect para login]]
    B -->|Overlay de sessão| F[Shell RID detecta expiração]
    F --> G([Overlay: Sessão expirada — faça login])
    G --> H{Utilizador autentica?}
    H -->|Sim| I([Editor restaurado — mesmo estado])
    H -->|Não| J([Utilizador encerra sessão])
```

---

## Flow 4: Editor de fluxos indisponível (error page)

### Entry points
- Qualquer acesso ao editor (autenticado ou redirect pós-login) quando o upstream Langflow não responde.

### Trigger
- Serviço Langflow parado ou a reiniciar.
- Timeout de rede entre o proxy/gate e o contentor Langflow.
- Langflow retorna 5xx.

### Happy path (do ponto de vista do utilizador)
1. Utilizador acede ao editor (autenticado).
2. Gate valida sessão — válida.
3. Gate tenta encaminhar para Langflow interno.
4. Langflow não responde (timeout) ou retorna 5xx.
5. Gate intercepta o erro antes de devolvê-lo ao browser.
6. Gate serve a página de erro com identidade visual RID.
7. Utilizador vê: título claro, mensagem explicativa, e acções de recuperação.
8. Utilizador tenta "Tentar novamente" ou "Voltar ao painel".

### Alternative paths
- **Se retry resulta em sucesso:** utilizador é levado para o editor normalmente.
- **Se retry falha novamente:** página de erro mantida; botão "Tentar novamente" mostra estado de loading durante a tentativa.
- **Se utilizador clica "Voltar ao painel":** redirect para o dashboard da plataforma RID.

### Diagram

```mermaid
flowchart TD
    A([Utilizador acede ao editor — sessão válida]) --> B[Gate encaminha para Langflow interno]
    B --> C{Langflow disponível?}
    C -->|Sim| D([Editor de fluxos carregado])
    C -->|Não — timeout ou 5xx| E[Gate intercepta erro]
    E --> F([Página de erro RID])
    F --> G{Acção do utilizador}
    G -->|Tentar novamente| H[Loading no botão — nova tentativa]
    H --> C
    G -->|Voltar ao painel| I([Dashboard da plataforma RID])
```

---

## State machine — Auth gate

Diagrama de estados do gate de autenticação para uma request ao editor:

```mermaid
stateDiagram-v2
    [*] --> Receiving: Request para /flows/*

    Receiving --> ValidatingSession: Ler cookie de sessão
    ValidatingSession --> Authenticated: Sessão válida
    ValidatingSession --> Unauthenticated: Sessão ausente ou inválida

    Unauthenticated --> RedirectingToLogin: 302 → /login/?next=<url>
    RedirectingToLogin --> [*]: Browser segue redirect

    Authenticated --> ValidatingTenant: Verificar tenant da sessão
    ValidatingTenant --> TenantValid: Tenant correcto
    ValidatingTenant --> TenantInvalid: Tenant diferente

    TenantInvalid --> ServingForbidden: 403 Forbidden
    ServingForbidden --> [*]

    TenantValid --> LoggingAudit: Registar acesso
    LoggingAudit --> ProxyingToLangflow: Encaminhar request

    ProxyingToLangflow --> LangflowAvailable: Upstream responde
    ProxyingToLangflow --> LangflowUnavailable: Timeout ou 5xx

    LangflowAvailable --> ServingEditor: Serve resposta do Langflow
    ServingEditor --> [*]

    LangflowUnavailable --> ServingErrorPage: Serve página de erro RID
    ServingErrorPage --> [*]
```
