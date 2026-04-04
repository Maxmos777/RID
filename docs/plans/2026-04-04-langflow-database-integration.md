# Plano — Integração Django ↔ Langflow: Base de Dados e Multi-tenancy

**Data:** 2026-04-04
**Estado:** Proposed
**Autores:** RID Platform Team
**Contexto:** Brainstorm de arquitectura pós-ADR-008; resolve dual-database problem + bug crítico de perda de dados
**ADR relacionado:** ADR-009 (a criar após aprovação deste plano)

---

## Diagnóstico

### Bug crítico (P0) — Perda de dados Langflow em cada restart

O `docker-compose.yml` actual não define `LANGFLOW_DATABASE_URL`. O Langflow usa SQLite por defeito, armazenado **dentro do container sem volume**. Consequências:

- `docker compose down` → todos os flows, utilizadores, API keys apagados
- Os `langflow_user_id` e `langflow_api_key` guardados em `TenantUser` ficam inválidos
- A bridge auto-login retorna erro 401 na próxima execução

**Este bug deve ser resolvido na Fase 1, antes de qualquer outra funcionalidade.**

### Lacuna de multi-tenancy (P1)

Langflow usa **workspaces** para isolamento de dados. O código actual não provisiona workspaces por tenant:
- `TenantUser` tem `langflow_user_id` e `langflow_api_key` — correcto
- `Customer` não tem `langflow_workspace_id` — **ausente**
- Todos os utilizadores estão no workspace default do superuser
- Flows de um tenant são visíveis para outros tenants — **falha de isolamento**

### Problema de dois servidores de BD (P2)

O problema real no legado RockItDown não era ter dois schemas de dados distintos — era ter dois **ciclos de vida operacionais independentes**: backup, restore, migração e monitorização separados. A solução não é unificar o ORM, é unificar o servidor.

---

## Decisão de arquitectura

```
ANTES:  Django PostgreSQL (rid-db)   +   Langflow SQLite (container efémero)
DEPOIS: Django PostgreSQL (rid-db)   +   Langflow PostgreSQL (rid-db, database 'langflow')
```

Um único servidor PostgreSQL (`rid-db`) com dois databases:
- `rid` — Django (django-tenants: schemas public + tenant)
- `langflow` — Langflow (Alembic: tabelas próprias, completamente isoladas)

**Não partilhamos schemas.** Langflow corre as suas migrações Alembic na database `langflow`; Django nunca toca nessa database. Zero risco de interferência com `django-tenants`.

Para visibilidade de dados Langflow no Django (billing, audit, reporting — M3+): webhook-driven sync. Django não acede directamente à database Langflow. O Django ORM permanece a única fonte de verdade para o Django.

---

## Fase 1 — Fix crítico: Langflow usa PostgreSQL (P0)

**Estimativa:** 30 minutos  
**Bloqueio:** nenhum

### 1.1 — Script de init do PostgreSQL

Criar `infra/docker/langflow-db-init.sql`:
```sql
-- Cria a database 'langflow' se não existir.
-- Executado automaticamente pelo postgres:16-alpine no primeiro arranque
-- (apenas ficheiros em /docker-entrypoint-initdb.d/ são executados se pgdata estiver vazio).
SELECT 'CREATE DATABASE langflow'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langflow')\gexec
```

### 1.2 — Actualizar docker-compose.yml

No serviço `db`, adicionar mount do script de init:
```yaml
db:
  image: postgres:16-alpine
  volumes:
    - pgdata:/var/lib/postgresql/data
    - ./infra/docker/langflow-db-init.sql:/docker-entrypoint-initdb.d/01-langflow-db.sql
```

No serviço `langflow`, adicionar:
```yaml
langflow:
  environment:
    LANGFLOW_SUPERUSER: admin
    LANGFLOW_SUPERUSER_PASSWORD: adminpassword
    LANGFLOW_DATABASE_URL: "postgresql://rid:rid@db:5432/langflow"
  depends_on:
    db:
      condition: service_healthy
```

> **Nota:** O script SQL só é executado quando `pgdata` está vazio (primeiro `docker compose up`).
> Em ambientes existentes com `pgdata` já inicializado, criar a database manualmente:
> `docker exec rid-db psql -U rid -c "CREATE DATABASE langflow;"`

