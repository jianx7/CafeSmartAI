import type {
  Catalog,
  Dashboard,
  DashboardGateway,
  HistoryEntry,
  Query,
} from "../domain/dashboard";

const baseUrl = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const signal = init.signal
    ? AbortSignal.any([init.signal, AbortSignal.timeout(30000)])
    : AbortSignal.timeout(30000);
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, signal });
  } catch (error) {
    if (init.signal?.aborted) throw error;
    throw new Error(
      "No se pudo conectar con la API. Comprueba que el backend esté iniciado en el puerto 8000.",
    );
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body ? body.detail : null;
    throw new Error(
      typeof detail === "string"
        ? detail
        : "La solicitud contiene datos inválidos o el servidor no está disponible.",
    );
  }
  return body as T;
}

export const dashboardApi: DashboardGateway = {
  catalog: (signal) => request<Catalog>("/catalogo", { signal }),
  predict: (query: Query, signal) =>
    request<Dashboard>("/predecir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(query),
      signal,
    }),
  history: (signal) => request<HistoryEntry[]>("/historial", { signal }),
  report: (id, comment) =>
    request("/reportes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ consulta_id: id, comentario: comment }),
    }),
};
