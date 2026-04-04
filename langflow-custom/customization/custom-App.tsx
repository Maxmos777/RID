import App from "../App";

// Ponto de extensão: envolver App com providers RID se necessário no futuro
// (ex: TenantContext, ThemeProvider customizado)
export default function CustomApp() {
  return <App />;
}
