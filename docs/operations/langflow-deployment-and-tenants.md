# Implantação Langflow e tenants

Runbook para operadores: base de dados partilhada com schema `langflow`, bootstrap DDL, compose, provisionamento de workspace por tenant e bridge RID ↔ Langflow (utilizador de serviço).

## Arquitectura resumida

- O PostgreSQL do projeto RID (`rid`) aloja o schema aplicacional Django (multi-tenant) e um **schema dedicado `langflow`** para as tabelas geridas pelo Langflow.
- A URL de ligação do Langflow fixa o `search_path` para `langflow`, isolando migrações Alembic do Langflow das tabelas Django.
- O comando Django `ensure_langflow_schema` cria o role e o schema de forma idempotente (fonte única de DDL, alinhada ao ADR-009).

## Docker Compose (perfil `langflow`)

Serviços relevantes em `docker-compose.yml`:

| Serviço | Função |
|---------|--------|
| `langflow-pg-bootstrap` | Executa `python manage.py ensure_langflow_schema` uma vez (restart `no`), com `depends_on: db` saudável. |
| `langflow` | Contentor Langflow; `LANGFLOW_DATABASE_URL` aponta para `db:5432/rid` com `options=-csearch_path=langflow`. |
| `db` | PostgreSQL partilhado. |

Ordem típica: `db` → `langflow-pg-bootstrap` (completa com sucesso) → `langflow` inicia.

### Porta no host

O mapeamento publicado usa **7861** no host → **7860** no contentor Langflow, para evitar conflito com processos locais na 7860.

## Variáveis de ambiente (backend / compose)

Consulte `backend/.env.example` para a lista completa. Resumo operacional:

| Variável | Uso |
|----------|-----|
| `LANGFLOW_DATABASE_URL` | No serviço Langflow: connstring com user `langflow`, DB `rid`, `search_path=langflow`. |
| `LANGFLOW_DB_PASSWORD` | Palavra-passe do role `langflow`; referenciada no compose e no bootstrap. |
| `LANGFLOW_BASE_URL` | No backend RID: URL para a API Langflow (ex.: `http://langflow:7860` em rede Docker ou `http://localhost:7861` a partir do host). |
| `LANGFLOW_SUPERUSER_API_KEY` | Chave de API de superuser: criação do utilizador de serviço e do project na fase de provisionamento. Se ausente, `langflow_workspace_id` pode não ser preenchido. |

## Bootstrap do schema

Executar (ou deixar o compose executar) no contexto do backend:

```bash
python manage.py ensure_langflow_schema
```

Requisitos: variáveis `DATABASE_*` correctas e acesso ao Postgres. O comando deve ser seguro de repetir (idempotente).

## Utilizadores Langflow e tenants

### Provisionamento (background)

Quando um `Customer` é criado, o fluxo em `apps/tenants/services.py` / sinais chama `provision_tenant_langflow_project` (`api/services/langflow_workspace.py`), que:

1. Cria (ou reutiliza) o utilizador Langflow `rid.svc.<schema>@tenant.rid` com password derivada.
2. Cria o **project** (workspace) nomeado `rid-<schema>`.
3. Persiste o UUID do project em **`Customer.langflow_workspace_id`**.

### Bridge (`auto-login`)

O endpoint `GET /api/v1/langflow/auth/auto-login` obtém JWT + API key via **`get_tenant_service_credentials`** (`api/services/langflow_client.py`):

- Primeira vez (sem cache): login como serviço + `POST /api/v1/api_key/`; a API key é guardada em **`Customer.langflow_service_api_key`**.
- Visitas seguintes: apenas login para JWT fresco; reutiliza a key em cache.

Requisitos para `200 OK`: utilizador Django com membership no tenant, `langflow_workspace_id` não nulo, Langflow acessível.

### Campos no modelo `Customer`

| Campo | Função |
|--------|--------|
| `langflow_workspace_id` | UUID do project Langflow (Folder). |
| `langflow_service_api_key` | Cache da API key do utilizador de serviço (opcional até ao primeiro auto-login bem-sucedido). |

Os campos `TenantUser.langflow_*` não são usados pela bridge actual; podem permanecer na base para dados legados ou usos futuros.

## Superuser e chaves API

- Em desenvolvimento, o compose define `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` para primeiro acesso ao painel.
- Em produção, prefira fluxos documentados pelo Langflow para API keys e minimize credenciais longas em ficheiros de ambiente versionados.

## Resolução de problemas

1. **Langflow não arranca após bootstrap:** verifique logs de `langflow-pg-bootstrap` e se `ensure_langflow_schema` terminou com exit code 0.
2. **409 na bridge `auto-login`:** o tenant ainda não tem `langflow_workspace_id` — verifique logs de provisionamento, `LANGFLOW_SUPERUSER_API_KEY` e conectividade a `LANGFLOW_BASE_URL`.
3. **502 na bridge:** confirme `LANGFLOW_BASE_URL` acessível a partir do processo do backend e que o login do utilizador de serviço funciona (password derivada alinhada com `derive_tenant_service_password` em `langflow_workspace.py`).
4. **Tabelas no schema errado:** confirme que `LANGFLOW_DATABASE_URL` inclui `search_path=langflow` (no compose: `options=-csearch_path%3Dlangflow`).

## Ver também

- [ADR-009 — Integração Langflow com PostgreSQL](../adr/ADR-009-langflow-database-integration.md)
- [Guia de integração Langflow](../guides/langflow-bridge-integration.md)
- [Referência API bridge](../api/langflow-bridge.md)
