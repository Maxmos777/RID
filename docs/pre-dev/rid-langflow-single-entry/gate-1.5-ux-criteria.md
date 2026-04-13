---
feature: rid-langflow-single-entry
gate: 1
document: ux-criteria
date: 2026-04-05
author: ring:product-designer
prd_ref: docs/pre-dev/rid-langflow-single-entry/gate-1-prd.md
---

# UX Acceptance Criteria — Entrada única autenticada para o editor de fluxos

## Problem validation

### Problem statement

**Who:** Administradoras de plataforma enterprise e builders de fluxos de automação que utilizam a plataforma RID.

**What:** O editor de fluxos (Langflow) está acessível numa segunda entrada de rede pública paralela ao perímetro de autenticação da plataforma, permitindo acesso sem verificação de identidade pelo sistema de controlo de acesso do RID.

**When:** A cada acesso ao editor — directo via bookmark para `:7861`, via link partilhado com origem alternativa, ou via acesso não autenticado ao URL do editor.

**Impact:**
- Trilhos de auditoria incompletos: acessos directos ao editor não aparecem nos registos de sessão da plataforma.
- Risco de conformidade mensurável: dados e fluxos de tenant expostos fora do perímetro de identidade acordado com clientes enterprise.
- Carga de suporte: dois endereços para a mesma ferramenta geram tickets de confusão ("qual URL devo usar?").
- Isolamento de tenant dependente exclusivamente de controlos internos do Langflow, sem a camada de autorização da plataforma.

### Evidence

- **Referência interna:** o repositório RockItDown resolve o mesmo problema servindo o editor sob `LoginRequiredMixin` em `/flows/`, com o backend Langflow inacessível directamente pelo browser. O RID diverge com `7861:7860` exposto no host.
- **Padrão de mercado:** ferramentas de analytics/BI embedded são invariavelmente servidas atrás do SSO da aplicação principal, nunca como origem pública paralela.
- **Pesquisa Gate 0 (`gate-0-research.md`):** identifica duas personas directamente afectadas e documenta a lacuna topológica como causa raiz do problema.
- **Brainstorm Ring:** consenso emergente entre engenharia e produto: "isso é um épico de plataforma, não um ajuste na bridge."

### Validation status

**VALIDATED.** O problema tem causa raiz identificada (topologia de rede), evidência de referência interna (RockItDown), padrão de mercado documentado, e duas personas afectadas com frustrações específicas e mensuráveis. Nenhuma questão em aberto bloqueia a validação do problema.

---

## Personas

### Persona 1: Ana — Administradora de plataforma (enterprise)

**Role:** Gestora de acessos, conformidade e auditoria para uma ou mais organizações no RID.

**Experience:** 5+ anos em operações de TI ou compliance. Proficiência técnica moderada; familiarizada com IdPs, SSO e relatórios de auditoria. Não é desenvolvedora.

**Context:** Empresa enterprise com 50–500 utilizadores na plataforma RID. Sujeita a auditorias internas e, em alguns casos, regulamentação sectorial (financeiro, saúde, logística).

**Goals:**
1. Garantir que todos os acessos a ferramentas sensíveis passam pelo IdP da plataforma e produzem registos rastreáveis.
2. Reportar a equipas de compliance com confiança que nenhum recurso da plataforma está exposto fora do perímetro acordado.
3. Resolver incidentes de acesso sem ambiguidade sobre qual URL foi utilizada.

**Pain points:**
1. Relatórios de acesso ao editor de fluxos estão incompletos porque sessões directas ao editor não passam pelo sistema de identidade da plataforma — não consegue provar que só utilizadores autorizados acederam.
2. Dois endereços para a mesma ferramenta criam inconsistência nos registos e nos procedimentos de onboarding, gerando retrabalho de documentação interna.

**Quote:**
> "Se eu não consigo provar que só os utilizadores certos acederam ao editor, não consigo fechar o relatório de conformidade. Dois URLs para a mesma ferramenta é um problema de auditoria, não de conforto."

**Scenario:** Ana recebe pedido de auditoria trimestral. Exporta log de acessos da plataforma RID e nota que vários builders da equipa de automação não aparecem nos registos do editor — porque acediam directamente por `:7861`. Tem de explicar à equipa de compliance por que o log está incompleto. Com a entrada única, todos os acessos passam pelo perímetro e aparecem no mesmo relatório.

---

### Persona 2: Bruno — Builder de fluxos

**Role:** Cria e mantém fluxos de automação para a organização no RID. Utilizador técnico mas não DevOps/infra.

