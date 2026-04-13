---
feature: rid-langflow-single-entry
gate: 1
date: 2026-04-05
status: draft
confidence: 85
topology:
  structure: multi-repo
  target_repo: /home/RID
  reference_repo: /home/RockItDown
---

# PRD — Entrada única autenticada para o editor de fluxos (RID)

## Resumo executivo

Utilizadores do RID conseguem aceder ao editor de fluxos de automação diretamente, sem passar pelo sistema de identidade da plataforma, contornando auditoria, controlo de sessão e isolamento por tenant. Este produto define os requisitos para que **toda e qualquer entrada na interface do editor de fluxos passe obrigatoriamente pelo perímetro de autenticação do RID**, garantindo conformidade, rastreabilidade e uma experiência de acesso coerente para todos os perfis de utilizador.

---

## Problema

Actualmente existe uma segunda entrada pública para o editor de fluxos, paralela à entrada da plataforma RID. Qualquer utilizador — autenticado ou não na plataforma — pode aceder directamente ao editor sem que a identidade seja verificada pelo sistema de controlo de acesso do RID.

**Impacto:**
- Trilhos de auditoria incompletos: acesso ao editor não aparece nos registos de sessão da plataforma.
- Risco de conformidade: dados e fluxos de tenant expostos fora do perímetro de identidade acordado.
- Confusão operacional: dois endereços distintos para a mesma ferramenta geram tickets de suporte e erros de bookmark.
- Isolamento por tenant comprometido: sem gate de identidade, a separação entre tenants depende unicamente de controlos internos do editor, sem a camada de autorização da plataforma.

**Evidência (pesquisa Gate 0 — `research.md`):**
- Padrão de referência interno (RockItDown) já resolve este problema servindo o editor **atrás** do login da plataforma; o RID diverge neste ponto.
- Pesquisa de produto identificou duas personas afectadas diretamente (ver abaixo) e documentou o padrão de mercado de ferramentas analíticas/BI embutidas atrás do SSO da aplicação principal.

---

## Personas

### 1. Administradora de Plataforma (enterprise)

**Papel:** Gere acessos, conformidade e auditoria de uma ou mais organizações no RID.

**Objetivos:**
- Garantir que todos os acessos a ferramentas sensíveis passam pelo IdP e produzem registos auditáveis.
- Reportar a equipas de compliance que nenhum recurso da plataforma está exposto fora do perímetro acordado.
- Resolver incidentes de acesso sem ambiguidade sobre qual URL foi usada.

**Frustrações actuais:**
- Relatórios de acesso ao editor de fluxos estão incompletos porque sessões directas ao editor não passam pelo sistema de identidade da plataforma.
- Não há como garantir formalmente que utilizadores não autorizados não acederam ao editor.
- Dois endereços para a mesma ferramenta criam inconsistência nos registos e nos procedimentos de onboarding.

---

### 2. Builder de Fluxos

**Papel:** Cria e mantém fluxos de automação para a sua organização no RID.

**Objetivos:**
- Aceder ao editor de fluxos de forma rápida e previsível, a partir da plataforma onde já está autenticado.
- Partilhar links directos para fluxos específicos com colegas sem que estes precisem de saber endereços alternativos.
- Trabalhar sem interrupções de sessão inesperadas.

**Frustrações actuais:**
- Dois endereços distintos para a mesma ferramenta geram confusão sobre qual usar e qual bookmarkar.
- Ao aceder pelo endereço alternativo, a sessão da plataforma não é reconhecida, forçando autenticação dupla ou comportamentos inesperados.
- Links partilhados para fluxos específicos podem falhar dependendo do endereço de origem.

---

## Requisitos de produto (o quê, não o como)

### RF-001 — Perímetro único de autenticação

Toda e qualquer entrada na interface do editor de fluxos requer autenticação prévia na plataforma RID. Utilizadores não autenticados são redirecionados para o fluxo de login da plataforma; após autenticação, são encaminhados para o destino original.

**Valor:** Fecha a segunda entrada pública; unifica auditoria.
**Critério de aceitação:** Não existe nenhum endereço público acessível ao editor de fluxos sem sessão RID válida.

---

### RF-002 — Endereço único e estável para o editor

O editor de fluxos é acessível num único endereço dentro do domínio da plataforma RID. O mesmo endereço funciona para acesso directo, deep links para fluxos específicos, partilha entre utilizadores e actualização de página.

**Valor:** Elimina confusão entre duas origens; suporte e onboarding com um único URL a documentar.
**Critério de aceitação:** Links directos para fluxos específicos funcionam no mesmo endereço após autenticação; a actualização de página não quebra a navegação.

