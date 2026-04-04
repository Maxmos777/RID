/**
 * Design tokens — single source of truth for colours, spacing, typography.
 * Import into Tailwind config or CSS-in-JS as needed.
 */
export const colors = {
  brand: {
    50: "#eff6ff",
    100: "#dbeafe",
    500: "#3b82f6",
    600: "#2563eb",
    900: "#1e3a8a"
  },
  neutral: {
    50: "#f9fafb",
    100: "#f3f4f6",
    700: "#374151",
    900: "#111827"
  }
} as const;

export const spacing = {
  xs: "0.25rem",
  sm: "0.5rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  "2xl": "3rem"
} as const;

