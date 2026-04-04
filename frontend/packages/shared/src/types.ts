/**
 * Shared TypeScript types used across all RID frontend apps.
 *
 * AppConfig is injected server-side by Django's RockItDownSPA view
 * and read from <script id="app-config"> in the HTML entry point.
 */
export interface TenantInfo {
  schema_name: string;
  user_email: string;
  user_id: string;
}

export interface ApiConfig {
  base_url: string;
  langflow_auto_login_url: string;
  langflow_base_url: string;
}

export interface AppConfig {
  tenant: TenantInfo;
  api: ApiConfig;
  csrf_token: string;
}

export interface LangflowCredentials {
  access_token: string;
  api_key: string;
}

