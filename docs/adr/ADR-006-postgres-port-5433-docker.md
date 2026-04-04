# ADR-006 — PostgreSQL na porta 5433 via Docker (evitar conflito com instância local)

**Data:** 2026-04-03
**Estado:** Accepted
**Autores:** ring:devops-engineer
**Revisores:** ring:governance-specialist
**Contexto de código:** `docker-compose.yml:40-44`, `backend/.env:6`

---

## Contexto

O ambiente de desenvolvimento usa Docker para o PostgreSQL (`postgres:16-alpine`) via `docker-compose.yml`. A porta padrão do PostgreSQL é 5432. O servidor onde o projecto foi desenvolvido já tem uma instância PostgreSQL 14 local a correr na porta 5432 (cluster `main`, gerida pelo sistema operativo).

Se o container Docker mapear para `host:5432`, o `docker compose up` falha com `address already in use` — ou, pior, o Django conecta-se à instância local em vez do container Docker, usando credenciais ou base de dados errados.

## Decisão

O container PostgreSQL Docker é mapeado para a porta **5433 no host** (`ports: "5433:5432"`). O ficheiro `.env` do backend aponta para `DATABASE_PORT=5433`. O container continua a usar 5432 internamente — outros serviços Docker (ex: `backend` container) usam o nome de serviço `db:5432` sem necessidade de ajuste.

```yaml
# docker-compose.yml
db:
  ports:
    - "5433:5432"   # host:5433 -> container:5432
```

```env
# backend/.env
DATABASE_HOST=localhost
DATABASE_PORT=5433
```

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Parar a instância PostgreSQL local (porta 5432 livre) | Intrusivo: a instância local pode ter outras bases de dados activas (RockItDown, projectos pessoais). Requer intervenção manual em cada setup de máquina nova. |
| Usar apenas networking Docker (sem `ports`) | O Django a correr localmente (fora de Docker) não consegue atingir o container sem port mapping. Obriga a sempre correr o backend dentro de Docker. |
| Mudar a porta interna do container para 5433 | Não standard: o PostgreSQL interno esperaria configuração extra. Complica troubleshooting dentro do container. |
| `DATABASE_HOST=db` com networking Docker | Só funciona se o Django correr dentro de Docker. Incompatível com `python manage.py` local (desenvolvimento, migrações, testes). |

## Consequências Positivas

- Sem conflito com instâncias PostgreSQL locais (porta 5432 livre).
- Django local (`python manage.py`, `pytest`) conecta directamente via `localhost:5433`.
- Container `backend` Docker conecta via `db:5432` (networking interno) sem ajuste.
- `.env.example` documenta a convenção para novos developers.

## Consequências Negativas / Trade-offs

- **Porta não-standard causa confusão no onboarding:** desenvolvedores que tentam conectar via ferramentas GUI (DBeaver, pgAdmin, TablePlus) com a porta padrão 5432 não conseguem. É o principal risco de suporte.
- **`.env` fora de sync com `docker-compose.yml`:** se alguém mudar a porta no `docker-compose.yml` sem actualizar o `.env`, o Django falha a conectar sem mensagem de erro óbvia. Requer disciplina ou um script de validação.
- **Específico ao ambiente de desenvolvimento:** em produção (Kubernetes, RDS, etc.) a porta 5432 standard será usada. O `docker-compose.yml` é apenas para desenvolvimento local.

## Compliance

```bash
# Verificar que .env e docker-compose.yml estão em sync
COMPOSE_PORT=$(grep -A 3 "ports:" /home/RID/docker-compose.yml | grep "5432" | sed 's/.*"\([0-9]*\):5432".*/\1/')
ENV_PORT=$(grep "DATABASE_PORT" /home/RID/backend/.env | cut -d= -f2)
[ "$COMPOSE_PORT" = "$ENV_PORT" ] && echo "OK: portas em sync ($COMPOSE_PORT)" || echo "ERRO: portas divergem (compose=$COMPOSE_PORT, env=$ENV_PORT)"

# Verificar que o container está acessível na porta correcta
docker compose -f /home/RID/docker-compose.yml ps | grep "5433"
# Expected: rid-db ... 0.0.0.0:5433->5432/tcp
```

**Nota para onboarding:** adicionar ao `README.md` do projecto:
> "O PostgreSQL Docker está na porta **5433** (não 5432). Configurar clientes GUI com `localhost:5433`."

## Referências

- `docker-compose.yml:40-44` — mapeamento de portas do serviço `db`
- `backend/.env:5-7` — configuração de BD com porta 5433
- `backend/.env.example` — documentação para novos developers
- `Makefile` — comando `make up` que inicia os serviços Docker
