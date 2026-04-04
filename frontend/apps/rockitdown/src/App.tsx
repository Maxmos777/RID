import { useEffect, useState } from "react";
import { readAppConfig, type AppConfig } from "@rid/shared";
import { useLangflowAuth } from "./hooks/useLangflowAuth";

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const { credentials, loading, error } = useLangflowAuth(config);

  useEffect(() => {
    try {
      setConfig(readAppConfig());
    } catch (e) {
      console.error("Failed to read app config:", e);
    }
  }, []);

  if (!config) return <div>Loading config...</div>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem" }}>
      <h1>RockItDown</h1>
      <p>
        Tenant: <strong>{config.tenant.schema_name}</strong>
      </p>
      <p>
        User: <strong>{config.tenant.user_email}</strong>
      </p>
      {loading && <p>Connecting to Langflow...</p>}
      {error && <p style={{ color: "red" }}>Langflow error: {error}</p>}
      {credentials && (
        <p style={{ color: "green" }}>
          Langflow connected. API key: {credentials.api_key.slice(0, 8)}...
        </p>
      )}
    </div>
  );
}

