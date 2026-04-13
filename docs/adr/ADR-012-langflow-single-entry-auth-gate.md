# ADR-012 — Auth Gate via Reverse Proxy para entrada única no editor de fluxos

**Data:** 2026-04-05
**Data de aceitação:** 2026-04-06
**Estado:** Accepted
**Autores:** ring:architect
**Revisores:** ring:backend-engineer, ring:devops
**Contexto de código:** `docker-compose.yml:131-158`, `backend/api/routers/langflow_auth.py`, `backend/api/services/langflow_client.py`

---

## Contexto

O editor de fluxos do RID está exposto numa porta pública separada do domínio da plataforma, fora do perímetro de autenticação. Qualquer utilizador — autenticado ou não na plataforma — pode aceder directamente ao editor sem que a identidade seja verificada pelo sistema de controlo de acesso da plataforma. Isto resulta em trilhos de auditoria incompletos, risco de acesso não autorizado a dados de tenant, e confusão operacional por existirem dois endereços distintos para a mesma ferramenta. O padrão de referência interno resolve este problema servindo o editor atrás do login da plataforma; o RID diverge neste ponto por expor o editor como contentor com porta pública.

## Decisão

Adoptamos o padrão de Container-native Edge Router com forwardAuth como Auth Gate: todo o tráfego para `/flows/*` passa pelo **Traefik**, a correr como container Docker no `docker-compose.yml` na mesma rede dos outros serviços (`rid-network`). O Traefik usa o mecanismo `forwardAuth` (equivalente ao `auth_request` do nginx) para validar cada pedido contra um Auth Check Endpoint no Application Server antes de encaminhar para o Editor Interno. A configuração é feita via labels Docker nos serviços — sem ficheiros de configuração externos. O Editor Interno deixa de ter porta exposta no host em staging e produção (porta `:7861` removida).

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| Paridade total com o padrão de referência: SPA do editor servida directamente pelo Application Server | Requer rebuild do frontend do Editor Interno e pipeline de build/deploy separado; complexidade de implementação superior ao MVP; reservada como Fase 2 (F-006) |
| Manter porta pública com reforço de autenticação no Editor Interno | Não resolve o problema de perímetro: a validação de identidade continuaria fora do sistema de controlo de acesso da plataforma; auditoria permaneceria incompleta; dois endereços distintos persistiriam |
| nginx como container Docker (alternativa ao Traefik) | nginx requer ficheiros de configuração externos (`nginx.conf`) versionados separadamente do docker-compose; `auth_request` é equivalente ao `forwardAuth` do Traefik mas a gestão de configuração é menos Docker-native; Traefik escolhido por suporte nativo a labels Docker, descoberta automática de serviços via socket Docker, e ausência de ficheiros de configuração externos |

## Consequências Positivas

- Fechamento imediato da segunda entrada pública sem modificação do Editor Interno.
- Reutilização do sistema de sessão existente do Application Server — sem nova lógica de autenticação.
- Auditoria de acesso integrada no perímetro da plataforma (F-005) com um único ponto de controlo.
- Isolamento de tenant garantido pelo Auth Check Endpoint usando o middleware multi-tenant existente.
- Extensível para Fase 2 (F-006): quando o Editor Interno for servido directamente pelo Application Server, o Auth Gate pode ser removido sem impacto no modelo de segurança.
- WebSockets suportados via configuração explícita de headers no proxy.
- Traefik adicionado ao docker-compose no perfil `langflow` — activado apenas quando o Editor Interno está em uso.
- Configuração de routing via labels Docker — versionada no docker-compose.yml, sem ficheiros de configuração externos.
- Host header original configurado explicitamente no middleware forwardAuth para compatibilidade com django-tenants (resolução de tenant por domínio).
- Session Expiry Overlay activado por heartbeat periódico no cliente (não por resposta do proxy) — compatível com o comportamento 302 do Traefik para navegação de browser.

## Consequências Negativas / Trade-offs

- Introduz o Traefik como novo componente de infraestrutura a configurar, manter e monitorizar.
- Adiciona latência de forwardAuth no hot path de cada pedido para `/flows/*` (target: overhead < 30ms, p95 Auth Check < 20ms).
- Conexões WebSocket abertas não são terminadas automaticamente quando a sessão expira — limitação conhecida do MVP, documentada no TRD.
- A paridade operacional total com o padrão de referência (SPA servida pelo Application Server) fica diferida para Fase 2, mantendo uma diferença de topologia entre os dois repositórios no médio prazo.
- Configuração de timeout longo para WebSocket no Traefik requer documentação no runbook operacional.
- Acesso ao socket Docker pelo Traefik requer gestão cuidadosa de permissões (read-only).

## Compliance

Verificar que o Editor Interno não tem porta exposta no host em staging/produção:

```bash
# Verificar ausência de mapeamento de porta pública do editor em ambientes não-locais
grep -n "7861" docker-compose.yml
grep -n "7860" docker-compose.yml
# Em staging/produção, nenhum destes deve resultar em mapeamento host:container activo
```

Verificar que todo o tráfego para `/flows/*` passa pelo sub-request de validação:

```bash
# Verificar configuração do Auth Gate no Reverse Proxy
grep -rn "auth_request\|forwardAuth\|/flows/" config/nginx/ config/traefik/ 2>/dev/null || true
```

Verificar que a validação de sessão não está duplicada no Async API Runtime:

```bash
# Não deve existir lógica de validação de sessão de plataforma em routers FastAPI para /flows/
grep -rn "session\|auth_check" backend/api/routers/ | grep -v "langflow_auth"
```

## Referências

- `docs/pre-dev/rid-langflow-single-entry/trd.md` — especificação técnica completa (Gate 3)
- `docs/pre-dev/rid-langflow-single-entry/prd.md` — requisitos de produto (Gate 1)
- `docker-compose.yml:131-158` — configuração actual do Editor Interno (porta 7861:7860 a restringir)
- `backend/api/routers/langflow_auth.py` — bridge de auto-login existente (complementar, não substituído)
- `backend/api/services/langflow_client.py` — cliente HTTP para o Editor Interno
- `docs/adr/ADR-001-sync-to-async-tenant-isolation.md` — padrão de isolamento de tenant em contexto async
- `docs/adr/ADR-009-langflow-database-integration.md` — auth Langflow via API Key (contexto do bridge existente)
