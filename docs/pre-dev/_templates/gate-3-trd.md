---
feature: {feature-slug}
gate: 3
date: {date}
status: draft
# Valores possíveis: draft | review | approved
topology:
  structure: {structure}
  # Valores possíveis: monorepo | multi-repo
  target_repo: {target-repo-path}
  reference_repo: {reference-repo-path}
  scope: {scope}
  # Valores possíveis: fullstack | backend | frontend | infra
  api_pattern: {api-pattern}
  # Valores possíveis: bff | rest | graphql | rpc
  arch_style: {arch-style}
  # Exemplos: modular_monolith | microservices | monolith | serverless
  edge: {edge-type}
  # Exemplos: reverse_proxy | cdn | api_gateway | none
  edge_router: {edge-router}
  # Exemplos: traefik | nginx | caddy | none
---

# TRD — {feature-name}

## Resumo executivo

<!-- 2-4 frases: qual a decisão arquitectural central, quais componentes são criados/modificados,
     e qual o resultado do perímetro técnico estabelecido. -->

{resumo-executivo}

---

## 1. Contexto e decisões herdadas

### 1.1 Requisitos funcionais herdados do PRD (Gate 1)

<!-- Mapear cada RF do PRD para o critério de aceitação técnico neste TRD.
     O critério técnico deve ser verificável (ex: "nenhum path X responde sem Y"). -->

| ID | Requisito | Critério de aceitação técnico |
|----|-----------|------------------------------|
| RF-001 | {nome-requisito-1} | {criterio-tecnico-1} |
| RF-002 | {nome-requisito-2} | {criterio-tecnico-2} |
| RF-003 | {nome-requisito-3} | {criterio-tecnico-3} |
| RF-004 | {nome-requisito-4} | {criterio-tecnico-4} |
| RF-005 | {nome-requisito-5} | {criterio-tecnico-5} |

### 1.2 Decisões de design herdadas (Gate 1.5 — Design Validation)

<!-- Mapear cada DD do Gate 1.5 para o impacto técnico concreto neste TRD. -->

| ID | Decisão | Impacto técnico |
|----|---------|----------------|
| DD-001 | {descricao-decisao-1} | {impacto-tecnico-1} |
| DD-002 | {descricao-decisao-2} | {impacto-tecnico-2} |
| DD-003 | {descricao-decisao-3} | {impacto-tecnico-3} |

### 1.3 Estilo arquitectural

<!-- Declarar explicitamente o estilo arquitectural escolhido e a justificativa.
     Nomear os componentes principais e as suas responsabilidades a alto nível. -->

**{arch-style-descritivo}**

{descricao-do-estilo-arquitectural-e-justificativa}

---

## 2. Componentes

<!-- Um componente por secção. Cada componente deve ter:
     - Responsabilidade clara e única
     - Comportamento documentado (tabelas, fluxos, ou lógica pseudocode)
     - Configuração necessária
     - Notas/limitações conhecidas -->

### Componente 1 — {nome-componente-1}

**Responsabilidade:** {responsabilidade-unica}

<!-- Documentar o comportamento por estado/resposta quando relevante -->

**Comportamento:**

| {condicao} | {accao} |
|------------|---------|
| {caso-1} | {accao-1} |
| {caso-2} | {accao-2} |
| {caso-3} | {accao-3} |

**Configuração necessária:**
- {config-item-1}
- {config-item-2}
- {config-item-3}

> {nota-ou-limitacao-conhecida}

---

### Componente 2 — {nome-componente-2}

**Responsabilidade:** {responsabilidade-unica}

**Localização:** {onde-vive-este-componente}

**Lógica:**

```
{pseudocode-ou-descricao-da-logica}
```

**Contrato de resposta:**

| Código | Condição |
|--------|----------|
| {codigo-1} | {condicao-1} |
| {codigo-2} | {condicao-2} |
| {codigo-3} | {condicao-3} |

**Performance target:** {p95-ou-sla-target}

---

### Componente 3 — {nome-componente-3}

