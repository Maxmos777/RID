import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useSessionHeartbeat } from "../useSessionHeartbeat";

describe("useSessionHeartbeat", () => {
  const onSessionExpired = vi.fn();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("calls onSessionExpired when server returns 401", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ status: 401 } as Response);

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(120_000);

    expect(onSessionExpired).toHaveBeenCalledOnce();
  });

  it("does not call onSessionExpired when server returns 200", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ status: 200 } as Response);

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(120_000);

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("does not call onSessionExpired when server returns 403", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ status: 403 } as Response);

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(120_000);

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("ignores network errors silently", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new TypeError("Failed to fetch"));

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(120_000);

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("clears interval on unmount", async () => {
    vi.mocked(fetch).mockResolvedValue({ status: 401 } as Response);

    const { unmount } = renderHook(() =>
      useSessionHeartbeat({ onSessionExpired })
    );

    unmount();

    await vi.advanceTimersByTimeAsync(120_000);

    expect(onSessionExpired).not.toHaveBeenCalled();
  });

  it("sends request with credentials same-origin", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ status: 200 } as Response);

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(120_000);

    expect(fetch).toHaveBeenCalledWith("/internal/auth-check/", {
      credentials: "same-origin",
    });
  });

  it("polls every 120 000 ms", async () => {
    vi.mocked(fetch).mockResolvedValue({ status: 200 } as Response);

    renderHook(() => useSessionHeartbeat({ onSessionExpired }));

    await vi.advanceTimersByTimeAsync(119_999);
    expect(fetch).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);
    expect(fetch).toHaveBeenCalledOnce();

    await vi.advanceTimersByTimeAsync(120_000);
    expect(fetch).toHaveBeenCalledTimes(2);
  });
});
