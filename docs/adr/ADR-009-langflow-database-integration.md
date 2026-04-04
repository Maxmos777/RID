# ADR-009 — Integração Django ↔ Langflow: Base de Dados Partilhada e Multi-tenancy via Workspaces

**Data:** 2026-04-04
**Estado:** Accepted
**Autores:** RID Platform Team
**Revisores:** Tech Lead, Backend Engineer
**Contexto de código:** `docker-compose.yml`, `backend/apps/tenants/models.py`, `backend/api/services/langflow_workspace.py`, `backend/apps/tenants/langflow_pg_bootstrap.py`, `backend/apps/tenants/management/commands/ensure_langflow_schema.py`, `docs/plans/2026-04-04-langflow-database-integration.md`

---

## Contexto

O RID Platform integra o Langflow 1.8.3 como motor de execução de fluxos LLM. O Langflow tem o seu próprio servidor e a sua própria camada de persistência (SQLAlchemy + Alembic), completamente separada do Django ORM.

O `docker-compose.yml` actual não define `LANGFLOW_DATABASE_URL`, pelo que o Langflow usa **SQLite por defeito, armazenado dentro do container sem volume**. Cada `docker compose down` apaga silenciosamente todos os flows, utilizadores Langflow e API keys — corrompendo os `langflow_user_id` e `langflow_api_key` guardados em `TenantUser`. Este é um bug crítico (P0) que torna o ambiente de desenvolvimento inutilizável após qualquer restart.

Para além do bug de persistência, existe uma lacuna de multi-tenancy: o modelo `Customer` não tem `langflow_workspace_id`. O Langflow usa workspaces para isolamento de dados; sem este mapeamento, todos os utilizadores partilham o workspace default do superuser e os flows de um tenant são visíveis para outros tenants.

No projecto legado (RockItDown), a dor operacional foi descrita como "dois bancos de dados a manter". A análise revelou que o problema real não era a existência de dois schemas de dados distintos — era ter dois **ciclos de vida operacionais independentes**: backup, restore, migração e monitorização em separado, com ORMs incompatíveis que tornavam qualquer tentativa de unificação mais cara do que o problema que resolvia.

## Decisão

### 1. Langflow usa PostgreSQL na mesma instância **e na mesma database** que o Django

Configuramos `LANGFLOW_DATABASE_URL` para a database `rid` (a mesma que `POSTGRES_DB`), com um **role PostgreSQL dedicado** `langflow` cujo `search_path` é exclusivamente `langflow` (sem `public`). O Alembic do Langflow cria todas as tabelas no schema `langflow`; o Django continua a usar `public` e os schemas de tenant via `django-tenants`, sem `TENANT_SCHEMA_EXCLUDE_LIST` para `langflow` porque o ORM Django nunca referencia esse schema.

> **Nota (2026-04-04):** o `search_path` inicial incluía `public`, o que causava o Alembic a detectar tabelas Django como "extra" e falhar no arranque com "mismatch between models and database". Corrigido restringindo `search_path` a `langflow` apenas, e adicionando `options=-csearch_path=langflow` na `LANGFLOW_DATABASE_URL`.

```
PostgreSQL server (rid-db)
  └── database: rid
        ├── schema public (+ tenant_*)  ← Django (django-tenants)
        └── schema langflow             ← Langflow (Alembic), role `langflow` + search_path
```

O DDL de bootstrap (role, schema, privilégios) é gerido via **management command Django** `ensure_langflow_schema` (módulo `langflow_pg_bootstrap.py`), executado pelo serviço one-shot `langflow-pg-bootstrap` no compose antes do `langflow`. Esta abordagem substitui o script de shell `/docker-entrypoint-initdb.d/` (agora no-op em `infra/docker/01-langflow-schema.sh`) e é idempotente — pode ser re-executada em qualquer estado do volume.

### 2. Multi-tenancy via workspaces Langflow

Adicionamos `langflow_workspace_id` ao modelo `Customer`. No momento do provisionamento de um novo tenant, um signal Django (`post_save` em `Customer`) chama a API REST do Langflow para criar um workspace dedicado e persiste o ID resultante.

```
Django Customer (acme)  →  Langflow Workspace (rid-acme, uuid)
Django TenantUser       →  Langflow User, membro do workspace do seu tenant
```

