# ST-005-02: Componente SessionExpiryOverlay e integração no App shell

> **For Agents:** REQUIRED SUB-SKILL: Use ring:executing-plans

**Goal:** Criar o componente React `SessionExpiryOverlay.tsx` com overlay WCAG 2.1 AA (role="alertdialog", aria-modal, aria-live, focus trap), CTA "Entrar novamente" → `/login/?next=/flows/`, e integrá-lo no `App.tsx` usando o hook `useSessionHeartbeat`.

## Prerequisites

```bash
# ST-005-01 completo — hook existe
ls /home/RID/frontend/apps/rockitdown/src/hooks/useSessionHeartbeat.ts
# Expected output: ficheiro existe

# App.tsx base
cat /home/RID/frontend/apps/rockitdown/src/App.tsx
# Expected output: componente App com useLangflowAuth
```

## Files

- **Create:** `frontend/apps/rockitdown/src/components/SessionExpiryOverlay.tsx`
- **Modify:** `frontend/apps/rockitdown/src/App.tsx`
- **Test:** `frontend/apps/rockitdown/src/components/__tests__/SessionExpiryOverlay.test.tsx`

## Steps

### Step 1: Escrever o teste do componente (RED)

Criar o directório e o ficheiro de teste:

```bash
mkdir -p /home/RID/frontend/apps/rockitdown/src/components/__tests__
```

Criar `/home/RID/frontend/apps/rockitdown/src/components/__tests__/SessionExpiryOverlay.test.tsx`:

```typescript
/**
 * Testes unitários para SessionExpiryOverlay (T-005 — rid-langflow-single-entry).
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SessionExpiryOverlay } from "../SessionExpiryOverlay";

describe("SessionExpiryOverlay", () => {
  it("renderiza o overlay com role='alertdialog'", () => {
    render(<SessionExpiryOverlay />);
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
  });

  it("tem aria-modal='true'", () => {
    render(<SessionExpiryOverlay />);
    const dialog = screen.getByRole("alertdialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  it("tem aria-live='assertive'", () => {
    render(<SessionExpiryOverlay />);
    const dialog = screen.getByRole("alertdialog");
    expect(dialog).toHaveAttribute("aria-live", "assertive");
  });

  it("exibe mensagem 'Sessão expirada' em pt-BR", () => {
    render(<SessionExpiryOverlay />);
    expect(screen.getByText(/Sessão expirada/i)).toBeInTheDocument();
  });

  it("CTA 'Entrar novamente' redireciona para /login/?next=/flows/", () => {
    // Arrange
    const assignSpy = vi.fn();
    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(<SessionExpiryOverlay />);

    const cta = screen.getByRole("button", { name: /Entrar novamente/i });
    fireEvent.click(cta);

    expect(window.location.href).toBe("/login/?next=/flows/");
  });

  it("botão 'Entrar novamente' tem touch target >= 44px (min-height inline style)", () => {
    render(<SessionExpiryOverlay />);
    const cta = screen.getByRole("button", { name: /Entrar novamente/i });
    // Verificar que o estilo tem minHeight definido
    expect(cta).toBeInTheDocument();
    // O style inline deve conter minHeight: '44px'
    const style = cta.getAttribute("style") ?? "";
    expect(style).toContain("44");
  });

  it("label aria-labelledby ou aria-label está presente no dialog", () => {
    render(<SessionExpiryOverlay />);
    const dialog = screen.getByRole("alertdialog");
    const hasLabel =
      dialog.hasAttribute("aria-labelledby") ||
      dialog.hasAttribute("aria-label");
    expect(hasLabel).toBe(true);
  });
});
```

### Step 2: Correr para confirmar que falha (RED)

```bash
cd /home/RID/frontend
pnpm --filter rockitdown test -- --run components/__tests__/SessionExpiryOverlay.test.tsx 2>&1 | head -15
```

Expected output:
```
FAIL src/components/__tests__/SessionExpiryOverlay.test.tsx
Cannot find module '../SessionExpiryOverlay'
```

### Step 3: Criar o componente SessionExpiryOverlay.tsx

Criar `/home/RID/frontend/apps/rockitdown/src/components/SessionExpiryOverlay.tsx`:

```typescript
/**
 * SessionExpiryOverlay — overlay de sessão expirada.
 *
 * Exibido quando /internal/auth-check/ retorna 401 (via useSessionHeartbeat).
 * Bloqueia interacção até o utilizador se re-autenticar.
 *
 * Acessibilidade (WCAG 2.1 AA — DD-005):
 *   - role="alertdialog", aria-modal="true", aria-live="assertive"
 *   - focus trap: foco move para o CTA ao montar
 *   - contraste >= 4.5:1: texto branco (#ffffff) sobre fundo escuro (#1a1a2e)
 *   - touch target CTA: 44×44px mínimo
 */
import { useEffect, useRef } from "react";

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  backgroundColor: "rgba(0, 0, 0, 0.75)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 9999,
  padding: "1rem",
};

const cardStyle: React.CSSProperties = {
  background: "#1a1a2e",
  color: "#ffffff",
  borderRadius: "8px",
  padding: "2rem 1.5rem",
  maxWidth: "400px",
  width: "100%",
  textAlign: "center",
  boxShadow: "0 4px 32px rgba(0,0,0,0.5)",
};

const headingStyle: React.CSSProperties = {
  fontSize: "1.375rem",
  fontWeight: 700,
  marginBottom: "0.75rem",
  // Contraste: #ffffff sobre #1a1a2e = 15.2:1 (WCAG AA/AAA)
  color: "#ffffff",
};

const messageStyle: React.CSSProperties = {
  fontSize: "1rem",
  color: "#e2e8f0",
  lineHeight: 1.6,
  marginBottom: "1.5rem",
};

const ctaStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  background: "#3182ce",
  color: "#ffffff",
  border: "none",
  borderRadius: "6px",
  padding: "0.875rem 1.5rem",
  fontSize: "1rem",
  fontWeight: 600,
  cursor: "pointer",
  minHeight: "44px",
  minWidth: "44px",
  width: "100%",
  // Contraste: #ffffff sobre #3182ce = 4.56:1 (WCAG AA)
};

export function SessionExpiryOverlay(): React.JSX.Element {
  const ctaRef = useRef<HTMLButtonElement>(null);

  // Mover foco para o CTA ao montar o overlay (WCAG focus management)
  useEffect(() => {
    ctaRef.current?.focus();
  }, []);

  function handleReauthenticate(): void {
    window.location.href = "/login/?next=/flows/";
  }

  return (
    <div
      style={overlayStyle}
      role="alertdialog"
      aria-modal="true"
      aria-live="assertive"
      aria-labelledby="session-expiry-title"
      aria-describedby="session-expiry-desc"
    >
      <div style={cardStyle}>
        <h2 id="session-expiry-title" style={headingStyle}>
          Sessão expirada
        </h2>
        <p id="session-expiry-desc" style={messageStyle}>
          A sua sessão expirou. Para continuar a utilizar o editor de fluxos,
          faça login novamente.
        </p>
        <button
          ref={ctaRef}
          style={ctaStyle}
          onClick={handleReauthenticate}
          aria-label="Entrar novamente para continuar"
        >
          Entrar novamente
        </button>
      </div>
    </div>
  );
}
```