---

### RF-003 — Página de indisponibilidade integrada

Quando o serviço do editor de fluxos estiver indisponível, o utilizador vê uma página de erro com identidade visual da plataforma RID, com mensagem clara sobre o estado e orientação sobre o que fazer.

**Valor:** Mantém a coerência da experiência mesmo em falha; reduz tickets de suporte por mensagens de erro genéricas do proxy.
**Critério de aceitação:** Em cenário de indisponibilidade do editor, 100% dos acessos mostram a página de erro RID (não um erro genérico de rede).

---

### RF-004 — Isolamento por tenant

O acesso ao editor respeita os limites de tenant da plataforma. Um utilizador autenticado num tenant não acede aos fluxos de outro tenant.

**Valor:** Conformidade e isolamento de dados entre clientes enterprise.
**Critério de aceitação:** Utilizadores de tenants distintos não conseguem visualizar nem aceder a fluxos de outros tenants.

---

### RF-005 — Auditoria de acesso alinhada ao perímetro RID

Cada acesso ao editor de fluxos produz registo rastreável associado à sessão do utilizador na plataforma, incluindo tenant, utilizador e momento de acesso.

**Valor:** Permite a administradoras reportar acessos com completude e exactidão.
**Critério de aceitação:** Registos de acesso ao editor aparecem nos mesmos trilhos de auditoria que outros recursos da plataforma.

---

## Métricas de sucesso

| Métrica | Baseline | Alvo | Prazo |
|---------|----------|------|-------|
| Acessos ao editor sem sessão RID (%) | >0% (não monitorado) | 0% | Após deploy |
| Tickets de suporte sobre "qual URL usar para o editor" | Não medido | 0/mês | 30 dias pós-deploy |
| Acessos ao editor que produzem registo de auditoria (%) | Parcial | 100% | Após deploy |
| Página de erro RID exibida em indisponibilidade (%) | 0% (erro genérico) | 100% | Após deploy |
| Satisfação de builders com acesso ao editor (CSAT) | Não medido | ≥4/5 | 60 dias pós-deploy |

---

## Escopo

### Incluído

- Única entrada autenticada para o editor de fluxos dentro do domínio da plataforma
- Redirecionamento de utilizadores não autenticados para o login da plataforma, com retorno ao destino original
- Suporte a deep links (links directos para fluxos específicos) dentro do mesmo endereço
- Página de erro com identidade visual RID quando o editor estiver indisponível
- Isolamento de acesso por tenant
- Auditoria de acesso integrada ao perímetro da plataforma
- Suporte a actualizações de página e partilha de URL no mesmo endereço

### Excluído (explicitamente)

- Redesenho da interface do editor de fluxos
- Novas funcionalidades de criação ou execução de fluxos
- Provisioning self-service de editor de fluxos por tenant
- Instâncias separadas do editor por tenant (avaliação futura)
- Interface do editor servida directamente pelo servidor de aplicação da plataforma (paridade total com RockItDown — fase 2 futura)
- Dashboard de negócio para métricas do editor (infraestrutura de plataforma — monitorização via stack de observabilidade existente)

---

## Perguntas abertas

Todas as perguntas técnicas de implementação (topologia de proxy, protocolo WebSocket, configuração de CORS, sessão Django vs FastAPI) são deliberadamente excluídas deste documento e serão resolvidas no TRD (Gate 3).

---

## Pressupostos de negócio

- A plataforma RID tem um sistema de identidade e sessão em produção para todos os tenants.
- O isolamento por tenant via RBAC/credenciais por tenant é suficiente para os requisitos de conformidade actuais dos clientes enterprise (separação física por instância é fase 2).
- Utilizadores existentes que acediam pelo endereço alternativo serão comunicados da mudança antes do deploy (gestão de mudança fora do escopo técnico).

---

## Dependências de negócio

- Comunicação aos utilizadores existentes sobre mudança de endereço de acesso.
- Alinhamento com equipa de compliance sobre definição de "registo de auditoria" aceitável para relatórios enterprise.

---

## Referências

- Pesquisa Gate 0: `docs/pre-dev/research.md` (RID) / `docs/pre-dev/rid-langflow-single-entry/gate-0-research.md` (RockItDown)
- Brainstorm Ring: `docs/pre-dev/brainstorm-rid-langflow-single-entry-ring.md`
- Padrão de referência: `/home/RockItDown/src/rocklangflow/` — implementação existente de editor atrás de login
