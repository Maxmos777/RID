import "./index.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// During Vite dev server the Django template is not present,
// so inject a mock app-config if the script tag is missing.
if (!document.getElementById("app-config")) {
  const el = document.createElement("script");
  el.id = "app-config";
  el.type = "application/json";
  el.textContent = JSON.stringify({
    tenant: { schema_name: "dev", user_email: "dev@example.com", user_id: "1" },
    api: {
      base_url: "/api/v1",
      langflow_auto_login_url: "/api/v1/langflow/auth/auto-login",
      langflow_base_url: "http://localhost:7860"
    },
    csrf_token: "dev-csrf-token"
  });
  document.head.appendChild(el);
}

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);

