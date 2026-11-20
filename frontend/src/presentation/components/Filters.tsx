import { useState, type FormEvent } from "react";
import { RefreshCw, Sparkles } from "lucide-react";
import type { Catalog, Period, Query } from "../../domain/dashboard";

interface Props {
  catalog: Catalog;
  initial: Query;
  loading: boolean;
  onSubmit: (query: Query) => void;
}

export function Filters({ catalog, initial, loading, onSubmit }: Props) {
  const [draft, setDraft] = useState(initial);
  const [manual, setManual] = useState(false);
  const [weather, setWeather] = useState({
    temperatura_c: 21,
    lluvia_mm: 0,
    humedad_pct: 62,
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    onSubmit({ ...draft, clima: manual ? weather : null });
  }
  function example() {
    setDraft(catalog.ejemplo);
    setManual(false);
    onSubmit(catalog.ejemplo);
  }
  return (
    <form
      onSubmit={submit}
      className="rounded-2xl border border-line bg-surface px-5 py-4"
    >
      <div className="flex flex-wrap items-end gap-3">
        <label className="field flex-1 min-w-40">
          <span>Sucursal</span>
          <select
            value={draft.sucursal}
            onChange={(e) => setDraft({ ...draft, sucursal: e.target.value })}
          >
            {catalog.sucursales.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <label className="field flex-1 min-w-40">
          <span>Fecha</span>
          <input
            required
            type="date"
            min={catalog.fecha_min}
            max={catalog.escenario_hasta}
            value={draft.fecha}
            onChange={(e) => setDraft({ ...draft, fecha: e.target.value })}
          />
          {draft.fecha > catalog.fecha_max && (
            <small className="text-[11px] text-muted">
              Posterior al dataset: se calcula como escenario.
            </small>
          )}
        </label>
        <label className="field flex-1 min-w-44">
          <span>Horario</span>
          <select
            value={draft.franja ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, franja: e.target.value || null })
            }
          >
            <option value="">Día completo</option>
            {catalog.franjas.map((time) => (
              <option key={time}>{time}</option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Histórico</span>
          <select
            value={draft.periodo}
            onChange={(e) =>
              setDraft({ ...draft, periodo: Number(e.target.value) as Period })
            }
          >
            {[7, 14, 30].map((period) => (
              <option value={period} key={period}>
                {period} días
              </option>
            ))}
          </select>
        </label>
        <button className="btn-primary" disabled={loading}>
          <Sparkles size={16} />
          {loading ? "Estimando…" : "Estimar menú"}
        </button>
        <button
          type="button"
          className="btn"
          disabled={loading}
          onClick={example}
        >
          <RefreshCw size={15} />
          Cargar ejemplo
        </button>
      </div>
      <details className="mt-3 text-xs text-muted">
        <summary className="cursor-pointer">
          Ajustar clima del escenario
        </summary>
        <label className="mt-3 flex items-center gap-2">
          <input
            type="checkbox"
            checked={manual}
            onChange={(e) => setManual(e.target.checked)}
          />
          Usar valores manuales
        </label>
        {manual && (
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            {(
              [
                {
                  key: "temperatura_c",
                  label: "Temperatura °C",
                  min: -30,
                  max: 50,
                },
                { key: "lluvia_mm", label: "Lluvia mm", min: 0, max: 300 },
                { key: "humedad_pct", label: "Humedad %", min: 0, max: 100 },
              ] as const
            ).map((field) => (
              <label key={field.key} className="field">
                <span>{field.label}</span>
                <input
                  type="number"
                  required
                  step="0.1"
                  min={field.min}
                  max={field.max}
                  value={weather[field.key]}
                  onChange={(e) =>
                    setWeather({
                      ...weather,
                      [field.key]: Number(e.target.value),
                    })
                  }
                />
              </label>
            ))}
          </div>
        )}
      </details>
    </form>
  );
}
