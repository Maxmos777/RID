// Ponto de extensão: geração de token para autenticação Langflow.
// No RID, a auth é gerida via TenantAwareBackend (ADR-005) e django-allauth.
// Implementar aqui se for necessário bridge de token Django → Langflow.
export const useGenerateToken = (): any => {
  const tokenFunction = (() => null) as any;
  tokenFunction.token = null;
  return tokenFunction;
};
