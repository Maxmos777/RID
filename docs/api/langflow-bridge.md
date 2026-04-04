# Langflow bridge — referência de API

Endpoints FastAPI expostos pelo backend RID para autenticação Langflow. A aplicação FastAPI está montada em `/api` no ASGI; os caminhos abaixo são **paths completos** a partir da raiz do host do backend (ex.: `https://api.exemplo.com/api/v1/langflow/...`).

## Autenticação

Os endpoints da bridge destinados ao browser assumem **sessão Django** (cookie de sessão). Não usam Bearer do RID neste fluxo.

---

## Obter credenciais Langflow (auto-login)

Obtém JWT e API key Langflow para o utilizador RID actualmente autenticado por sessão.

### Request

```http
GET /api/v1/langflow/auth/auto-login HTTP/1.1
Host: <backend-rid>
Cookie: <sessionid=...>
Accept: application/json
```

**Parâmetros de query (estado actual):** nenhum obrigatório.

**Planeado:** poderá existir `tenant_schema` (ou mecanismo equivalente) quando a bridge passar a emitir credenciais do utilizador de serviço do tenant; consulte nota em [Integração bridge Langflow](../guides/langflow-bridge-integration.md).

### Resposta `200 OK`

Corpo JSON (campos estáveis no código actual):

| Campo | Tipo | Descrição |
|--------|------|-------------|
| `access_token` | string | JWT Langflow para sessão do cliente. |
| `api_key` | string | API key Langflow para chamadas com `x-api-key` (ou fluxo suportado pela vossa versão Langflow). |
| `langflow_user_id` | string ou `null` | Identificador do utilizador Langflow no lado RID/TenantUser; pode ser `null` em casos extremos. |

Exemplo:

```json
{
  "access_token": "<jwt>",
  "api_key": "<api-key>",
  "langflow_user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Erros

| Status | Quando ocorre |
|--------|----------------|
| `401` | Sem sessão válida (utilizador não autenticado no RID). |
| `502` | Langflow indisponível ou resposta inválida (ex.: sem `access_token`). O `detail` descreve a causa. |

**Nota:** outros códigos (`400`, `403`, `404`, `409`) podem ser introduzidos quando o contrato multi-tenant por serviço estiver completo (validação de tenant, conflitos de provisionamento). Esta página deve ser actualizada nessa altura.

---

## Saúde da integração (placeholder)

Existe um router com prefixo `/langflow` e rota `GET /langflow/health` na aplicação FastAPI. O encaminhamento exacto face ao prefixo `/api` do ASGI pode variar conforme a configuração de deployment; trate como **não contractu** até haver testes ou documentação de produto que fixem o URL público.

---

## OpenAPI

Em modo de desenvolvimento (`DJANGO_DEBUG=true`), a especificação OpenAPI do RID pode estar disponível em `/api/openapi.json` e a UI em `/api/docs`, conforme `api/main.py`.

## Ver também

- [Guia de integração Langflow](../guides/langflow-bridge-integration.md)
- [ADR-009](../adr/ADR-009-langflow-database-integration.md)