**Experience:** 2–5 anos de trabalho com ferramentas de automação e integração. Confortável com interfaces gráficas de fluxo (n8n, Zapier, Langflow). Usa a plataforma RID diariamente.

**Context:** Equipa de operações ou tecnologia de empresa de médio porte. Partilha links de fluxos com colegas e parceiros. Trabalha com múltiplos tenants em alguns casos.

**Goals:**
1. Aceder ao editor de fluxos de forma rápida e previsível, a partir da plataforma onde já está autenticado.
2. Partilhar links directos para fluxos específicos com colegas sem que estes precisem de saber endereços alternativos ou passar por processos de autenticação duplicados.
3. Trabalhar sem interrupções de sessão inesperadas — refresh de página não deve expulsar do editor.

**Pain points:**
1. Dois endereços distintos para a mesma ferramenta geram confusão sobre qual usar e qual colocar no bookmark. Quando onboarding de novos colegas, nunca sabe qual URL documentar.
2. Links partilhados para fluxos específicos podem não funcionar para o destinatário dependendo da origem do link.

**Quote:**
> "Eu só quero abrir o editor e trabalhar. Não devia precisar de saber qual das duas URLs funciona hoje — e muito menos explicar isso a um colega novo."

**Scenario:** Bruno termina de construir um fluxo e quer partilhá-lo com a colega Clara. Copia o URL da barra de endereços e envia no Slack. Clara abre o link, mas como acedeu por um endereço diferente, a sessão não é reconhecida e vê uma página de erro confusa. Com a entrada única, o link funciona para qualquer utilizador autenticado na plataforma, redirecionando para login se necessário antes de devolver ao fluxo específico.

---

## Jobs to be done

### Job 1: Acesso auditável ao editor

**Statement:** Quando preciso de garantir que todos os acessos ao editor de fluxos estão registados e são rastreáveis, quero que qualquer entrada no editor passe obrigatoriamente pelo perímetro de autenticação da plataforma, para que possa reportar acessos com completude e exactidão.

- **Functional:** Que o sistema capture e associe cada acesso ao editor à identidade e sessão do utilizador na plataforma.
- **Emotional:** Sentir confiança de que o relatório de auditoria é completo e defensável.
- **Social:** Ser percebida como administradora rigorosa e confiável pela equipa de compliance e direcção.

**Priority:** Must Have.

---

### Job 2: Acesso directo e previsível ao editor

**Statement:** Quando quero aceder ao editor de fluxos a partir da plataforma onde já estou autenticado, quero encontrar sempre o mesmo endereço que funciona para acesso directo, deep links e refresh, para que possa trabalhar sem interrupções e partilhar links com confiança.

- **Functional:** Ter um único URL estável que funciona independentemente do ponto de entrada (bookmark, link partilhado, refresh de página, deep link para fluxo específico).
- **Emotional:** Sentir que a ferramenta é previsível e confiável — sem surpresas de autenticação dupla ou links quebrados.
- **Social:** Poder fazer onboarding de colegas com uma única instrução ("usa este URL").

**Priority:** Must Have.

---

### Job 3: Continuidade de sessão durante trabalho no editor

**Statement:** Quando estou a trabalhar no editor de fluxos e a minha sessão expira ou preciso de actualizar a página, quero ser redirecionado para o login e retornar ao estado exacto onde estava, para que não perca o contexto do trabalho.

- **Functional:** Que o sistema preserve o URL destino (incluindo deep link para fluxo específico) através do ciclo de autenticação.
- **Emotional:** Sentir que a sessão é gerida pela plataforma, não pelo utilizador.

**Priority:** Must Have.

---

## UX acceptance criteria

### Functional criteria

#### RF-001 — Perímetro único de autenticação

- [ ] Um utilizador não autenticado que acede a qualquer URL do editor de fluxos é redirecionado para a página de login da plataforma RID antes de qualquer conteúdo do editor ser servido.
- [ ] Após autenticação bem sucedida, o utilizador é encaminhado para o URL original que tentou aceder (incluindo deep links para fluxos específicos).
- [ ] O parâmetro `next` (ou equivalente) é preservado através do ciclo de redirect — login → autenticação → retorno — sem perdas de path, query strings ou fragmentos de URL relevantes para a navegação do editor.
- [ ] Uma sessão RID expirada que tenta aceder ao editor é tratada como sessão ausente: redirect para login com retorno ao URL original após re-autenticação.
- [ ] Não existe nenhum URL público acessível ao editor de fluxos sem sessão RID válida — verificável por teste com browser sem cookies de sessão.
- [ ] O redirect de login não apresenta ecrã em branco perceptível: qualquer estado transitório (loading spinner ou skeleton mínimo) é visível antes do redirect HTTP.

