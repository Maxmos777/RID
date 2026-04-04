import { useMemo } from "react";

export function useCustomIsLocalConnection(): boolean {
  return useMemo(() => {
    const local = ["localhost", "127.0.0.1", "0.0.0.0"];
    return local.includes(window.location.hostname);
  }, []);
}
