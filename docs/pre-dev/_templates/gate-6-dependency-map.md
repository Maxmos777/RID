---
feature: {feature-slug}
gate: 6
date: {date}
status: draft
standards_loaded: [{lista-de-standards-consultados}]
# Exemplo: [devops.md, frontend.md, backend.md]
---

# Dependency Map — {feature-slug}

> Referência arquitectural: [TRD Gate 3](./{feature-slug}/gate-3-trd.md) — {referencias-trd}
>
> Este documento regista **apenas o que este feature adiciona ou altera**. O stack existente
> ({lista-resumida-do-stack-existente}) não é re-documentado aqui.

---

## 1. Resumo de dependências novas

<!-- Tabela de alto nível com todas as dependências adicionadas ou alteradas por este feature.
     "Nova dependência?" = Sim se é uma nova biblioteca/serviço; Não se é reconfiguração de existente.
     "Novas dependências transitivas?" = Sim se adiciona libs transitivas relevantes. -->

| Tipo | Componente | Versão | Nova dependência? | Novas dependências transitivas? |
|------|-----------|--------|:-----------------:|:-------------------------------:|
| {tipo-1} | {componente-1} | {versao-1} | {Sim \| Não} | {Sim \| Não} |
| {tipo-2} | {componente-2} | {versao-2} | {Sim \| Não} | {Sim \| Não} |
| {tipo-3} | {componente-3} | — | {Sim \| Não} | {Sim \| Não} |

**Conclusão:** {resumo-das-dependencias-novas}

---

## 2. Infrastructure

<!-- Uma subsecção por nova dependência de infraestrutura (Docker, cloud services, etc.) -->

### 2.1 {nome-dependencia-infra} (dependência de infraestrutura {nova | alterada})

#### Identificação

| Atributo | Valor |
|----------|-------|
| Nome | {nome-completo} |
| Versão exacta | **{versao-exacta}** |
| Imagem / Package | `{imagem-ou-package}` |
| Licença | {licenca} |
| Repositório | {url-repositorio} |
| Origem | {url-origem} |

#### Justificação da versão

<!-- Explicar porquê esta versão específica foi escolhida:
     - É a versão estável mais recente?
     - Inclui patches de segurança específicos?
     - Há restrições de compatibilidade? -->

{justificativa-da-versao}

#### Configuração necessária

<!-- Documentar a configuração mínima necessária para este feature.
     Incluir snippets de código/YAML quando útil. -->

```yaml
{snippet-de-configuracao-relevante}
```

#### CVE e segurança

<!-- Documentar CVEs conhecidos e o estado de cada um. -->

| CVE | Severidade | Estado | Notas |
|-----|-----------|--------|-------|
| {cve-1} | {severidade} | {Fixed in vX.Y.Z \| Mitigated \| Accepted} | {nota} |
| {cve-2} | {severidade} | {Fixed in vX.Y.Z} | {nota} |

#### Alternativas consideradas e rejeitadas

| Alternativa | Motivo da rejeição |
|-------------|-------------------|
| {alternativa-1} | {motivo} |
| {alternativa-2} | {motivo} |

---

## 3. Backend

<!-- Dependências Python/backend adicionadas ou alteradas por este feature. -->

### 3.1 {nome-dependencia-backend}

<!-- Se não há novas dependências backend (apenas reconfiguração), indicar explicitamente. -->

| Package | Version | Purpose | Rationale | License | CVE status |
|---------|---------|---------|-----------|---------|------------|
| {package-1} | {version} | {purpose} | {rationale} | {license} | {cve-status} |

> {nota-sobre-dependencias-backend-se-aplicavel}

---

## 4. Frontend

<!-- Dependências npm/frontend adicionadas ou alteradas por este feature. -->

### 4.1 {nome-dependencia-frontend}

<!-- Se não há novas dependências frontend, indicar explicitamente. -->

| Package | Version | Purpose | Rationale | License | CVE status |
|---------|---------|---------|-----------|---------|------------|
| {package-1} | {version} | {purpose} | {rationale} | {license} | {cve-status} |

> {nota-sobre-dependencias-frontend-se-aplicavel}

---

## 5. Dev tools

<!-- Ferramentas de desenvolvimento adicionadas (test runners, linters, etc.).
     Não incluir ferramentas que já existem no projecto. -->

### 5.1 {nome-dev-tool}

| Package | Version | Purpose | Rationale | License | CVE status |
|---------|---------|---------|-----------|---------|------------|
| {package-1} | {version} | {purpose} | {rationale} | {license} | {cve-status} |

---

## 6. Configuração e variáveis de ambiente

<!-- Documentar variáveis de ambiente novas ou alteradas por este feature.
     Incluir: nome, valor esperado, onde é usada, se é segredo. -->

| Variável | Valor exemplo | Serviço | Segredo? | Notas |
|----------|--------------|---------|:--------:|-------|
| `{VAR_1}` | `{valor-exemplo}` | {servico} | {Sim \| Não} | {nota} |
| `{VAR_2}` | `{valor-exemplo}` | {servico} | {Sim \| Não} | {nota} |
| `{VAR_3}` | `{valor-exemplo}` | {servico} | {Sim \| Não} | {nota} |

> Todas as variáveis acima devem ser adicionadas ao `.env.example`.

---

## 7. Alterações em ficheiros de configuração existentes

<!-- Ficheiros existentes que precisam ser modificados por este feature
     (ex: docker-compose.yml, settings.py, nginx.conf). -->

| Ficheiro | Tipo de alteração | Descrição |
|----------|------------------|-----------|
| `{ficheiro-1}` | {Adição \| Remoção \| Modificação} | {descricao} |
| `{ficheiro-2}` | {Adição \| Remoção \| Modificação} | {descricao} |

---

## 8. Gate 6 — Validation Checklist

| Verificação | Estado |
|-------------|--------|
| [ ] Todas as novas dependências identificadas e justificadas | PENDENTE |
| [ ] Versões exactas especificadas (sem `latest`) | PENDENTE |
| [ ] CVE check realizado para todas as novas dependências | PENDENTE |
| [ ] Licenças verificadas (sem GPL incompatível com licença do projecto) | PENDENTE |
| [ ] Alternativas consideradas e rejeitadas documentadas | PENDENTE |
| [ ] Variáveis de ambiente documentadas e `.env.example` actualizado | PENDENTE |
| [ ] Alterações em ficheiros de configuração listadas | PENDENTE |

**Resultado: {PASS | FAIL} — {justificativa}**