**Responsabilidade:** {responsabilidade-unica}

**Localização:** {onde-vive-este-componente}

**Comportamento:**

{descricao-do-comportamento}

**Implementação ({refs-decisoes-design}):**
- {detalhe-implementacao-1}
- {detalhe-implementacao-2}

---

### Componente 4 — {nome-componente-4}

**Responsabilidade:** {responsabilidade-unica}

**Trigger:** {o-que-dispara-este-componente}

**Requisitos:**
- {requisito-1}
- {requisito-2}

**Performance target:** {target}

---

### Componente 5 — {nome-componente-5}

<!-- Pode ser um componente existente que NÃO é modificado, mas cujo comportamento
     deve ser documentado como constraint. -->

**Responsabilidade:** {responsabilidade-unica}

**Restrições de exposição / configuração:**
- {restricao-1}
- {restricao-2}

**Configuração actual a alterar:**
- {alteracao-necessaria}

---

## 3. Modelo de segurança

### 3.1 Threat model

<!-- Documentar as ameaças relevantes e as suas mitigações.
     Focar nas ameaças específicas deste feature, não no threat model completo da aplicação. -->

| Ameaça | Mitigação |
|--------|-----------|
| {ameaca-1} | {mitigacao-1} |
| {ameaca-2} | {mitigacao-2} |
| {ameaca-3} | {mitigacao-3} |
| {ameaca-4} | {mitigacao-4} |

### 3.2 OWASP relevante

<!-- Referenciar categorias OWASP Top 10 relevantes para este feature e como são mitigadas. -->

- **{owasp-categoria-1}:** {como-e-mitigado}
- **{owasp-categoria-2}:** {como-e-mitigado}

### 3.3 {validacao-critica-de-input}

<!-- Documentar lógica de validação crítica de segurança (ex: validação de `next` URL,
     sanitização de inputs, verificação de tokens). Incluir pseudocode ou código real. -->

```python
# {descricao-da-logica-de-validacao}
def {funcao_de_validacao}({parametro}: str) -> bool:
    # {explicacao-da-logica}
    return (
        {condicao-1}
        and {condicao-2}
        and {condicao-3}
    )
```

---

## 4. Integration Patterns

### 4.1 Padrão: {nome-padrao}

<!-- Descrever o padrão de integração adoptado (BFF, REST, event-driven, etc.)
     e como os componentes se encaixam nele. -->

{descricao-do-padrao}

### 4.2 Data flow

<!-- Diagrama ASCII do fluxo de dados entre componentes.
     Usar setas (→, ←, ↑, ↓, ▼) para indicar direcção. -->

```
{actor-ou-origem}
    │
    ▼
{componente-1}  ({descricao-da-accao})
    │                    │
    │                    ▼
    │         {componente-2}
    │                    │
    │         {codigo} ◄─┘
    ▼
{componente-destino}
```

### 4.3 {protocolo-especifico}

<!-- Documentar comportamento de protocolos especiais (WebSocket, gRPC, SSE, etc.) quando aplicável. -->

- {detalhe-1}
- {detalhe-2}
- {detalhe-3-limitacao-conhecida}

---

## 5. Backend Integration Points

<!-- Tabela mapeando features do PRD para componentes técnicos, sistemas integrados e direcção do fluxo. -->

| Feature | Componente | Sistema integrado | Direcção |
|---------|-----------|------------------|---------|
| {feature-id-1} | {componente-1} | {sistema-1} | {Leitura \| Escrita \| Bidirecional} |
| {feature-id-2} | {componente-2} | {sistema-2} | {Leitura \| Escrita} |
| {feature-id-3} | {componente-3} | {sistema-3} | {Escrita async} |

### 5.1 Sistemas externos ao escopo (dependências existentes)

<!-- Sistemas que este feature usa mas não modifica. -->

| Sistema | Papel | Interacção |
|---------|-------|-----------|
| {sistema-1} | {papel} | {como-interage} |
| {sistema-2} | {papel} | {como-interage} |