### 3. Django não acede directamente à database Langflow

Toda a comunicação Django → Langflow é via REST API (httpx). O Django ORM é a única fonte de verdade para os dados do Django. Para visibilidade de execuções Langflow no Django (billing, audit, reporting), usa-se webhook-driven sync na Fase 3 (M3+): Langflow envia eventos de execução → endpoint Django → Celery task → upsert em modelos Django espelho.

```
Arquitectura de comunicação:
  Django → Langflow:  REST API (httpx, async)
  Langflow → Django:  Webhooks → Celery (M3+)
  Django ORM:         nunca usa o schema `langflow` (nem o role `langflow`)
  SQLAlchemy:         nunca importado no código RID
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| SQLite com volume persistente | Não é production-ready sob carga concorrente (WAL file locking); não resolve o problema operacional de dois stores independentes. Aceitável apenas como hotfix temporário de desenvolvimento. |
| Duas databases no mesmo servidor (`rid` + `langflow`) | Foi a opção intermédia; mantinha `pg_dump` com duas DB no mesmo cluster. A variante **actual** (uma DB + schema `langflow` + role dedicado) reduz ainda mais superfície operacional e satisfaz o requisito de “um só banco com esquemas distintos”, com isolamento garantido por role e `search_path`. |
| Unificar ORMs (expor SQLAlchemy no Django) | Acoplamento total aos internos do Langflow, que mudam em cada minor release. Inviável em upgrades. Contradiz o princípio de integração via API oficial (ADR-008). |
| Dois servidores PostgreSQL independentes | Reproduz exactamente o problema do legado: dois ciclos de vida operacionais independentes. Nenhum benefício sobre a decisão adoptada; overhead máximo. |
| Acesso directo à database Langflow a partir do Django | Coupling a SQLAlchemy models internos do Langflow. Qualquer upgrade do Langflow pode alterar o schema sem aviso. Impossível manter correctamente com `django-tenants`. |

## Consequências Positivas

- O bug crítico de perda de dados (SQLite sem volume) é eliminado — dados Langflow persistem entre restarts.
- Único servidor PostgreSQL e **uma única database lógica** para dados da plataforma: `pg_dump` / backup de `rid` inclui Django e Langflow; restore e monitorização unificados.
- Zero interferência entre Alembic (Langflow) e Django: o Langflow liga-se como role `langflow` com tabelas no schema `langflow`; o Django usa o role `rid` e não referencia esse schema.
- Isolamento multi-tenant correcto: cada tenant tem o seu workspace Langflow; flows de um tenant não são visíveis para outro.
- O Django ORM permanece a única fonte de verdade para dados do Django. Sem SQLAlchemy no código RID — a equipa não precisa de aprender nem manter dois ORMs.
- Upgrade do Langflow = alterar a tag + verificar API de workspaces + re-testar bridge. O Django ORM não é afectado.

## Consequências Negativas / Trade-offs

- **Bootstrap via management command (idempotente):** O serviço `langflow-pg-bootstrap` corre `ensure_langflow_schema` em cada `up`, garantindo que o role/schema existe. O script shell `01-langflow-schema.sh` foi mantido como no-op em `infra/docker/` por compatibilidade histórica.
- **Password URL:** `LANGFLOW_DATABASE_URL` usa o role `langflow`; em produção usar palavra-passe forte e, se necessário, encoding na URL.
- **API de workspaces usa `/api/v1/projects/` no Langflow 1.8.3:** O Langflow 1.8.3 usa `projects` como conceito de workspace (não `workspaces/` nem `folders/`). Verificado via swagger em `http://localhost:7861/docs`. O serviço `langflow_workspace.py` isola este detalhe — mudança de endpoint afecta apenas 1 ficheiro.
- **Provisioning de workspace falha silenciosamente:** O signal `post_save` captura excepções e loga sem propagar, para não bloquear a criação do tenant. Um tenant pode ser criado sem `langflow_workspace_id`. Mitigação: health check de tenant no painel de admin; alerta de monitorização para erros de provisioning.
- **Tenant context em FastAPI routes (M2 dependency):** O `add_user_to_workspace` no auto-login bridge requer o `langflow_workspace_id` do tenant actual, que por sua vez requer resolver o tenant a partir do request. Este mecanismo faz parte do M2 (FastAPI API Layer). Até M2, o utilizador fica no workspace default e o `add_user_to_workspace` é chamado apenas quando o contexto de tenant estiver disponível.
- **Webhook sync eventual (M3+):** Até à Fase 3, o Django não tem visibilidade directa das execuções Langflow para billing/reporting. Se billing por uso for necessário antes de M3, requer solução temporária (polling ou sincronização manual).

