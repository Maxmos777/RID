import { useEffect, useState } from "react";
import type { AppConfig, LangflowCredentials } from "@rid/shared";

interface UseLangflowAuthResult {
  credentials: LangflowCredentials | null;
  loading: boolean;
  error: string | null;
}

/**
 * Fetches Langflow credentials via the Django/FastAPI auto-login bridge.
 *
 * Flow:
 *   1. Call GET /api/v1/langflow/auth/auto-login
 *      (Django session cookie is sent automatically by the browser).
 *   2. Store returned access_token and api_key in memory (not localStorage).
 *   3. Re-runs when config changes (i.e., once on mount).
 */
export function useLangflowAuth(config: AppConfig | null): UseLangflowAuthResult {
  const [credentials, setCredentials] = useState<LangflowCredentials | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!config) return;
    const cfg: AppConfig = config;

    let cancelled = false;

    async function fetchCredentials() {
      setLoading(true);
      setError(null);

      try {
        const resp = await fetch(cfg.api.langflow_auto_login_url, {
          credentials: "include",
          headers: {
            "X-CSRFToken": cfg.csrf_token
          }
        });

        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(`${resp.status}: ${text}`);
        }

        const data = (await resp.json()) as LangflowCredentials;
        if (!cancelled) setCredentials(data);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void fetchCredentials();

    return () => {
      cancelled = true;
    };
  }, [config]);

  return { credentials, loading, error };
}

