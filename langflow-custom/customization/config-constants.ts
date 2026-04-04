// Constantes de configuração do RID Platform para o frontend Langflow.
// PROXY_TARGET aponta para o nome do serviço Docker (rid-langflow) em vez de localhost.
// Referência upstream: src/frontend/src/customization/config-constants.ts@1.8.3

export const BASENAME = "";
export const PORT = 3000;

// Nome do serviço Docker definido em docker-compose.yml (ADR-006)
export const PROXY_TARGET = "http://rid-langflow:7860";

export const API_ROUTES = ["^/api/v1/", "^/api/v2/", "/health"];
export const BASE_URL_API = "/api/v1/";
export const BASE_URL_API_V2 = "/api/v2/";
export const HEALTH_CHECK_URL = "/health_check";
export const DOCS_LINK = "https://docs.langflow.org";

export default {
  DOCS_LINK,
  BASENAME,
  PORT,
  PROXY_TARGET,
  API_ROUTES,
  BASE_URL_API,
  BASE_URL_API_V2,
  HEALTH_CHECK_URL,
};
