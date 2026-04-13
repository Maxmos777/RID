# ST-005-01: Hook useSessionHeartbeat (polling /internal/auth-check/ a cada 120s)

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar o hook `useSessionHeartbeat.ts` em `frontend/apps/rockitdown/src/hooks/` que faz polling a `GET /internal/auth-check/` a cada 120 segundos, chama `onSessionExpired()` em caso de HTTP 401, ignora erros de rede, e cancela o interval no cleanup do `useEffect`.

## Prerequisites

```bash
# Frontend existe e tem hooks
ls /home/RID/frontend/apps/rockitdown/src/hooks/
# Expected output: useLangflowAuth.ts

# package.json com React 18 e TypeScript
cat /home/RID/frontend/apps/rockitdown/package.json | grep -E '"react"|"typescript"' | head -5
# Expected output: versões de react e typescript

# Verificar que não existe useSessionHeartbeat já
ls /home/RID/frontend/apps/rockitdown/src/hooks/useSessionHeartbeat.ts 2>/dev/null && echo "JÁ EXISTE" || echo "não existe — criar"
# Expected output: não existe — criar
```

## Files

- **Create:** `frontend/apps/rockitdown/src/hooks/useSessionHeartbeat.ts`
- **Test:** `frontend/apps/rockitdown/src/hooks/__tests__/useSessionHeartbeat.test.ts`

## Steps

### Step 1: Verificar o setup de testes do frontend

```bash
ls /home/RID/frontend/apps/rockitdown/
cat /home/RID/frontend/apps/rockitdown/package.json | grep -E '"vitest"|"jest"|"@testing-library"' | head -10
```

Expected output: configuração de testes existente (vitest ou jest)

### Step 2: Escrever o teste (RED)

Criar `/home/RID/frontend/apps/rockitdown/src/hooks/__tests__/useSessionHeartbeat.test.ts`:

```typescript
/**
 * Testes unitários para useSessionHeartbeat hook (T-005 — rid-langflow-single-entry).
 *
 * Usa vitest (ou jest) + @testing-library/react-hooks (ou renderHook de @testing-library/react).
 * Timers são controlados com vi.useFakeTimers() para evitar esperar 120s reais.
 */
import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useSessionHeartbeat } from "../useSessionHeartbeat";

describe("useSessionHeartbeat", () => {
  const INTERVAL_MS = 120_000;

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("chama onSessionExpired quando auth-check retorna 401", async () => {
    const onSessionExpired = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      status: 401,
    });

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    // Avançar o timer para disparar o primeiro heartbeat
    await act(async () => {
      vi.advanceTimersByTime(INTERVAL_MS);
    });

    expect(onSessionExpired).toHaveBeenCalledTimes(1);
  });

  it("NÃO chama onSessionExpired quando auth-check retorna 200", async () => {
    const onSessionExpired = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      status: 200,
    });

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await act(async () => {
      vi.advanceTimersByTime(INTERVAL_MS);
    });

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("NÃO chama onSessionExpired quando auth-check retorna 403", async () => {
    const onSessionExpired = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      status: 403,
    });

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await act(async () => {
      vi.advanceTimersByTime(INTERVAL_MS);
    });

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("NÃO chama onSessionExpired em erro de rede (fetch lança excepção)", async () => {
    const onSessionExpired = vi.fn();

    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await act(async () => {
      vi.advanceTimersByTime(INTERVAL_MS);
    });

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("cancela o interval no cleanup (unmount)", async () => {
    const onSessionExpired = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({ status: 200 });

    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");

    const { unmount } = renderHook(() =>
      useSessionHeartbeat({ onSessionExpired })
    );

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalledTimes(1);
  });

  it("envia fetch com credentials: same-origin", async () => {
    const onSessionExpired = vi.fn();
    const fetchMock = vi.fn().mockResolvedValue({ status: 200 });
    global.fetch = fetchMock;

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await act(async () => {
      vi.advanceTimersByTime(INTERVAL_MS);
    });

    expect(fetchMock).toHaveBeenCalledWith("/internal/auth-check/", {
      credentials: "same-origin",
    });
  });

  it("usa intervalo de exactamente 120000ms", async () => {
    const onSessionExpired = vi.fn();
    global.fetch = vi.fn().mockResolvedValue({ status: 401 });

    const setIntervalSpy = vi.spyOn(globalThis, "setInterval");

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    expect(setIntervalSpy).toHaveBeenCalledWith(expect.any(Function), 120_000);
  });
});
```