### 1.3 — Verificação

```bash
# Confirmar que Langflow usa PostgreSQL
docker compose --profile langflow exec langflow \
  python -c "import os; print(os.getenv('LANGFLOW_DATABASE_URL', 'NOT SET'))"
# Expected: postgresql://rid:rid@db:5432/langflow

# Confirmar que a database langflow existe no rid-db
docker exec rid-db psql -U rid -c "\l" | grep langflow
# Expected: langflow | rid | UTF8 | ...

# Confirmar health check Langflow após arranque
curl -s http://localhost:7860/health | python3 -m json.tool
# Expected: {"status":"ok","chat":"ok","db":"ok"}
```

---

## Fase 2 — Multi-tenancy: workspace Langflow por tenant (P1)

**Estimativa:** 2–3 horas  
**Bloqueio:** Fase 1 concluída

### 2.1 — Adicionar `langflow_workspace_id` ao modelo `Customer`

Ficheiro: `backend/apps/tenants/models.py`

```python
class Customer(TenantMixin):
    # ... campos existentes ...
    langflow_workspace_id = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID do workspace Langflow correspondente a este tenant.",
    )
```

Gerar e aplicar migração:
```bash
python manage.py makemigrations tenants --name="add_langflow_workspace_id"
python manage.py migrate_schemas --shared
```

### 2.2 — Serviço de provisioning de workspace

Criar `backend/api/services/langflow_workspace.py`:

```python
"""
Langflow workspace provisioning service.

Cada tenant Django tem um workspace Langflow correspondente.
O workspace é criado no momento do provisionamento do tenant,
não no auto-login do utilizador.

API Langflow usada:
  POST /api/v1/workspaces/                    → criar workspace
  POST /api/v1/workspaces/{id}/add-users/     → adicionar utilizador ao workspace
"""
from __future__ import annotations
from typing import Any
import httpx
from django.conf import settings
from api.services.langflow_client import _get_superuser_token


async def provision_tenant_workspace(
    tenant_schema: str,
    tenant_name: str,
) -> tuple[str, str | None]:
    """
    Cria um workspace Langflow para um tenant RID.

    Returns (workspace_id, None) on success.
    Returns ("", error_message) on failure.
    """
    superuser_token, err = await _get_superuser_token()
    if err:
        return "", err

    headers = {"Authorization": f"Bearer {superuser_token}"}

    async with httpx.AsyncClient(
        base_url=settings.LANGFLOW_BASE_URL, timeout=10
    ) as client:
        resp = await client.post(
            "/api/v1/workspaces/",
            json={"name": f"rid-{tenant_schema}", "description": tenant_name},
            headers=headers,
        )
        if resp.status_code not in (200, 201):
            return "", f"create workspace failed: {resp.status_code} — {resp.text}"

        workspace_id: str = resp.json().get("id", "")
        return workspace_id, None


async def add_user_to_workspace(
    workspace_id: str,
    langflow_user_id: str,
) -> str | None:
    """
    Adiciona um utilizador Langflow ao workspace do tenant.

    Returns None on success, error_message on failure.
    """
    superuser_token, err = await _get_superuser_token()
    if err:
        return err

    headers = {"Authorization": f"Bearer {superuser_token}"}

    async with httpx.AsyncClient(
        base_url=settings.LANGFLOW_BASE_URL, timeout=10
    ) as client:
        resp = await client.post(
            f"/api/v1/workspaces/{workspace_id}/add-users/",
            json={"user_ids": [langflow_user_id]},
            headers=headers,
        )
        if resp.status_code not in (200, 201, 204):
            return f"add user to workspace failed: {resp.status_code} — {resp.text}"
        return None
```

> **Nota sobre a API de workspaces:** A API de workspaces do Langflow 1.8.3 deve ser verificada
> antes da implementação (pode ser `/api/v1/folders/` dependendo da versão — o conceito de
> workspace em Langflow mapeou para "folders" em algumas versões). Verificar contra o swagger
> em `http://localhost:7860/docs`.

### 2.3 — Signal de provisioning no tenant

Criar `backend/apps/tenants/signals.py` (ou actualizar se existir):

