# Integração com a bridge Langflow

Este guia explica como o frontend obtém credenciais Langflow através do backend RID, usando a sessão Django autenticada. Serve para quem implementa ou mantém o embed Langflow e variáveis de ambiente associadas.

## Pré-requisitos

- Utilizador autenticado no RID (sessão com cookie).
- Backend com integração Langflow activa (`MULTI_TENANT_ENABLED` e `LANGFLOW_BASE_URL` quando aplicável ao vosso ambiente).
- CORS configurado para o origin do frontend em desenvolvimento (ver `CORSMiddleware` em `api/main.py`).

## Fluxo resumido (estado actual)

1. O utilizador inicia sessão no RID (Django).
2. O frontend chama o endpoint da bridge com `credentials: 'include'` para enviar o cookie de sessão.
3. O backend valida a sessão, obtém ou cria o utilizador Langflow correspondente e devolve `access_token` e `api_key`.
4. O frontend guarda tokens (por exemplo em cookies httpOnly definidos pelo próprio frontend ou pelo backend, conforme a vossa política) e usa-os nas chamadas ao Langflow (por exemplo cabeçalho `x-api-key` ou Bearer, conforme a API exposta pelo Langflow).

O padrão actual é **credenciais Langflow por utilizador RID** (email como username no Langflow). Isto está descrito em `docs/adr/ADR-009-langflow-database-integration.md` e implementado em `api/routers/langflow_auth.py`.

## Chamada desde o browser

Use sempre o mesmo origin que o backend espera para CORS, e inclua credenciais:

```javascript
const res = await fetch(`${API_BASE}/api/v1/langflow/auth/auto-login`, {
  method: 'GET',
  credentials: 'include',
  headers: { Accept: 'application/json' },
});
if (!res.ok) throw new Error(`auto-login failed: ${res.status}`);
const { access_token, api_key, langflow_user_id } = await res.json();
```

- **`API_BASE`**: URL do backend RID (por exemplo `http://localhost:8000`). Não confundir com `LANGFLOW_BASE_URL` (servidor Langflow, tipicamente `http://localhost:7861` no compose).
- **`credentials: 'include'`** é obrigatório para o cookie de sessão Django ser enviado.

Referência de contrato HTTP e códigos de erro: [Langflow bridge — referência de API](../api/langflow-bridge.md).

## Variáveis de ambiente relevantes

| Variável | Papel |
|----------|--------|
| `LANGFLOW_BASE_URL` | URL base do serviço Langflow (o backend usa-a para falar com a API Langflow). |
| `LANGFLOW_SUPERUSER_API_KEY` | Chave de superuser para operações administrativas (por exemplo provisionamento de workspace por tenant). Opcional em dev; ver `.env.example`. |
| `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` | Credenciais do superuser Langflow em ambientes que as usem (ex.: compose de desenvolvimento). |

Lista completa e comentários: `backend/.env.example`.

## Multi-tenant e schema

Com `django-tenants`, o utilizador autenticado pertence ao tenant correcto; a bridge usa o contexto de request já resolvido pelo middleware. Não é necessário enviar o schema do tenant no query string **no estado actual** do endpoint `auto-login`.

## Contrato planeado (alinhamento futuro)

O produto pode evoluir para **credenciais por tenant** (utilizador de serviço Langflow por `Customer`, `workspace_id` persistido, eventual query `tenant_schema` ou cabeçalho explícito). Quando esse contrato estiver implementado:

- Actualize este guia e [langflow-bridge.md](../api/langflow-bridge.md) para reflectir campos novos (por exemplo `workspace_id`) e deprecações (por exemplo `langflow_user_id` apenas para migração).
- Garanta que o frontend obtém `workspace_id` e envia-o ao embed Langflow conforme a documentação do produto nessa versão.

Até lá, trate a secção acima como roadmap; o comportamento em produção segue o fluxo «por utilizador» descrito no início deste guia.

## Ver também

- [ADR-009 — Integração Langflow com PostgreSQL](../adr/ADR-009-langflow-database-integration.md)
- [Implantação Langflow e tenants](../operations/langflow-deployment-and-tenants.md)
