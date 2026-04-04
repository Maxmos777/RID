import { UseRequestProcessor } from "@/controllers/API/services/request-processor";
import type { useQueryFunctionType } from "@/types/api";

// Ponto de extensão: loading state primário da aplicação.
// Pode ser usado para verificar sessão Django antes de renderizar o Langflow.
export const useCustomPrimaryLoading: useQueryFunctionType<undefined, null> = (
  options,
) => {
  const { query } = UseRequestProcessor();

  return query(["usePrimaryLoading"], async () => null, options);
};
