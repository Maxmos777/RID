# ADR-004 — `provision_tenant_for_user` como service layer idempotente (não signal directo)

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:backend-engineer-typescript, ring:codebase-explorer
**Revisores:** ring:governance-specialist
**Contexto de código:** `apps/tenants/services.py`, `apps/tenants/signals.py`

---

## Contexto

Criar um novo tenant no RID envolve múltiplos passos: normalizar o `schema_name`, criar o `Customer`, criar o `Domain`, e executar `migrate_schemas` para criar as tabelas no novo schema PostgreSQL. Este processo demora ~100-500ms e **não pode falhar silenciosamente** — um tenant sem schema é inacessível.

O predecessor RockItDown colocava esta lógica directamente no `post_save` signal do `Customer`. O RID começou com o mesmo padrão, o que criou três problemas: (1) o signal bloqueia o HTTP worker durante a migração; (2) não é idempotente — chamar `save()` duas vezes num `Customer` novo pode tentar criar o schema duas vezes; (3) a lógica de negócio (normalização, domínio único, migração) estava acoplada ao mecanismo de persistência Django.

## Decisão

A lógica de provisionamento fica numa **service function pura** `provision_tenant_for_user` em `apps/tenants/services.py`, chamada explicitamente a partir de views ou signals. O signal `post_save` em `apps/tenants/signals.py` é um **thin dispatcher** que apenas delega para a service layer (via thread para não bloquear o worker), sem conter lógica de negócio.

```python
# apps/tenants/services.py:72-85
tenant, created = Customer.objects.get_or_create(
    schema_name=schema_name,
    defaults={"name": tenant_name},
)
if created:
    with tenant_context(tenant):
        call_command("migrate_schemas", ...)
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Lógica completa no `post_save` signal (padrão RockItDown) | Não idempotente; lógica de negócio acoplada ao ORM signal; difícil de testar isoladamente; bloqueia worker HTTP durante migração. |
| Celery task imediata | Correcto para produção, mas adiciona dependência operacional (broker, worker) antes de qualquer feature estar implementada. Adiado para fase posterior. |
| `auto_create_schema = True` no modelo e deixar o `django-tenants` gerir | O `django-tenants` cria o schema mas não executa `migrate_schemas` automaticamente nem garante unicidade de domínio. Exige lógica adicional de qualquer forma. |
| Service layer sem idempotência (`create` em vez de `get_or_create`) | Falha em retry após timeout, em chamadas duplicadas, e em recovery após crash durante signup. |

## Consequências Positivas

- Idempotente: chamar `provision_tenant_for_user` múltiplas vezes com o mesmo `tenant_name` retorna o tenant existente sem erro.
- Testável: `_normalize_schema_name` e `_ensure_unique_domain` são funções puras testáveis sem BD.
- Separação de responsabilidades: signal thin (evento) → service (lógica) → ORM (persistência).
- `schema_name` normalizado: `slugify` + regex garante nomes PostgreSQL válidos, máximo 48 caracteres.
- Domínio único garantido: `_ensure_unique_domain` adiciona sufixo numérico se necessário.

## Consequências Negativas / Trade-offs

- **Signal e service duplicam o ponto de entrada:** em desenvolvimento, um `Customer.save()` dispara o signal que chama a lógica de thread. Em produção futura, views de signup chamarão `provision_tenant_for_user` directamente. Existe o risco de duplo provisionamento se ambos estiverem activos simultaneamente — mitigado pela idempotência de `get_or_create`.
- **Thread de fundo sem observabilidade:** o `threading.Thread` actual não tem retry, não reporta falhas a um sistema de alertas, e não é re-executável. É uma solução de transição até Celery ser configurado.
- **`migrate_schemas` é síncrono e lento:** mesmo dentro da thread, a migração pode demorar vários segundos num schema complexo. A UX de signup mostra sucesso antes da migração completar.

## Compliance

```bash
# Verificar que o signal não contém lógica de negócio (apenas Thread dispatch)
grep -n "schema_name\|slugify\|get_or_create\|migrate" /home/RID/backend/apps/tenants/signals.py
# Expected: sem resultados (lógica apenas em services.py)

# Verificar que services.py usa get_or_create (idempotência)
grep -n "get_or_create" /home/RID/backend/apps/tenants/services.py
# Expected: Customer.objects.get_or_create e Domain.objects.get_or_create

# Teste de normalização
cd /home/RID/backend && . .venv/bin/activate && python3 -c "
from apps.tenants.services import _normalize_schema_name
assert _normalize_schema_name('Acme Corp') == 'acme_corp'
assert len(_normalize_schema_name('A' * 100)) <= 48
print('OK')
"
```

## Referências

- `apps/tenants/services.py` — implementação completa de `provision_tenant_for_user`
- `apps/tenants/signals.py` — thin dispatcher com `threading.Thread`
- `apps/tenants/signals.py:1-25` — docstring com roadmap Celery
- `RockItDown/src/customers/services.py` — origem do padrão (predecessor do RID)
- [Martin Fowler — Service Layer](https://martinfowler.com/eaaCatalog/serviceLayer.html) — padrão arquitectural de referência