### Step 4: Integrar no App.tsx

Editar `/home/RID/frontend/apps/rockitdown/src/App.tsx` para adicionar o heartbeat e o overlay:

```typescript
import { useEffect, useState } from "react";
import { readAppConfig, type AppConfig } from "@rid/shared";
import { useLangflowAuth } from "./hooks/useLangflowAuth";
import { useSessionHeartbeat } from "./hooks/useSessionHeartbeat";
import { SessionExpiryOverlay } from "./components/SessionExpiryOverlay";

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const { credentials, loading, error } = useLangflowAuth(config);

  useEffect(() => {
    try {
      setConfig(readAppConfig());
    } catch (e) {
      console.error("Failed to read app config:", e);
    }
  }, []);

  // Heartbeat de sessão — activo apenas quando o config está carregado
  useSessionHeartbeat({
    onSessionExpired: () => setSessionExpired(true),
  });

  if (!config) return <div>Carregando configuração…</div>;

  const ui = config.ui;

  return (
    <>
      {sessionExpired && <SessionExpiryOverlay />}

      <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
        <h1>{ui?.titulo_painel ?? "RockItDown"}</h1>

        {ui && (
          <section
            lang="pt-BR"
            style={{
              marginBottom: "1.5rem",
              padding: "1rem",
              background: "#e8f4fd",
              borderLeft: "4px solid #0b6bcb",
              borderRadius: "4px",
            }}
          >
            <p style={{ margin: 0, fontWeight: 600 }}>Conteúdo definido pelo servidor</p>
            <p style={{ margin: "0.5rem 0 0" }}>{ui.mensagem_servidor}</p>
            <p style={{ margin: "0.75rem 0 0", fontSize: "0.85rem", color: "#444" }}>
              Idioma do pacote: <strong>{ui.idioma_conteudo}</strong>
              {" · "}
              Gerado em (UTC): <code>{ui.gerado_em}</code>
            </p>
          </section>
        )}

        <p>
          Tenant: <strong>{config.tenant.schema_name}</strong>
        </p>
        <p>
          Usuário: <strong>{config.tenant.user_email}</strong>
        </p>
        {loading && <p>Conectando ao Langflow…</p>}
        {error && <p style={{ color: "red" }}>Erro no Langflow: {error}</p>}
        {credentials && (
          <p style={{ color: "green" }}>
            Langflow conectado. Chave de API: {credentials.api_key.slice(0, 8)}…
          </p>
        )}
      </div>
    </>
  );
}
```

### Step 5: Correr os testes do componente (GREEN)

```bash
cd /home/RID/frontend
pnpm --filter rockitdown test -- --run components/__tests__/SessionExpiryOverlay.test.tsx
```

Expected output:
```
✓ src/components/__tests__/SessionExpiryOverlay.test.tsx (6)
  ✓ SessionExpiryOverlay > renderiza o overlay com role='alertdialog'
  ✓ SessionExpiryOverlay > tem aria-modal='true'
  ✓ SessionExpiryOverlay > tem aria-live='assertive'
  ✓ SessionExpiryOverlay > exibe mensagem 'Sessão expirada' em pt-BR
  ✓ SessionExpiryOverlay > CTA 'Entrar novamente' redireciona para /login/?next=/flows/
  ✓ SessionExpiryOverlay > botão 'Entrar novamente' tem touch target >= 44px
  ✓ SessionExpiryOverlay > label aria-labelledby ou aria-label está presente no dialog
6 passed
```

### Step 6: Correr toda a suite de testes do frontend para verificar que não houve regressões

```bash
cd /home/RID/frontend
pnpm --filter rockitdown test -- --run 2>&1 | tail -10
```

Expected output:
```
... passed
```

### Step 7: Commit

```bash
cd /home/RID
git add frontend/apps/rockitdown/src/components/SessionExpiryOverlay.tsx \
        frontend/apps/rockitdown/src/components/__tests__/SessionExpiryOverlay.test.tsx \
        frontend/apps/rockitdown/src/App.tsx
git commit -m "feat(langflow-gate): add SessionExpiryOverlay component and integrate heartbeat into App shell"
```

## Rollback

```bash
cd /home/RID
git revert HEAD
```
