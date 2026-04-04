import { useEffect, useState } from "react";
import { useDarkStore } from "@/stores/darkStore";

// Gestão de tema com persistência em localStorage.
// Suporta: "light" | "dark" | "system" (default: segue o sistema).
const useTheme = () => {
  const [systemTheme, setSystemTheme] = useState(false);
  const { setDark, dark } = useDarkStore((state) => ({
    setDark: state.setDark,
    dark: state.dark,
  }));

  const handleSystemTheme = () => {
    if (typeof window !== "undefined") {
      setDark(window.matchMedia("(prefers-color-scheme: dark)").matches);
    }
  };

  useEffect(() => {
    const pref = localStorage.getItem("themePreference");
    if (pref === "light") {
      setDark(false);
      setSystemTheme(false);
    } else if (pref === "dark") {
      setDark(true);
      setSystemTheme(false);
    } else {
      setSystemTheme(true);
      handleSystemTheme();
    }
  }, []);

  useEffect(() => {
    if (!systemTheme || typeof window === "undefined") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [systemTheme]);

  const setThemePreference = (theme: "light" | "dark" | "system") => {
    if (theme === "light") { setDark(false); setSystemTheme(false); }
    else if (theme === "dark") { setDark(true); setSystemTheme(false); }
    else { setSystemTheme(true); handleSystemTheme(); }
    localStorage.setItem("themePreference", theme);
  };

  return { systemTheme, dark, setThemePreference };
};

export default useTheme;
