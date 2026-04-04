import {
  type NavigateFunction,
  type NavigateOptions,
  type To,
  useNavigate,
  useParams,
} from "react-router-dom";
import { ENABLE_CUSTOM_PARAM } from "../feature-flags";

// ENABLE_CUSTOM_PARAM=false no RID → comportamento idêntico ao useNavigate padrão.
// Manter o ponto de extensão para caso o RID precise de prefixo de rota por tenant.
export function useCustomNavigate(): NavigateFunction {
  const domNavigate = useNavigate();
  const { customParam } = useParams();

  function navigate(to: To | number, options?: NavigateOptions) {
    if (typeof to === "number") {
      domNavigate(to);
    } else {
      domNavigate(
        ENABLE_CUSTOM_PARAM && typeof to === "string" && to[0] === "/"
          ? `/${customParam}${to}`
          : to,
        options,
      );
    }
  }

  return navigate as NavigateFunction;
}