```python
"""
Signal: quando um Customer é criado → provisionar workspace Langflow.
"""
from __future__ import annotations
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from apps.tenants.models import Customer


@receiver(post_save, sender=Customer, dispatch_uid="provision_langflow_workspace")
def provision_langflow_workspace(
    sender: type[Customer],
    instance: Customer,
    created: bool,
    **kwargs: object,
) -> None:
    """
    Ao criar um novo Customer, provisionar workspace no Langflow.
    Falhas são logadas mas não bloqueiam a criação do tenant.
    """
    if not created or instance.langflow_workspace_id:
        return

    import logging
    logger = logging.getLogger(__name__)

    try:
        from api.services.langflow_workspace import provision_tenant_workspace

        workspace_id, err = async_to_sync(provision_tenant_workspace)(
            tenant_schema=instance.schema_name,
            tenant_name=instance.name,
        )
        if err:
            logger.error(
                "Failed to provision Langflow workspace for tenant %s: %s",
                instance.schema_name,
                err,
            )
            return

        instance.langflow_workspace_id = workspace_id
        instance.save(update_fields=["langflow_workspace_id"])

    except Exception:
        logger.exception(
            "Unexpected error provisioning Langflow workspace for tenant %s",
            instance.schema_name,
        )
```

### 2.4 — Actualizar auto-login bridge para incluir workspace

No `langflow_auth.py`, após criar o utilizador Langflow e obter o `langflow_user_id`, adicionar o utilizador ao workspace do tenant:

```python
# Obter workspace_id do tenant actual
from apps.tenants.models import Customer
from django_tenants.utils import get_tenant

tenant = get_tenant(request)  # FastAPI: via header X-Tenant-Schema ou subdomain
if tenant.langflow_workspace_id and result.get("langflow_user_id"):
    from api.services.langflow_workspace import add_user_to_workspace
    err = await add_user_to_workspace(
        workspace_id=str(tenant.langflow_workspace_id),
        langflow_user_id=result["langflow_user_id"],
    )
    if err:
        logger.warning("Could not add user to workspace: %s", err)
        # Não bloquear o login — workspace membership pode ser re-tentada
```

> **Bloqueio:** o contexto de tenant em FastAPI routes está pendente de M2 (FastAPI API Layer).
> O `add_user_to_workspace` fica implementado mas chamado apenas quando o tenant context
> estiver disponível no router.

### 2.5 — Verificação da Fase 2

```bash
# Criar tenant de teste e verificar que langflow_workspace_id foi preenchido
python manage.py shell -c "
from apps.tenants.models import Customer
c = Customer.objects.get(schema_name='test_tenant')
print('workspace_id:', c.langflow_workspace_id)
"

# Verificar workspace no Langflow
curl -s -H "Authorization: Bearer $SUPERUSER_JWT" \
  http://localhost:7860/api/v1/workspaces/ | python3 -m json.tool | grep rid-test_tenant
```

---

## Fase 3 — Webhook sync para Django (M3+, reporting/billing)

**Estimativa:** 1–2 dias  
**Bloqueio:** Fase 2 concluída; Celery configurado

Esta fase é opcional para M1/M2. Implementar quando o reporting de execuções ou billing por uso for necessário.

### Modelos Django para mirror de dados Langflow

```python
# backend/apps/langflow_sync/models.py

class LangflowFlow(models.Model):
    """Mirror dos flows Langflow — source of truth para a UI Django."""
    flow_id = models.UUIDField(unique=True, db_index=True)
    tenant_schema = models.CharField(max_length=63, db_index=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "langflow_sync"


class LangflowExecution(models.Model):
    """Mirror de execuções de flows — para billing e audit."""
    execution_id = models.UUIDField(unique=True, db_index=True)
    flow = models.ForeignKey(LangflowFlow, on_delete=models.SET_NULL, null=True)
    tenant_schema = models.CharField(max_length=63, db_index=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=50)  # success, error, timeout
    tokens_used = models.IntegerField(default=0)

    class Meta:
        app_label = "langflow_sync"
        indexes = [models.Index(fields=["tenant_schema", "started_at"])]
```

### Endpoint de webhook

