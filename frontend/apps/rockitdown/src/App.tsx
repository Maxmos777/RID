import { useCallback, useEffect, useState } from "react";
import { readAppConfig, type AppConfig } from "@rid/shared";
import { useLangflowAuth } from "./hooks/useLangflowAuth";
import { useSessionHeartbeat } from "./hooks/useSessionHeartbeat";
import { SessionExpiryOverlay } from "./components/SessionExpiryOverlay";

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);
  const { credentials, loading, error } = useLangflowAuth(config);

  useSessionHeartbeat({
    onSessionExpired: useCallback(() => setSessionExpired(true), []),
  });

  useEffect(() => {
    try {
      setConfig(readAppConfig());
    } catch (e) {
      console.error("Failed to read app config:", e);
    }
  }, []);

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

