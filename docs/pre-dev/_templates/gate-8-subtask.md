# ST-{NNN}-{NN}: {Nome da subtask}

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

<!-- Convenção de nomenclatura:
     ST-{NNN} = número da task pai (ex: T-001 → 001)
     {NN}     = número sequencial da subtask dentro da task (01, 02, 03...)
     Nome     = descrição curta e imperativa do que é feito (ex: "Adicionar serviço X ao docker-compose.yml") -->

**Goal:** {descricao-clara-do-objetivo-desta-subtask}

<!-- O Goal responde a: "Quando esta subtask estiver completa, o que exactamente existe/funciona que não existia antes?" -->

---

## Prerequisites

<!-- Comandos de verificação que confirmam que as condições necessárias estão satisfeitas
     ANTES de começar esta subtask. Cada verificação deve ter um "Expected output" claro. -->

```bash
# {descricao-verificacao-1}
{comando-de-verificacao-1}
# Expected output: {output-esperado}

# {descricao-verificacao-2}
{comando-de-verificacao-2}
# Expected output: {output-esperado}

# {descricao-verificacao-3}
{comando-de-verificacao-3}
# Expected output: {output-esperado}
```

---

## Files

<!-- Listar todos os ficheiros que serão criados, modificados, ou testados por esta subtask. -->

- **Create:** `{caminho/ficheiro-novo}` *(descrição do que contém)*
- **Modify:** `{caminho/ficheiro-existente}` *(descrição da alteração)*
- **Test:** `{caminho/ficheiro-de-teste}` *(descrição dos testes)*

---

## Steps

<!-- Estrutura TDD obrigatória:
     Step 1: Escrever o teste (RED) → Step 2: Verificar que falha → Step 3: Implementar → Step 4: Verificar que passa → Step 5: Commit
     Cada step deve ter o código exacto e o "Expected output" correspondente. -->

### Step 1: Escrever o teste de validação (RED)

<!-- Criar o teste ANTES de implementar. O teste deve falhar neste ponto (RED).
     Pode ser: script bash de validação, pytest, jest, ou outro mecanismo de teste. -->

```bash
{comando-para-criar-ou-escrever-o-teste}
```

<!-- Ou, para testes de ficheiro: -->

```{linguagem}
{codigo-do-teste}
```

Expected output:
```
FAIL: {descricao-do-que-falha-e-porque}
```

---

### Step 2: Verificar que o teste falha (confirmar RED)

```bash
{comando-para-executar-o-teste}
```

Expected output:
```
{output-de-falha-esperado}
```

---

### Step 3: Implementar (GREEN)

<!-- Implementação mínima para fazer os testes passarem.
     Incluir o código exacto ou instrução precisa sobre o que modificar. -->

{instrucao-de-implementacao}

```{linguagem}
{codigo-de-implementacao}
```

<!-- Se for modificação de ficheiro existente, indicar onde inserir: -->

Abrir `{caminho/ficheiro}` e {adicionar | modificar | remover} o seguinte {após | antes | em} `{referencia-de-localizacao}`:

```{linguagem}
{codigo-a-inserir-ou-modificar}
```

---

### Step 4: Verificar que os testes passam (GREEN)

```bash
{comando-para-executar-o-teste}
```

Expected output:
```
{output-de-sucesso-esperado}
ALL TESTS PASSED
```

---

### Step 5: Commit

<!-- Mensagem de commit seguindo o padrão do projecto (Conventional Commits). -->

```bash
cd {working-directory}
git add {lista-de-ficheiros-a-adicionar}
git commit -m "{tipo}({escopo}): {descricao-curta}"
```

<!-- Exemplos de tipos: feat | fix | chore | refactor | test | docs | ci
     Exemplos de mensagens:
     "feat(langflow-gate): add Traefik v3.3.6 service to docker-compose under langflow profile"
     "feat(auth): add /internal/auth-check/ endpoint with session and tenant validation"
     "test(auth): add unit tests for auth check endpoint session validation" -->

---

## Rollback

<!-- Comandos para desfazer as alterações desta subtask caso algo corra mal.
     Deve ser seguro executar mesmo que a subtask tenha completado parcialmente. -->

```bash
cd {working-directory}
git revert HEAD
# ou, se não houve commit:
git checkout -- {ficheiros-modificados}
{comandos-adicionais-de-cleanup-se-necessario}
```