### Step 3: Correr para confirmar que falha (RED)

```bash
cd /home/RID/frontend
pnpm --filter rockitdown test -- --run hooks/__tests__/useSessionHeartbeat.test.ts 2>&1 | head -20
```

Expected output:
```
FAIL src/hooks/__tests__/useSessionHeartbeat.test.ts
Cannot find module '../useSessionHeartbeat'
```

### Step 4: Criar o hook useSessionHeartbeat.ts

Criar `/home/RID/frontend/apps/rockitdown/src/hooks/useSessionHeartbeat.ts`:

```typescript
/**
 * useSessionHeartbeat — polling periódico de /internal/auth-check/ para detectar sessão expirada.
 *
 * Comportamento:
 *   - Faz GET /internal/auth-check/ a cada 120 segundos (credentials: same-origin).
 *   - Chama onSessionExpired() se a resposta for HTTP 401.
 *   - Ignora silenciosamente erros de rede (não activa overlay em falhas transitórias).
 *   - HTTP 403 (tenant inválido) é silencioso — diferente de expiração de sessão.
 *   - Cancela o setInterval no cleanup do useEffect (evita memory leaks).
 *
 * Referência: TRD Component 3, dependency-map §5.1–5.3.
 */
import { useEffect } from "react";

const HEARTBEAT_INTERVAL_MS = 120_000; // 2 minutos
const AUTH_CHECK_URL = "/internal/auth-check/";

interface UseSessionHeartbeatOptions {
  /** Chamada quando /internal/auth-check/ retorna HTTP 401. */
  onSessionExpired: () => void;
}

/**
 * Hook que activa heartbeat de sessão enquanto montado.
 * Deve ser usado no shell component que envolve o editor de fluxos.
 */
export function useSessionHeartbeat({
  onSessionExpired,
}: UseSessionHeartbeatOptions): void {
  useEffect(() => {
    const checkSession = async (): Promise<void> => {
      try {
        const response = await fetch(AUTH_CHECK_URL, {
          credentials: "same-origin",
        });
        if (response.status === 401) {
          onSessionExpired();
        }
        // 200 → sessão válida, continuar silenciosamente
        // 403 → tenant inválido, silencioso (não é expiração de sessão)
      } catch {
        // Erro de rede → silencioso (não activar overlay por falha transitória)
      }
    };

    const intervalId = setInterval(checkSession, HEARTBEAT_INTERVAL_MS);

    // Cleanup obrigatório: cancela o interval quando o componente desmonta
    return () => {
      clearInterval(intervalId);
    };
  }, [onSessionExpired]);
}
```

### Step 5: Correr os testes (GREEN)

```bash
cd /home/RID/frontend
pnpm --filter rockitdown test -- --run hooks/__tests__/useSessionHeartbeat.test.ts
```

Expected output:
```
✓ src/hooks/__tests__/useSessionHeartbeat.test.ts (6)
  ✓ useSessionHeartbeat > chama onSessionExpired quando auth-check retorna 401
  ✓ useSessionHeartbeat > NÃO chama onSessionExpired quando auth-check retorna 200
  ✓ useSessionHeartbeat > NÃO chama onSessionExpired quando auth-check retorna 403
  ✓ useSessionHeartbeat > NÃO chama onSessionExpired em erro de rede (fetch lança excepção)
  ✓ useSessionHeartbeat > cancela o interval no cleanup (unmount)
  ✓ useSessionHeartbeat > envia fetch com credentials: same-origin
  ✓ useSessionHeartbeat > usa intervalo de exactamente 120000ms
6 passed
```

### Step 6: Commit

```bash
cd /home/RID
git add frontend/apps/rockitdown/src/hooks/useSessionHeartbeat.ts frontend/apps/rockitdown/src/hooks/__tests__/useSessionHeartbeat.test.ts
git commit -m "feat(langflow-gate): add useSessionHeartbeat hook (120s polling, 401 detection, cleanup)"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
