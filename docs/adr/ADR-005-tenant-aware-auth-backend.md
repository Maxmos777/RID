# ADR-005 — `TenantAwareBackend` com formato de login `user@tenant-domain`

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:backend-engineer-typescript, ring:codebase-explorer
**Revisores:** ring:governance-specialist
**Contexto de código:** `core/auth_backends.py`, `core/settings.py:127-132`

---

## Contexto

Num sistema multi-tenant com utilizadores no schema público (ADR-002), um utilizador pode pertencer a vários tenants. O `django-allauth` por defeito autentica por email global — o que funciona para utilizadores com um único tenant, mas é ambíguo quando o mesmo email existe com papéis diferentes em tenants distintos.

Além disso, cenários como acesso por CLI, integrações M2M, ou painéis multi-tenant requerem que um utilizador consiga especificar **qual o tenant** no acto de login, sem depender de detecção por domínio HTTP.

O predecessor RockItDown tinha um `TenantAwareBackend` que resolvia este problema, mas com utilizadores no schema do tenant (requerendo `schema_context` switch). O RID precisa de uma versão adaptada para utilizadores no schema público.

## Decisão

Adicionamos `TenantAwareBackend` à cadeia de `AUTHENTICATION_BACKENDS` do Django como primeiro backend, suportando login no formato `username@tenant-domain` ou `username@schema_name`. O backend valida que o tenant existe, depois autentica o utilizador no schema público sem `schema_context` switch. Se o formato não corresponder ou o tenant não existir, o backend retorna `None` e a cadeia continua para os backends seguintes (allauth EmailBackend para login standard por email).

```python
# core/settings.py:127-132
AUTHENTICATION_BACKENDS = [
    "core.auth_backends.TenantAwareBackend",        # user@tenant-domain
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Só allauth EmailBackend (login por email global) | Ambíguo para utilizadores multi-tenant; sem mecanismo para especificar tenant no login. |
| Detecção de tenant exclusivamente por domínio HTTP | Obriga cada tenant a ter o seu domínio configurado para aceder ao painel. Inviável em desenvolvimento, insuficiente para CLI/M2M. |
| Campo `tenant` separado no formulário de login | Altera UX do formulário allauth, requer forms customizadas, não funciona em integrações externas que usam username/password standard. |
| `schema_context` switch durante autenticação (padrão RockItDown) | Incompatível com ADR-002 (utilizadores no schema público). Tornaria o backend dependente do schema do tenant para encontrar utilizadores que estão no schema público. |

## Consequências Positivas

- Compatibilidade com allauth: se o formato `user@tenant` não corresponder, o backend retorna `None` e o allauth EmailBackend tenta normalmente — sem breaking change para utilizadores existentes.
- Flexibilidade de identificação de tenant: aceita hostname (`alice@acme.rid.com`) e schema_name curto (`alice@acme`) — útil em desenvolvimento e CLI.
- Sem `schema_context` complexo: utilizadores no schema público simplificam o fluxo de autenticação a um único query.
- Extensível para SSO: o formato `user@tenant` é compatível com SAML NameID format `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress` e pode servir de base para integração SSO futura.

## Consequências Negativas / Trade-offs

- **Formato `user@tenant` pode confundir com email:** se `username` for um email (ex: `alice@gmail.com`), o backend interpreta `gmail.com` como tenant — e como não existe, retorna `None` e delega correctamente. Mas pode gerar queries desnecessárias à tabela `Domain`. Mitigado pela ordem na cadeia: `TenantAwareBackend` primeiro, depois allauth.
- **Sem enforcement de formato:** o formulário de login não valida o formato `user@tenant` — um utilizador que escreve `alice` (sem `@`) vai directamente para o allauth EmailBackend. Isto é comportamento esperado mas pode ser confuso.
- **Dois registos de autenticação na audit trail:** um login `alice@acme` gera uma tentativa no `TenantAwareBackend` (sucesso ou fail) e depois pode gerar outra no allauth backend se o primeiro falhar. O audit log de autenticação deve estar ciente disto.

## Compliance

```bash
# Verificar que TenantAwareBackend é o primeiro na cadeia
grep -A 5 "AUTHENTICATION_BACKENDS" /home/RID/backend/core/settings.py
# Expected: TenantAwareBackend na primeira posição

# Verificar que o backend retorna None para inputs sem '@' (sem BD)
cd /home/RID/backend && . .venv/bin/activate && python3 -c "
import os; os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django; django.setup()
from core.auth_backends import TenantAwareBackend
b = TenantAwareBackend()
assert b.authenticate(None, username='sem_arroba', password='x') is None
assert b.authenticate(None, username='@', password='x') is None
print('OK: early return sem BD')
"

# Teste completo (requer BD)
cd /home/RID/backend && . .venv/bin/activate && pytest tests/test_auth_backends.py -v 2>/dev/null || echo "(criar tests/test_auth_backends.py se não existir)"
```

## Referências

- `core/auth_backends.py` — implementação completa
- `core/settings.py:127-132` — posição na cadeia `AUTHENTICATION_BACKENDS`
- `core/auth_backends.py:1-12` — docstring com fluxo de autenticação
- `RockItDown/src/core/auth_backends.py` — origem do padrão (predecessor)
- [Django Authentication Backends docs](https://docs.djangoproject.com/en/5.0/topics/auth/customizing/#specifying-authentication-backends) — documentação oficial da cadeia de backends
