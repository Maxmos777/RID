import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SessionExpiryOverlay } from "../SessionExpiryOverlay";
import "@testing-library/jest-dom/vitest";

describe("SessionExpiryOverlay", () => {
  beforeEach(() => {
    // Reset location mock before each test
    Object.defineProperty(window, "location", {
      writable: true,
      value: { href: "" },
    });
  });

  it("renders with role alertdialog", () => {
    render(<SessionExpiryOverlay />);

    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
  });

  it("has aria-modal attribute", () => {
    render(<SessionExpiryOverlay />);

    expect(screen.getByRole("alertdialog")).toHaveAttribute(
      "aria-modal",
      "true"
    );
  });

  it("has aria-live assertive", () => {
    render(<SessionExpiryOverlay />);

    expect(screen.getByRole("alertdialog")).toHaveAttribute(
      "aria-live",
      "assertive"
    );
  });

  it("displays 'Sessão expirada' heading", () => {
    render(<SessionExpiryOverlay />);

    expect(
      screen.getByRole("heading", { name: /sessão expirada/i })
    ).toBeInTheDocument();
  });

  it("redirects to login page when CTA is clicked", async () => {
    const user = userEvent.setup();

    render(<SessionExpiryOverlay />);

    const button = screen.getByRole("button", { name: /entrar novamente/i });
    await user.click(button);

    expect(window.location.href).toBe("/login/?next=/flows/");
  });

  it("CTA button meets 44px minimum touch target", () => {
    render(<SessionExpiryOverlay />);

    const button = screen.getByRole("button", { name: /entrar novamente/i });

    expect(button.style.minHeight).toBe("44px");
  });

  it("has aria-labelledby pointing to the heading", () => {
    render(<SessionExpiryOverlay />);

    const dialog = screen.getByRole("alertdialog");
    const headingId = dialog.getAttribute("aria-labelledby");

    expect(headingId).toBeTruthy();
    expect(document.getElementById(headingId!)).toHaveTextContent(
      "Sessão expirada"
    );
  });
});