## Compliance

```bash
# 1. Langflow usa PostgreSQL (não SQLite)
grep "LANGFLOW_DATABASE_URL" /home/RID/docker-compose.yml | grep -q "postgresql"
# Expected: exit 0

# 2. Langflow tem depends_on: db
grep -A 10 "langflow:" /home/RID/docker-compose.yml | grep -q "db"
# Expected: exit 0

# 3. Customer tem langflow_workspace_id
grep -q "langflow_workspace_id" /home/RID/backend/apps/tenants/models.py
# Expected: exit 0

# 4. Sem import SQLAlchemy no código RID (o Django nunca acede à DB Langflow directamente)
grep -r "import sqlalchemy" /home/RID/backend/apps/ /home/RID/backend/api/
# Expected: sem resultados

# 5. Bootstrap Langflow em Python (fonte única)
test -f /home/RID/backend/apps/tenants/langflow_pg_bootstrap.py
test -f /home/RID/backend/apps/tenants/management/commands/ensure_langflow_schema.py
grep -q langflow-pg-bootstrap /home/RID/docker-compose.yml
# Expected: exit 0
```

## Referências

- `docker-compose.yml` — serviço `langflow` e `db`
- `backend/apps/tenants/models.py` — modelo `Customer` (campo `langflow_workspace_id` a adicionar)
- `backend/apps/accounts/models.py` — modelo `TenantUser` (campos `langflow_user_id`, `langflow_api_key`)
- `backend/api/services/langflow_client.py` — bridge HTTP existente
- `backend/api/routers/langflow_auth.py` — auto-login bridge (a actualizar na Fase 2)
- `backend/api/services/langflow_workspace.py` — serviço de provisioning (implementado)
- `backend/apps/tenants/langflow_pg_bootstrap.py` — DDL idempotente (role, schema, grants)
- `backend/apps/tenants/management/commands/ensure_langflow_schema.py` — management command
- `docs/plans/2026-04-04-langflow-database-integration.md` — plano de implementação detalhado
- ADR-003 — Arquitectura híbrida Django + FastAPI
- ADR-008 — Personalização do Frontend Langflow (integração via API REST oficial)

---

## Apêndice — Bugs detectados e resolvidos

### IB-001 — Langflow usava SQLite sem volume no docker-compose.yml ✅ RESOLVIDO

**Descoberto durante:** brainstorm de arquitectura de integração (2026-04-04).

**Sintoma:** após `docker compose down && docker compose up`, o health check Langflow retornava `{"status":"ok"}` mas todos os flows, utilizadores e API keys tinham sido apagados.

**Causa:** `docker-compose.yml` não definia `LANGFLOW_DATABASE_URL` → Langflow usava SQLite em `/root/.langflow/langflow.db` dentro do container → sem volume, o ficheiro era efémero.

**Correcção aplicada:** `LANGFLOW_DATABASE_URL=postgresql://langflow:...@db:5432/rid?options=-csearch_path=langflow` + serviço `langflow-pg-bootstrap` (management command `ensure_langflow_schema`) + `depends_on: db`.

### IB-002 — Alembic detectava tabelas Django como "extra" e falhava no arranque ✅ RESOLVIDO

**Descoberto durante:** validação end-to-end (2026-04-04).

**Sintoma:** `RuntimeError: There's a mismatch between the models and the database.` — Alembic propunha `remove_table` para todas as tabelas Django do schema `public`.

**Causa:** `search_path = langflow, public` no role — o Alembic introspectava o schema `public` e encontrava tabelas Django que não existem nos modelos do Langflow.

**Correcção aplicada:** `search_path` restrito a `langflow` apenas (no bootstrap e na URL via `options=-csearch_path=langflow`).
