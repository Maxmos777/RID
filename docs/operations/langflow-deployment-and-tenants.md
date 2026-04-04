# Implantação Langflow e tenants

Runbook para operadores: base de dados partilhada com schema `langflow`, bootstrap DDL, compose e variáveis que afectam o provisionamento de tenants e a bridge RID ↔ Langflow.

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
| `LANGFLOW_SUPERUSER_API_KEY` | Chave de API de superuser para criar utilizadores/workspaces via API. Se ausente, funcionalidades que dependam dela degradam com graciosidade (ex.: `Customer.langflow_workspace_id` pode ficar vazio). |

## Bootstrap do schema

Executar (ou deixar o compose executar) no contexto do backend:

```bash
python manage.py ensure_langflow_schema
```

Requisitos: variáveis `DATABASE_*` correctas e acesso ao Postgres. O comando deve ser seguro de repetir (idempotente).

## Utilizadores Langflow e tenants

**Estado actual (bridge):** o endpoint `GET /api/v1/langflow/auth/auto-login` associa credenciais Langflow **ao utilizador RID** (email, utilizador activo no Langflow). Campos em `TenantUser` (por exemplo `langflow_api_key`, `langflow_user_id`) persistem o estado.

**Planeado / produto:** utilizador de serviço por tenant (`rid.svc.<schema>@tenant.rid`), membership no workspace e `Customer.langflow_workspace_id`. Quando implementado, actualize este runbook com:

- passos de verificação por tenant (workspace criado, API key de serviço armazenada de forma segura);
- rotação de chaves e impacto na bridge.

## Superuser e chaves API

- Em desenvolvimento, o compose define `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` para primeiro acesso ao painel.
- Em produção, prefira fluxos documentados pelo Langflow para API keys e minimize credenciais longas em ficheiros de ambiente versionados.

## Resolução de problemas

1. **Langflow não arranca após bootstrap:** verifique logs de `langflow-pg-bootstrap` e se `ensure_langflow_schema` terminou com exit code 0.
2. **502 na bridge `auto-login`:** confirme `LANGFLOW_BASE_URL` acessível a partir do processo do backend, TLS/firewall, e que o Langflow responde à API de autenticação utilizada pelo cliente em `api/services/langflow_client.py`.
3. **Tabelas no schema errado:** confirme que `LANGFLOW_DATABASE_URL` inclui `search_path=langflow` (codificado no compose como `options=-csearch_path%3Dlangflow`).

## Ver também

- [ADR-009 — Integração Langflow com PostgreSQL](../adr/ADR-009-langflow-database-integration.md)
- [Guia de integração Langflow](../guides/langflow-bridge-integration.md)
- [Referência API bridge](../api/langflow-bridge.md)
