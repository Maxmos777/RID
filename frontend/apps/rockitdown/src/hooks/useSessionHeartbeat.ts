import { useEffect } from "react";

const HEARTBEAT_INTERVAL_MS = 120_000;
const AUTH_CHECK_URL = "/internal/auth-check/";

interface UseSessionHeartbeatOptions {
  onSessionExpired: () => void;
}

export function useSessionHeartbeat({ onSessionExpired }: UseSessionHeartbeatOptions): void {
  useEffect(() => {
    const checkSession = async (): Promise<void> => {
      try {
        const response = await fetch(AUTH_CHECK_URL, { credentials: "same-origin" });
        if (response.status === 401) {
          onSessionExpired();
        }
      } catch {
        // Network error — silently ignored
      }
    };

    const intervalId = setInterval(checkSession, HEARTBEAT_INTERVAL_MS);

    return () => {
      clearInterval(intervalId);
    };
  }, [onSessionExpired]);
}
