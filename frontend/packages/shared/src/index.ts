export * from "./types";
export * from "./tokens";

/**
 * Reads the server-injected AppConfig from the Django template.
 *
 * Django injects a JSON blob into <script id="app-config">.
 * This function parses it once at boot time.
 */
export function readAppConfig(): import("./types").AppConfig {
  const el = document.getElementById("app-config");
  if (!el || !el.textContent) {
    throw new Error(
      "app-config script tag not found — is the Django template correct?"
    );
  }
  return JSON.parse(el.textContent) as import("./types").AppConfig;
}

