import { useState, type FormEvent } from "react";
import type { DashboardGateway } from "../../domain/dashboard";
import { Card, PageTitle } from "../components/ui";

interface Props {
  dark: boolean;
  onThemeChange: () => void;
  gateway: DashboardGateway;
  queryId: number | null;
}

export function Settings({ dark, onThemeChange, gateway, queryId }: Props) {
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState("");
  const [sending, setSending] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (queryId === null) return;
    setSending(true);
    setStatus("");
    try {
      const result = await gateway.report(queryId, comment);
      setStatus(`Reporte #${result.id} guardado para la consulta #${queryId}.`);
      setComment("");
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "No se pudo guardar el reporte.",
      );
    } finally {
      setSending(false);
    }
  }
  return (
    <>
      <PageTitle title="Configuración">
        Preferencias de visualización y reporte de resultados.
      </PageTitle>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-semibold">Apariencia</h2>
            <p className="mt-1 text-sm text-muted">
              La preferencia se guarda en este navegador.
            </p>
          </div>
          <button className="btn" aria-pressed={dark} onClick={onThemeChange}>
            {dark ? "Usar tema claro" : "Usar tema oscuro"}
          </button>
        </div>
      </Card>
      <Card>
        <h2 className="font-semibold">Reportar resultado</h2>
        <p className="mt-2 text-sm text-muted">
          {queryId === null
            ? "Ejecuta una estimación para asociarle un reporte."
            : `El comentario se asociará a la consulta #${queryId}.`}
        </p>
        <form onSubmit={submit} className="mt-4 grid gap-3">
          <label className="field">
            <span>Describe el problema observado</span>
            <textarea
              required
              minLength={5}
              maxLength={2000}
              rows={4}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </label>
          <button
            className="btn-primary justify-self-start"
            disabled={queryId === null || sending}
          >
            {sending ? "Guardando…" : "Guardar reporte"}
          </button>
          <p role="status" className="text-sm text-muted">
            {status}
          </p>
        </form>
      </Card>
    </>
  );
}