### 5.2 Relação com componentes existentes

<!-- Clarificar explicitamente como este feature se relaciona com bridges, serviços
     ou padrões já existentes que possam gerar confusão. -->

{descricao-da-relacao-com-componentes-existentes}

---

## 6. Topologia de deployment (lógica)

<!-- Diagrama ASCII da topologia lógica de deployment.
     Não mostrar IPs ou detalhes de infra — apenas componentes e redes lógicas. -->

```
{origem-do-trafego}
    │
    ▼
[{componente-edge}]  ← {descricao-do-papel-na-rede}
    │           │
    │           │
    ▼           ▼
[{componente-a}]  [{componente-b}]
    ↑
[{componente-auth}]
    ↑
[{componente-aplicacao}]
```

**{rede-interna}:** {descricao-das-restricoes-de-rede}

**Alteração necessária em {ficheiro-de-infra}:**
- {alteracao-1}
- {alteracao-2}

---

## 7. Issues técnicas conhecidas

<!-- Documentar limitações conhecidas, comportamentos inesperados aceitáveis no MVP,
     e decisões deliberadas que trocam correctude por simplicidade. -->

### 7.1 {nome-da-issue-1}

{descricao-da-issue-e-porque-e-aceitavel-no-mvp}

### 7.2 {nome-da-issue-2}

{descricao-da-issue}

### 7.3 {nome-da-issue-3} (limitação conhecida do MVP)

{descricao-da-limitacao}

**Comportamento esperado:** {o-que-o-utilizador-vera}

{descricao-da-mitigacao-parcial}

---

### 7.4 {nome-da-issue-4}

{descricao-da-issue}

{configuracao-necessaria-ou-workaround}

---

## 8. Targets de performance e qualidade

| Componente | Métrica | Target |
|-----------|---------|--------|
| {componente-1} | {metrica-1} | {target-1} |
| {componente-2} | {metrica-2} | {target-2} |
| {componente-3} | {metrica-3} | {target-3} |

### 8.1 Qualidade

<!-- Listar os cenários de teste obrigatórios para Gate 9 (delivery). -->

- {cenario-teste-1}
- {cenario-teste-2}
- {cenario-teste-3}
- {cenario-teste-4}

---

## 9. Riscos técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| {risco-1} | {probabilidade} | {impacto} | {mitigacao} |
| {risco-2} | {probabilidade} | {impacto} | {mitigacao} |
| {risco-3} | {probabilidade} | {impacto} | {mitigacao} |

---

## 10. Gate 3 — Validation Checklist

| Categoria | Verificação | Estado |
|-----------|-------------|--------|
| **Rastreabilidade** | Todos os RF mapeados para componentes | PENDENTE |
| **Rastreabilidade** | Todas as decisões de design (DD) endereçadas | PENDENTE |
| **Arquitectura** | Estilo arquitectural declarado | PENDENTE |
| **Componentes** | {N} componentes descritos com responsabilidades e contratos | PENDENTE |
| **Segurança** | Threat model documentado | PENDENTE |
| **Segurança** | OWASP relevante endereçado | PENDENTE |
| **Integração** | Padrão de integração declarado e data flow documentado | PENDENTE |
| **Integração** | Backend integration points por feature (tabela) | PENDENTE |
| **Deployment** | Topologia lógica documentada | PENDENTE |
| **Deployment** | Alterações necessárias na infra identificadas | PENDENTE |
| **Performance** | Targets de latência definidos para componentes críticos | PENDENTE |
| **Qualidade** | Critérios de teste especificados | PENDENTE |
| **Issues técnicas** | Limitações conhecidas documentadas | PENDENTE |
| **Riscos** | Tabela de riscos com probabilidade, impacto e mitigação | PENDENTE |
| **Abstracção** | Arquitectura descrita de forma abstracta; escolhas concretas em ADR | PENDENTE |
| **ADR** | ADR criado para decisão arquitectural principal | PENDENTE |

**Resultado: {PASS | FAIL} — {justificativa}**
