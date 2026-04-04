# ADR-009 — Integração Django ↔ Langflow: Base de Dados Partilhada e Multi-tenancy via Workspaces

**Data:** 2026-04-04
**Estado:** Proposed
**Autores:** RID Platform Team
**Revisores:** Tech Lead, Backend Engineer
**Contexto de código:** `docker-compose.yml`, `backend/apps/tenants/models.py`, `backend/api/services/langflow_workspace.py` (a criar), `docs/plans/2026-04-04-langflow-database-integration.md`

---

## Contexto

O RID Platform integra o Langflow 1.8.3 como motor de execução de fluxos LLM. O Langflow tem o seu próprio servidor e a sua própria camada de persistência (SQLAlchemy + Alembic), completamente separada do Django ORM.

O `docker-compose.yml` actual não define `LANGFLOW_DATABASE_URL`, pelo que o Langflow usa **SQLite por defeito, armazenado dentro do container sem volume**. Cada `docker compose down` apaga silenciosamente todos os flows, utilizadores Langflow e API keys — corrompendo os `langflow_user_id` e `langflow_api_key` guardados em `TenantUser`. Este é um bug crítico (P0) que torna o ambiente de desenvolvimento inutilizável após qualquer restart.

Para além do bug de persistência, existe uma lacuna de multi-tenancy: o modelo `Customer` não tem `langflow_workspace_id`. O Langflow usa workspaces para isolamento de dados; sem este mapeamento, todos os utilizadores partilham o workspace default do superuser e os flows de um tenant são visíveis para outros tenants.

No projecto legado (RockItDown), a dor operacional foi descrita como "dois bancos de dados a manter". A análise revelou que o problema real não era a existência de dois schemas de dados distintos — era ter dois **ciclos de vida operacionais independentes**: backup, restore, migração e monitorização em separado, com ORMs incompatíveis que tornavam qualquer tentativa de unificação mais cara do que o problema que resolvia.

## Decisão

### 1. Langflow usa PostgreSQL na mesma instância que o Django

Configuramos `LANGFLOW_DATABASE_URL` apontando para uma database `langflow` separada no mesmo servidor PostgreSQL (`rid-db`):

```
PostgreSQL server (rid-db)
  ├── database: rid        ← Django (django-tenants: schemas public + tenant_*)
  └── database: langflow   ← Langflow (Alembic: tabelas internas, completamente isoladas)
```

O Langflow corre as suas próprias migrações Alembic na database `langflow`. O Django nunca acede à database `langflow`. Não há partilha de schemas, tabelas ou ORM entre os dois subsistemas.

A database `langflow` é criada via script de init do PostgreSQL (`/docker-entrypoint-initdb.d/01-langflow-db.sql`), executado automaticamente no primeiro arranque.

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
  Django ORM:         nunca toca na database 'langflow'
  SQLAlchemy:         nunca importado no código RID
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| SQLite com volume persistente | Não é production-ready sob carga concorrente (WAL file locking); não resolve o problema operacional de dois stores independentes. Aceitável apenas como hotfix temporário de desenvolvimento. |
| Schema partilhado `langflow_svc` na database `rid` | Tecnicamente possível mas arriscado: Alembic pode não respeitar `search_path` em todas as operações (índices, FK constraints com schema explícito); `django-tenants` itera schemas em `migrate_schemas` — requer `TENANT_SCHEMA_EXCLUDE_LIST` como dependência de configuração frágil. A Opção adoptada resolve o mesmo problema sem estes riscos. |
| Unificar ORMs (expor SQLAlchemy no Django) | Acoplamento total aos internos do Langflow, que mudam em cada minor release. Inviável em upgrades. Contradiz o princípio de integração via API oficial (ADR-008). |
| Dois servidores PostgreSQL independentes | Reproduz exactamente o problema do legado: dois ciclos de vida operacionais independentes. Nenhum benefício sobre a decisão adoptada; overhead máximo. |
| Acesso directo à database Langflow a partir do Django | Coupling a SQLAlchemy models internos do Langflow. Qualquer upgrade do Langflow pode alterar o schema sem aviso. Impossível manter correctamente com `django-tenants`. |

## Consequências Positivas

- O bug crítico de perda de dados (SQLite sem volume) é eliminado — dados Langflow persistem entre restarts.
- Único servidor PostgreSQL a operar: um `pg_dump rid-db` inclui ambas as databases; backup, restore e monitorização unificados.
- Zero risco de interferência entre Alembic (Langflow) e Django migrations (`django-tenants`): databases completamente separadas, sem partilha de schemas.
- Isolamento multi-tenant correcto: cada tenant tem o seu workspace Langflow; flows de um tenant não são visíveis para outro.
- O Django ORM permanece a única fonte de verdade para dados do Django. Sem SQLAlchemy no código RID — a equipa não precisa de aprender nem manter dois ORMs.
- Upgrade do Langflow = alterar a tag + verificar API de workspaces + re-testar bridge. O Django ORM não é afectado.

## Consequências Negativas / Trade-offs

- **Script de init só corre com `pgdata` vazio:** O `01-langflow-db.sql` é executado pelo `postgres:16-alpine` apenas na primeira inicialização. Ambientes existentes com `pgdata` já populado requerem criação manual da database `langflow` (`CREATE DATABASE langflow;` via `psql`). Documentado no plano; risco residual baixo em desenvolvimento.
- **API de workspaces pode variar entre versões:** O Langflow 1.8.3 pode expor o conceito de workspace como `/api/v1/workspaces/` ou `/api/v1/folders/` (variou entre minor releases). Verificar contra o swagger em `http://localhost:7860/docs` antes de implementar a Fase 2. Mitigação: o serviço `langflow_workspace.py` isola este detalhe — mudança de endpoint afecta apenas 1 ficheiro.
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

# 5. Script de init da database langflow existe
test -f /home/RID/infra/docker/langflow-db-init.sql
# Expected: exit 0
```

## Referências

- `docker-compose.yml` — serviço `langflow` e `db`
- `backend/apps/tenants/models.py` — modelo `Customer` (campo `langflow_workspace_id` a adicionar)
- `backend/apps/accounts/models.py` — modelo `TenantUser` (campos `langflow_user_id`, `langflow_api_key`)
- `backend/api/services/langflow_client.py` — bridge HTTP existente
- `backend/api/routers/langflow_auth.py` — auto-login bridge (a actualizar na Fase 2)
- `backend/api/services/langflow_workspace.py` — serviço de provisioning (a criar)
- `docs/plans/2026-04-04-langflow-database-integration.md` — plano de implementação detalhado
- ADR-003 — Arquitectura híbrida Django + FastAPI
- ADR-008 — Personalização do Frontend Langflow (integração via API REST oficial)

---

## Apêndice — Bug P0 detectado em análise (2026-04-04)

### IB-001 — Langflow usa SQLite sem volume no docker-compose.yml

**Descoberto durante:** brainstorm de arquitectura de integração.

**Sintoma:** após `docker compose down && docker compose up`, o health check Langflow retorna `{"status":"ok"}` mas todos os flows, utilizadores e API keys foram apagados. Os `langflow_user_id` e `langflow_api_key` em `TenantUser` apontam para utilizadores inexistentes; o auto-login retorna 401.

**Causa:** `docker-compose.yml` não define `LANGFLOW_DATABASE_URL` → Langflow usa SQLite em `/root/.langflow/langflow.db` dentro do container → sem volume, o ficheiro é efémero.

**Correcção:** Fase 1 deste ADR — `LANGFLOW_DATABASE_URL=postgresql://rid:rid@db:5432/langflow` + script de init + `depends_on: db`.