```python
# backend/api/routers/langflow_webhooks.py

@router.post("/webhooks/langflow/execution", status_code=204)
async def on_execution_complete(
    payload: LangflowWebhookPayload,
    x_langflow_secret: str = Header(...),
) -> None:
    """
    Recebe evento de conclusão de execução do Langflow.
    Valida HMAC via X-Langflow-Secret e enfileira Celery task.
    """
    if not _verify_webhook_secret(x_langflow_secret, payload):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Enfileirar task idempotente (execution_id como chave de deduplicação)
    await sync_langflow_execution.apply_async(
        args=[payload.execution_id, payload.model_dump()],
        task_id=f"lf-exec-{payload.execution_id}",  # idempotency key
    )
```

---

## Mapa de decisões arquitecturais

| Dimensão | Decisão | Alternativa rejeitada |
|---|---|---|
| Storage Langflow | PostgreSQL (database `langflow` no rid-db) | SQLite (data loss); schema partilhado (risco django-tenants) |
| ORM | Django ORM para dados RID; Langflow usa SQLAlchemy internamente — sem cruzamento | Expor SQLAlchemy no Django (coupling); reescrever Langflow ORM |
| Visibilidade Langflow → Django | Webhook-driven sync (M3+) | Acesso directo à DB Langflow (coupling a internals) |
| Multi-tenancy Langflow | Workspace por tenant; `langflow_workspace_id` em `Customer` | Workspace global (isolamento nulo) |
| Acoplamento | API REST only (httpx); Django nunca acede à DB Langflow directamente | Join cross-database (impossível em Django ORM standard) |

---

## Compliance checks

```bash
# 1. Langflow usa PostgreSQL (não SQLite)
grep "LANGFLOW_DATABASE_URL" /home/RID/docker-compose.yml | grep -q "postgresql"
echo "LANGFLOW_DATABASE_URL usa PostgreSQL: $?"

# 2. Customer tem langflow_workspace_id
grep "langflow_workspace_id" /home/RID/backend/apps/tenants/models.py
echo "langflow_workspace_id em Customer: $?"

# 3. Langflow depende do serviço db
grep -A 5 "depends_on" /home/RID/docker-compose.yml | grep -q "db"
echo "depends_on db: $?"

# 4. Sem acesso directo à DB Langflow a partir do Django (sem import sqlalchemy no código RID)
grep -r "import sqlalchemy" /home/RID/backend/apps/ /home/RID/backend/api/
echo "Sem import sqlalchemy (0 = ok): $?"
```

---

## Intercorrências conhecidas / Riscos

### R-001 — API de workspaces Langflow pode ser `/api/v1/folders/`

O conceito de "workspace" no Langflow mapeou para "folders" em algumas versões minor. Antes de implementar a Fase 2, verificar o swagger em `http://localhost:7860/docs` e ajustar os endpoints em `langflow_workspace.py`.

**Mitigação:** wrapper de serviço (`langflow_workspace.py`) isola este detalhe — mudança de endpoint afecta apenas 1 ficheiro.

### R-002 — Script SQL de init só corre com pgdata vazio

O script `01-langflow-db.sql` é executado pelo `postgres:16-alpine` apenas na primeira inicialização (quando `pgdata` está vazio). Ambientes de desenvolvimento com `pgdata` existente precisam de criação manual.

**Mitigação:** Documentado em Fase 1.3. Alternativa: usar `POSTGRES_MULTIPLE_DATABASES` via script custom em vez de SQL puro.

### R-003 — Provisioning de workspace falha silenciosamente

O signal de provisioning captura excepções e loga sem propagar. Um tenant pode ser criado sem `langflow_workspace_id`.

**Mitigação:** health check de tenant — validar que `langflow_workspace_id is not None` no endpoint de admin. Adicionar alerta/log monitoring para erros de provisioning.

### R-004 — Tenant context não disponível em FastAPI routes (M1)

O `add_user_to_workspace` no auto-login bridge requer `tenant.langflow_workspace_id`, que por sua vez requer resolver o tenant a partir do request. Este mecanismo (via header ou subdomain) faz parte do M2.

**Mitigação:** O auto-login bridge funciona sem workspace membership na Fase 1. O utilizador fica no workspace default até M2 completar o contexto de tenant nas FastAPI routes.