#### RF-002 — Endereço único e estável

- [ ] O editor de fluxos é acessível num único URL dentro do domínio da plataforma RID.
- [ ] Deep links para fluxos específicos funcionam após autenticação — o utilizador aterra no fluxo correcto, não na raiz do editor.
- [ ] Actualização de página dentro do editor não quebra a navegação — o utilizador permanece no mesmo fluxo ou estado do editor.
- [ ] O URL antigo (`:7861`) retorna 404 ou redirect permanente para o URL único em ambientes de staging e produção.

#### RF-003 — Página de indisponibilidade integrada

- [ ] Quando o serviço do editor está indisponível, o utilizador vê a página de erro com identidade visual RID — não um erro genérico de rede (502/503 do proxy).
- [ ] A página de erro apresenta: (a) título claro do problema, (b) mensagem explicativa em português, (c) pelo menos uma acção de recuperação ("Tentar novamente" e/ou "Voltar ao painel").
- [ ] A página de erro mantém a navegação da plataforma RID (header/nav) se aplicável ao layout da plataforma — o utilizador não perde o contexto da aplicação.
- [ ] 100% dos acessos ao editor em cenário de indisponibilidade do upstream mostram a página de erro RID — verificável por teste com upstream Langflow parado.

#### RF-004 — Isolamento por tenant

- [ ] Um utilizador autenticado num tenant não consegue aceder ao editor de fluxos de outro tenant — mesmo que conheça o URL ou ID do fluxo.
- [ ] O acesso ao editor valida o tenant activo da sessão antes de servir qualquer conteúdo do editor.

#### RF-005 — Auditoria de acesso

- [ ] Cada acesso bem sucedido ao editor de fluxos produz registo nos trilhos de auditoria da plataforma, contendo: tenant, utilizador (ID e email), timestamp e URL acedido.
- [ ] Registos de acesso ao editor aparecem no mesmo sistema de auditoria que outros recursos protegidos da plataforma — não num log separado.

---

### Usability criteria

- [ ] O fluxo de redirect para login e retorno ao editor ocorre em no máximo 2 passos perceptíveis para o utilizador: (1) página de login, (2) editor com o conteúdo destino — sem passos intermédios indefinidos.
- [ ] A página de login para a qual o utilizador é redirecionado é a mesma página de login padrão da plataforma RID — sem página de login alternativa ou genérica.
- [ ] A mensagem de erro na página de indisponibilidade usa linguagem clara em português (pt-BR), sem mensagens técnicas de proxy (ex.: "502 Bad Gateway") expostas ao utilizador final.
- [ ] A acção primária na página de erro ("Tentar novamente") recarrega o editor — não a página de login.
- [ ] O utilizador consegue distinguir visualmente entre: (a) editor a carregar, (b) editor indisponível, (c) sessão expirada — três estados distintos com feedback visual diferente.
- [ ] Deep links partilhados entre colegas funcionam sem instrução adicional — o utilizador não autenticado é conduzido pelo sistema até ao destino.

---

### Accessibility criteria

Nível exigido: **WCAG 2.1 AA**

#### Página de erro de indisponibilidade (RF-003)

- [ ] Contraste de texto/fundo >= 4.5:1 para texto normal; >= 3:1 para texto grande (18px+) e elementos de UI.
- [ ] A página tem um `<h1>` visível com o título do erro — hierarquia de headings correcta sem saltos.
- [ ] Todos os botões/links de acção têm nome acessível (`aria-label` ou texto visível) que descreve a acção.
- [ ] A página é totalmente navegável por teclado: Tab atinge todos os elementos interactivos, Enter activa botões e links.
- [ ] Ordem de foco segue a ordem visual de leitura (cima → baixo, esquerda → direita).
- [ ] O estado de erro é anunciado a leitores de ecrã — `role="alert"` ou equivalente quando o conteúdo é dinâmico.
- [ ] Ícone ou ilustração de erro tem `alt` descritivo ou `aria-hidden="true"` se decorativo.
- [ ] A página funciona sem JavaScript para o conteúdo estático de erro.

#### Fluxo de redirect (RF-001)

- [ ] Qualquer estado transitório usa `aria-live="polite"` ou `role="status"` para anunciar o estado a leitores de ecrã.
- [ ] O parâmetro `next` no URL de login não expõe dados sensíveis de sessão ou tokens no histórico do browser — apenas o path de destino.

---

### Responsive criteria

> Aplicam-se exclusivamente aos componentes RID criados por este feature: página de erro de indisponibilidade e eventuais estados transitórios durante o redirect. O editor Langflow não é redesenhado.

