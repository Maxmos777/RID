// Feature flags do RID Platform para o frontend Langflow.
// Cada flag desactivada tem comentário com o motivo.
// Referência upstream: src/frontend/src/customization/feature-flags.ts@1.8.3

export const ENABLE_DARK_MODE = true;
export const ENABLE_API = true;

// Desactivado: o RID não usa o marketplace público do Langflow
export const ENABLE_LANGFLOW_STORE = false;

export const ENABLE_PROFILE_ICONS = true;
export const ENABLE_SOCIAL_LINKS = true;
export const ENABLE_BRANDING = true;

// Desactivado: funcionalidades MVP do Langflow Cloud não usadas no RID
export const ENABLE_MVPS = false;

// Desactivado: rota /:customParam não usada na arquitectura RID
export const ENABLE_CUSTOM_PARAM = false;

// Desactivado: painel de integrações externas não relevante no contexto multi-tenant RID
export const ENABLE_INTEGRATIONS = false;

// Desactivado: produto DataStax não usado
export const ENABLE_DATASTAX_LANGFLOW = false;

export const ENABLE_FILE_MANAGEMENT = true;
export const ENABLE_PUBLISH = true;
export const ENABLE_WIDGET = true;
export const ENABLE_VOICE_ASSISTANT = true;

// Desactivado: playground de imagens não necessário na fase actual
export const ENABLE_IMAGE_ON_PLAYGROUND = false;

export const ENABLE_MCP = true;

// Desactivado: aviso MCP já não relevante após 1.8.x
export const ENABLE_MCP_NOTICE = false;

// Desactivado: knowledge bases não fazem parte do MVP RID
export const ENABLE_KNOWLEDGE_BASES = false;

export const ENABLE_MCP_COMPOSER =
  import.meta.env.LANGFLOW_MCP_COMPOSER_ENABLED === "true";

export const ENABLE_NEW_SIDEBAR = true;

// Desactivado: experiência agentic ainda não relevante no MVP RID
export const LANGFLOW_AGENTIC_EXPERIENCE = false;

export const ENABLE_INSPECTION_PANEL = true;

// Desactivado: credenciais via fetch não necessárias na arquitectura RID (auth via cookie Django)
export const ENABLE_FETCH_CREDENTIALS = false;
