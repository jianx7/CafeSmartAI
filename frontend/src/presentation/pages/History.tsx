import { useEffect, useState } from "react";
import type { DashboardGateway, HistoryEntry } from "../../domain/dashboard";
import { Card, ErrorState, PageTitle, day, number } from "../components/ui";

export function History({ gateway }: { gateway: DashboardGateway }) {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    setEntries(null);
    gateway
      .history(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setEntries(result);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error
              ? err.message
              : "No se pudo cargar el historial.",
          );
      });
    return () => controller.abort();
  }, [gateway, attempt]);
  return (
    <>
      <PageTitle title="Historial de consultas">
        Últimas 100 estimaciones guardadas en el backend local.
      </PageTitle>
      {error ? (
        <ErrorState message={error} retry={() => setAttempt((n) => n + 1)} />
      ) : (
        <Card>
          {entries === null ? (
            <p role="status">Cargando historial…</p>
          ) : entries.length === 0 ? (
            <p>Aún no hay consultas registradas.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Consulta</th>
                    <th>Sucursal</th>
                    <th>Fecha estimada</th>
                    <th>Horario</th>
                    <th>Unidades</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id}>
                      <td>#{entry.id}</td>
                      <td>{entry.entrada.sucursal}</td>
                      <td>{day(entry.entrada.fecha)}</td>
                      <td>{entry.entrada.franja ?? "Día completo"}</td>
                      <td>{number(entry.prediccion)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </>
  );
}