- [ ] A página de erro é legível e utilizável em viewport de 320px de largura mínima sem scroll horizontal.
- [ ] Botões de acção na página de erro têm touch target de mínimo 44x44px em viewports mobile (< 768px).
- [ ] Texto da página de erro é legível sem zoom em dispositivos mobile — tamanho mínimo de 16px para corpo de texto.
- [ ] Layout da página de erro adapta-se a viewports mobile: conteúdo em coluna única, sem elementos sobrepostos.
- [ ] Em desktop (>= 1024px), largura máxima de conteúdo definida para não esticar o layout.

---

### Performance criteria

- [ ] A página de erro de indisponibilidade é servida pelo servidor da plataforma RID (não pelo upstream Langflow) — tempo de resposta < 200ms independente do estado do Langflow.
- [ ] O redirect para login inicia em < 100ms após detecção de sessão ausente/expirada pelo gate de autenticação.
- [ ] A página de erro não carrega assets do Langflow (JS/CSS do editor) — bundle isolado para não depender do serviço indisponível.

---

## UI states inventory

### Estados do fluxo de autenticação (RF-001 / RF-002)

| Estado | Trigger | Comportamento esperado | Feedback visual |
|--------|---------|----------------------|-----------------|
| **Unauthenticated redirect** | Acesso sem sessão RID válida | Redirect 302 para login com `?next=<url-original>` | Loading mínimo antes do redirect |
| **Authenticated access** | Sessão RID válida presente | Editor serve o conteúdo; sem interrupção | Nenhum — transparente |
| **Session expired mid-use** | Sessão expira enquanto utilizador está no editor | Shell RID detecta 401 do gate e exibe overlay "Sessão expirada" com botão "Entrar novamente" → redireciona para /flows/ após re-autenticação | Overlay com botão CTA |
| **Post-login return** | Autenticação bem sucedida com parâmetro `next` | Redirect para URL original | Nenhum — transparente |
| **Deep link unauthenticated** | URL de fluxo específico sem sessão | Mesmo que "Unauthenticated redirect" — `next` inclui path completo | Loading mínimo antes do redirect |

### Estados da página de erro de indisponibilidade (RF-003)

| Estado | Trigger | Comportamento esperado | Feedback visual |
|--------|---------|----------------------|-----------------|
| **Langflow unavailable** | Upstream não responde (502/503/504) | Página de erro RID servida pelo proxy/app | Página de erro completa com identidade RID |
| **Retry success** | Utilizador clica "Tentar novamente" e Langflow recuperou | Editor carrega normalmente | Transição para editor |
| **Retry fail** | Utilizador clica "Tentar novamente" e Langflow ainda indisponível | Página de erro mantida | Feedback de retry (loading no botão) |
| **Return to dashboard** | Utilizador clica "Voltar ao painel" | Redirect para dashboard da plataforma RID | Navegação normal |

---

## PRD issues log

Os seguintes problemas foram identificados durante a validação UX. Não bloqueiam o Gate 1 mas **devem ser resolvidos antes de iniciar implementação (Gate 2/TRD)**.

| Severidade | Problema | Referência PRD | Recomendação |
|------------|----------|----------------|--------------|
| ~~HIGH~~ RESOLVED | Estado de sessão expirada durante uso do editor. | RF-001 | **Decisão:** overlay "Sessão expirada" com botão "Entrar novamente" → redireciona para /flows/ após re-autenticação. |
| ~~HIGH~~ RESOLVED | Estado transitório antes do redirect HTTP. | RF-001 | **Decisão:** redirect HTTP 302 directo — sem página intermédia. Flash de branco aceitável (imperceptível na prática). |
| MEDIUM | CTAs da página de erro não especificadas no PRD. "Orientação sobre o que fazer" é vago. | RF-003 | Definir as acções concretas antes do TRD — impacta contrato entre proxy e aplicação. CTAs propostas: "Tentar novamente" + "Voltar ao painel". |
| MEDIUM | Estado "utilizador autenticado sem permissão para o editor" não definido (authorization vs authentication). | RF-004 | Definir: o editor está disponível para todos os utilizadores autenticados no tenant, ou há roles específicas? Se há, qual é o ecrã de acesso negado? |
| MEDIUM | Preservação do URL de destino para URLs com query strings complexas ou fragmentos hash não validada. O router do Langflow pode usar hashes. | RF-002 | O TRD deve especificar o mecanismo de preservação do `next` param, incluindo encoding e limitações. |
| LOW | Comportamento do redirect quando URL de destino é a raiz do editor vs um fluxo específico. | RF-001, RF-002 | Documentar no TRD como edge case; não bloqueia o PRD. |
