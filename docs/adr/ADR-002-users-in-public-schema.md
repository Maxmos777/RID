# ADR-002 — Utilizadores no schema público (SHARED_APPS), não no schema do tenant

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:backend-engineer-typescript, ring:codebase-explorer
**Revisores:** ring:governance-specialist
**Contexto de código:** `core/settings.py:25-49`, `apps/accounts/models.py`, `core/auth_backends.py`

---

## Contexto

O `django-tenants` suporta dois modelos de utilizadores: (A) utilizadores no schema do tenant (cada tenant tem a sua tabela `auth_user`) ou (B) utilizadores no schema público partilhado. O predecessor do projecto (RockItDown) usava o modelo A — utilizadores no schema do tenant — o que obrigava a `schema_context` switches dentro do processo de autenticação e criava acoplamento entre a identidade do utilizador e o tenant.

O RID suporta utilizadores que pertencem a **múltiplos tenants** (via `TenantMembership`) e usa `django-allauth` para autenticação, que não foi desenhado para multi-tenant com `schema_context` switches durante o fluxo de login. Além disso, o `django.contrib.admin` e o `django.contrib.auth` esperam tabelas de utilizadores no schema onde correm — o que num sistema multi-tenant exigiria ou um admin por tenant ou gestão manual de schema switches.

## Decisão

Todos os utilizadores (`TenantUser`, que estende `AbstractUser`) ficam no schema **público** (`SHARED_APPS`). A ligação utilizador↔tenant é feita por `TenantMembership` (schema público), que armazena `tenant_schema` como string em vez de FK cross-schema.

```python
# core/settings.py:25-47
SHARED_APPS = [
    ...
    "apps.accounts",   # TenantUser aqui — schema público
]
TENANT_APPS = [
    "django.contrib.contenttypes",  # apenas contenttypes por tenant
]
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Utilizadores no schema do tenant (modelo RockItDown) | Quebra `django-allauth`: o fluxo de signup/login corre no schema público e allauth v65+ não suporta `schema_context` switches transparentes dentro dos seus handlers. Exigiria fork ou monkey-patching do allauth. |
| Utilizadores duplicados (público + tenant) | Sincronização bidirecional complexa, risco de divergência de dados, dois registos de password para o mesmo utilizador. |
| Middleware que detecta tenant e faz schema switch antes do allauth | Frágil: depende da ordem de middleware e falha em requests sem Host header (admin Django, management commands). |
| Modelo de utilizador global sem `TenantMembership` | Sem separação de papéis por tenant. Um utilizador `owner` num tenant seria `owner` em todos — inaceitável para SaaS. |

## Consequências Positivas

- `django-allauth` funciona sem modificações: signup, login, confirmação de email, reset de password correm no schema público como esperado.
- Admin Django funciona: o painel de administração vê todos os utilizadores num único schema.
- Multi-tenant para um utilizador: um utilizador pode pertencer a vários tenants com papéis diferentes via `TenantMembership`.
- Sem cross-schema joins: `TenantMembership` usa `tenant_schema: CharField` em vez de FK, evitando joins entre schemas PostgreSQL.
- `TenantAwareBackend` simplificado: valida que o tenant existe, depois autentica no schema público sem `schema_context`.

## Consequências Negativas / Trade-offs

- **Dados de utilizador não isolados por tenant:** se um utilizador pertencer a dois tenants, os seus dados pessoais (email, nome) são partilhados. Para SaaS onde a privacidade entre tenants é crítica, esta decisão requer revisão antes de compliance GDPR avançado.
- **`TENANT_APPS` quase vazio:** modelos de negócio tenant-específicos (ex: `apps.flows`, `apps.billing_usage`) devem ser adicionados a `TENANT_APPS` à medida que são criados — requer disciplina.
- **`TenantMembership.tenant_schema` é uma string:** sem integridade referencial por FK. Se um `Customer` for eliminado, os registos de `TenantMembership` ficam orphaned (mitigado pelo signal `cleanup_tenant_memberships`).

## Compliance

```bash
# Verificar que apps.accounts está em SHARED_APPS e não em TENANT_APPS
grep -A 20 "SHARED_APPS" /home/RID/backend/core/settings.py | grep "apps.accounts"
# Expected: "apps.accounts" presente

grep -A 10 "TENANT_APPS" /home/RID/backend/core/settings.py | grep "apps.accounts"
# Expected: sem resultado (accounts não deve estar em TENANT_APPS)

# Verificar que TenantUser extends AbstractUser (não AbstractBaseUser sem contrib.auth)
grep -n "class TenantUser" /home/RID/backend/apps/accounts/models.py
# Expected: class TenantUser(AbstractUser)
```

**Regra para novas apps:** Qualquer nova app que contenha modelos de utilizador ou autenticação deve ser adicionada a `SHARED_APPS`. Modelos de dados de negócio tenant-específicos vão para `TENANT_APPS`.

## Referências

- `core/settings.py:25-49` — configuração `SHARED_APPS` / `TENANT_APPS`
- `apps/accounts/models.py` — `TenantUser` e `TenantMembership`
- `core/auth_backends.py:72` — comentário "Utilizadores no schema público — auth directa sem schema_context"
- `apps/tenants/signals.py:58-62` — `cleanup_tenant_memberships` mitiga orphaned memberships
- [django-tenants SHARED_APPS docs](https://django-tenants.readthedocs.io/en/latest/install.html#shared-and-tenant-specific-apps) — documentação oficial
