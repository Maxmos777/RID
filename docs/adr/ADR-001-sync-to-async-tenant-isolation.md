# ADR-001 — `sync_to_async` com `thread_sensitive=True` para isolamento de tenant em FastAPI async

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:code-reviewer, ring:backend-engineer-typescript
**Revisores:** ring:governance-specialist
**Contexto de código:** `api/deps.py:26-47`, `api/deps.py:69`

---

## Contexto

O projecto usa `django-tenants` com isolamento por schema PostgreSQL. O `TenantMainMiddleware` do Django garante que cada request HTTP tem o schema correcto na conexão de BD — mas este middleware **não cobre rotas FastAPI** (`/api/*`), que seguem um caminho ASGI separado.

A implementação inicial de `get_current_tenant` usava `await Domain.objects.aget(...)` seguido de `connection.set_tenant(tenant)`. Em ambiente ASGI com Uvicorn, múltiplas corrotinas podem correr no mesmo OS thread e intercalar entre `await`s: a corrotina A chama `aget`, aguarda, e antes de retomar a corrotina B chama `set_tenant` na mesma `connection` thread-local — contaminando o contexto de A.

A `connection` do Django é **thread-local por design** e não é segura para uso concorrente em contexto async sem isolamento explícito.

## Decisão

Executamos todo o bloco de resolução de tenant (query ORM + `connection.set_tenant`) dentro de `sync_to_async(..., thread_sensitive=True)`, que garante que o código síncrono corre numa thread dedicada do pool do Django — o mesmo mecanismo de isolamento que o `TenantMainMiddleware` usa internamente.

```python
# api/deps.py:69
return await sync_to_async(_resolve_tenant, thread_sensitive=True)(hostname)
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| `await Domain.objects.aget(...)` + `connection.set_tenant()` directo em corrotina async | Race condition: `set_tenant` é chamado após um `await`, altura em que outra corrotina pode ter mudado o estado da `connection` thread-local. Falha silenciosa — queries correm no schema errado sem erro visível. |
| Django Middleware wrapping FastAPI | O `TenantMainMiddleware` do Django só actua sobre o stack Django. Montar FastAPI dentro do middleware Django quebra o isolamento ASGI e introduz overhead de inicialização por request. |
| Middleware FastAPI personalizado | Possível, mas replica a lógica do `TenantMainMiddleware` sem usar a infraestrutura testada do `django-tenants`. Maior superfície de erro. |
| Migrar toda a lógica de tenant para FastAPI (sem Django ORM) | Descartado por custo de migração e perda da infraestrutura `django-tenants` (migrações automáticas, admin, etc.). |

## Consequências Positivas

- Isolamento thread-local garantido: cada request FastAPI que resolve tenant tem a sua própria thread de pool, sem partilha de estado.
- Consistência com `TenantMainMiddleware`: usa o mesmo mecanismo de isolamento que o Django usa internamente.
- Testável: `_resolve_tenant` é síncrona pura, injectável em testes sem infra async.
- Sem overhead extra: `sync_to_async` com `thread_sensitive=True` usa o thread pool existente do Django/asgiref — não cria threads adicionais.

## Consequências Negativas / Trade-offs

- **Latência de thread dispatch:** cada request FastAPI que precisa de resolver tenant paga o custo de dispatch para o thread pool (~0.1–0.5ms). Aceitável para APIs com tempo de resposta >1ms.
- **`thread_sensitive=True` é obrigatório:** remover este parâmetro não causa erro imediato — o código parece funcionar em desenvolvimento com baixa concorrência, mas falha em produção. Este é o principal risco de drift (ver Compliance).
- **Código splitting obrigatório:** a lógica de DB precisa de ser separada em funções síncronas para poder ser envolvida por `sync_to_async`. Isto é uma convenção de arquitectura que deve ser mantida em todas as rotas FastAPI futuras que acedem ao ORM.

## Compliance

```bash
# Verificar que sync_to_async está presente em deps.py com thread_sensitive=True
grep -n "sync_to_async" /home/RID/backend/api/deps.py
# Expected: linha com sync_to_async(_resolve_tenant, thread_sensitive=True)

# Verificar que não há chamadas ORM directas em funções async de api/
grep -rn "\.aget\|\.asave\|\.adelete" /home/RID/backend/api/
# Expected: sem resultados (todo o acesso ORM deve ser via sync_to_async)
```

**PR checklist:** Qualquer PR que adicione rotas FastAPI com acesso ORM deve incluir `sync_to_async` com `thread_sensitive=True`. Item obrigatório no ADR Impact checklist para ficheiros `api/**/*.py`.

## Referências

- `api/deps.py:1-17` — docstring que explica a isolation strategy
- `api/deps.py:26-47` — `_resolve_tenant`: função síncrona isolada
- `api/deps.py:69` — invocação `sync_to_async(..., thread_sensitive=True)`
- [asgiref sync_to_async docs](https://asgi.readthedocs.io/en/latest/extensions/sync.html) — documentação oficial do `thread_sensitive`
- [django-tenants TenantMainMiddleware source](https://github.com/django-tenants/django-tenants/blob/master/django_tenants/middleware/main.py) — referência do mecanismo equivalente no Django
