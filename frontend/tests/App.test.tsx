// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../src/app/App";
import { dashboardApi } from "../src/infrastructure/api";
import dashboard from "./dashboard.json";
import catalog from "./catalog.json";
import type { Dashboard } from "../src/domain/dashboard";

beforeEach(() => {
  vi.spyOn(dashboardApi, "catalog").mockResolvedValue(
    catalog as Awaited<ReturnType<typeof dashboardApi.catalog>>,
  );
  vi.spyOn(dashboardApi, "predict").mockResolvedValue(dashboard as Dashboard);
  vi.spyOn(dashboardApi, "history").mockResolvedValue([]);
  vi.spyOn(dashboardApi, "report").mockResolvedValue({
    id: 3,
    mensaje: "Reporte guardado.",
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Dashboard conectado al contrato del motor", () => {
  it("muestra la predicción y los 13 tipos reales, y envía la franja elegida", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findAllByText("572.9", { exact: true });
    await user.click(
      screen.getByRole("button", { name: "Recomendaciones", exact: true }),
    );
    await screen.findByRole("heading", { name: "Todos los tipos de producto" });
    expect(screen.getAllByRole("row")).toHaveLength(14);
    await user.selectOptions(
      screen.getByLabelText("Categoría", { exact: true }),
      "Tea",
    );
    expect(screen.getAllByRole("row")).toHaveLength(5);
    await user.selectOptions(
      screen.getByLabelText("Horario", { exact: true }),
      "06:00–10:59",
    );
    await user.click(
      screen.getByRole("button", { name: "Estimar menú", exact: true }),
    );
    await waitFor(() =>
      expect(dashboardApi.predict).toHaveBeenLastCalledWith(
        expect.objectContaining({
          franja: "06:00–10:59",
          sucursal: "Hell's Kitchen",
          fecha: "2023-06-15",
        }),
        expect.any(AbortSignal),
      ),
    );
  });

  it("permite reintentar un error real de la API y asociar un reporte a la consulta", async () => {
    vi.mocked(dashboardApi.predict).mockRejectedValueOnce(
      new Error("API no disponible"),
    );
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole("alert");
    await user.click(
      screen.getByRole("button", { name: "Reintentar", exact: true }),
    );
    await screen.findAllByText("572.9", { exact: true });
    await user.click(
      screen.getByRole("button", { name: "Configuración", exact: true }),
    );
    await user.type(
      screen.getByLabelText("Describe el problema observado"),
      "Verificar el menú recomendado.",
    );
    await user.click(
      screen.getByRole("button", { name: "Guardar reporte", exact: true }),
    );
    await screen.findByText(/Reporte #3 guardado/);
    expect(dashboardApi.report).toHaveBeenCalledWith(
      dashboard.consulta_id,
      "Verificar el menú recomendado.",
    );
  });
});
