import {
  BASE_URL_API,
  HEALTH_CHECK_URL,
} from "@/customization/config-constants";

export function getBaseUrl(): string {
  return BASE_URL_API || "/api/v1/";
}

export function getHealthCheckUrl(): string {
  return HEALTH_CHECK_URL || "/health";
}

// Ajustado para docs RID (upstream aponta para langflow.org)
export const LangflowButtonRedirectTarget = () => {
  return "https://docs.ridplatform.com";
};
