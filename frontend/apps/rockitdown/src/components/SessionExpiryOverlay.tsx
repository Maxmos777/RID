import { useEffect, useRef } from "react";

const LOGIN_URL = "/login/?next=/flows/";
const HEADING_ID = "session-expiry-heading";

export function SessionExpiryOverlay() {
  const ctaRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    ctaRef.current?.focus();
  }, []);

  const handleLogin = () => {
    window.location.href = LOGIN_URL;
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Tab") {
      // Focus trap: keep focus on the CTA button
      event.preventDefault();
      ctaRef.current?.focus();
    }
  };

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-live="assertive"
      aria-labelledby={HEADING_ID}
      onKeyDown={handleKeyDown}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(0, 0, 0, 0.6)",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "8px",
          padding: "2rem",
          maxWidth: "400px",
          width: "90%",
          textAlign: "center",
          boxShadow: "0 4px 24px rgba(0, 0, 0, 0.2)",
        }}
      >
        <h2
          id={HEADING_ID}
          style={{ margin: "0 0 0.75rem", fontSize: "1.25rem", color: "#111" }}
        >
          Sessão expirada
        </h2>
        <p style={{ margin: "0 0 1.5rem", color: "#555", fontSize: "0.95rem" }}>
          Sua sessão expirou. Faça login novamente para continuar.
        </p>
        <button
          ref={ctaRef}
          type="button"
          onClick={handleLogin}
          style={{
            minHeight: "44px",
            minWidth: "44px",
            padding: "0.75rem 1.5rem",
            fontSize: "1rem",
            fontWeight: 600,
            color: "#fff",
            backgroundColor: "#0b6bcb",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
          }}
        >
          Entrar novamente
        </button>
      </div>
    </div>
  );
}
