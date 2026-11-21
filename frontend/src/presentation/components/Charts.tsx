import { Download } from "lucide-react";
import type { Dashboard } from "../../domain/dashboard";
import { Card, categoryNames, day, number } from "./ui";

const colors = ["#79563f", "#8eabb5", "#bba170", "#677f6b"];

export function CategoryChart({ data }: { data: Dashboard["categorias"] }) {
  const total = data.reduce((sum, item) => sum + item.unidades, 0);
  let start = 0;
  const gradient = data
    .map((item, index) => {
      const end = start + (total ? (item.unidades / total) * 100 : 0);
      const segment = `${colors[index % colors.length]} ${start}% ${end}%`;
      start = end;
      return segment;
    })
    .join(",");
  return (
    <Card>
      <h2 className="font-semibold">Unidades por categoría</h2>
      <div className="mt-5 flex flex-wrap items-center justify-center gap-7">
        <div
          className="grid size-36 place-items-center rounded-full"
          role="img"
          aria-label={`Distribución de ${number(total)} unidades estimadas`}
          style={{
            background: total
              ? `conic-gradient(${gradient})`
              : "var(--color-line)",
          }}
        >
          <div className="grid size-25 place-content-center rounded-full bg-surface text-center">
            <strong className="text-xl">{number(total)}</strong>
            <span className="text-xs text-muted">unidades</span>
          </div>
        </div>
        <ul className="grid gap-3 text-xs">
          {data.map((item, index) => (
            <li key={item.categoria} className="flex items-center gap-2">
              <i
                className="size-2 rounded-full"
                style={{ background: colors[index % colors.length] }}
              />
              <span>{categoryNames[item.categoria] ?? item.categoria}</span>
              <strong className="ml-auto pl-3">
                {total ? Math.round((item.unidades / total) * 100) : 0}%
              </strong>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}

export function TrendChart({
  data,
  manual,
  onDownload,
}: {
  data: Dashboard["tendencia"];
  manual: boolean;
  onDownload?: () => void;
}) {
  const max =
    Math.max(1, ...data.flatMap((point) => [point.reales, point.estimadas])) *
    1.1;
  const x = (i: number) => 55 + (i * 620) / Math.max(1, data.length - 1);
  const y = (value: number) => 205 - (value / max) * 170;
  const points = (key: "reales" | "estimadas") =>
    data.map((p, i) => `${x(i)},${y(p[key])}`).join(" ");
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold">Ventas reales y estimadas</h2>
          <p className="mt-1 text-xs text-muted">
            Unidades · periodo de prueba disponible
          </p>
        </div>
        {onDownload && (
          <button
            type="button"
            className="btn"
            disabled={data.length === 0}
            onClick={onDownload}
          >
            <Download size={15} />
            Descargar reporte
          </button>
        )}
      </div>
      <svg
        viewBox="0 0 720 245"
        role="img"
        aria-label="Tendencia de unidades reales y estimadas"
        className="mt-3 w-full"
      >
        {[0, 0.5, 1].map((ratio) => (
          <g key={ratio}>
            <line
              x1="55"
              y1={y(max * ratio)}
              x2="675"
              y2={y(max * ratio)}
              stroke="var(--color-line)"
            />
            <text
              x="45"
              y={y(max * ratio) + 4}
              textAnchor="end"
              fontSize="11"
              fill="var(--color-muted)"
            >
              {Math.round(max * ratio)}
            </text>
          </g>
        ))}
        <polyline
          fill="none"
          stroke="#8eabb5"
          strokeWidth="3"
          points={points("reales")}
        />
        <polyline
          fill="none"
          stroke="#79563f"
          strokeWidth="2.5"
          strokeDasharray="6 5"
          points={points("estimadas")}
        />
        {data.map((point, i) => (
          <circle
            key={point.fecha}
            cx={x(i)}
            cy={y(point.estimadas)}
            r="3.5"
            fill="#79563f"
          >
            <title>
              {day(point.fecha)} · real {number(point.reales)} · estimada{" "}
              {number(point.estimadas)}
            </title>
          </circle>
        ))}
        {data.length > 0 && (
          <>
            <text x="55" y="230" fontSize="11" fill="var(--color-muted)">
              {day(data[0].fecha)}
            </text>
            <text
              x="675"
              y="230"
              fontSize="11"
              fill="var(--color-muted)"
              textAnchor="end"
            >
              {day(data[data.length - 1].fecha)}
            </text>
          </>
        )}
      </svg>
      <div className="flex gap-5 text-xs text-muted">
        <span className="flex items-center gap-2">
          <i className="h-0.5 w-5 bg-[#8eabb5]" />
          Real
        </span>
        <span className="flex items-center gap-2">
          <i className="h-0.5 w-5 bg-[#79563f]" />
          Estimada
        </span>
      </div>
      {manual && (
        <p className="mt-3 text-xs text-muted">
          La tendencia conserva las estimaciones de prueba con clima histórico.
          El ajuste manual corresponde a la consulta actual.
        </p>
      )}
      <details className="mt-3 text-xs">
        <summary className="cursor-pointer text-muted">Ver valores</summary>
        <table className="data-table mt-2">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Real</th>
              <th>Estimada</th>
            </tr>
          </thead>
          <tbody>
            {data.map((p) => (
              <tr key={p.fecha}>
                <td>{p.fecha}</td>
                <td>{number(p.reales)}</td>
                <td>{number(p.estimadas)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </Card>
  );
}

export function TopChart({ products }: { products: Dashboard["menu_top5"] }) {
  const max = Math.max(1, ...products.map((p) => p.unidades));
  return (
    <Card>
      <h2 className="font-semibold">Demanda del menú recomendado</h2>
      <div className="mt-5 grid gap-4">
        {products.map((p) => (
          <div key={p.producto}>
            <div className="mb-1 flex justify-between gap-3 text-xs">
              <span>{p.producto}</span>
              <strong>{number(p.unidades)}</strong>
            </div>
            <div className="h-2 rounded-full bg-canvas">
              <div
                className="h-2 rounded-full bg-coffee"
                style={{ width: `${(p.unidades / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function TimeBandChart({
  data,
}: {
  data: Dashboard["demanda_franjas"];
}) {
  const max = Math.max(1, ...data.map((band) => band.unidades));
  return (
    <Card>
      <h2 className="font-semibold">Demanda por franja horaria</h2>
      <div className="mt-6 flex h-48 items-end justify-around gap-4">
        {data.map((band) => (
          <div
            key={band.franja}
            className="flex h-full flex-1 flex-col items-center justify-end gap-2"
          >
            <strong className="text-sm">{number(band.unidades)}</strong>
            <div
              className="w-full max-w-16 rounded-t-md bg-[#8eabb5]"
              style={{ height: `${(band.unidades / max) * 120}px` }}
            />
            <span className="text-center text-xs text-muted">
              {band.franja}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs leading-relaxed text-muted">
        Cada barra usa el modelo por franja. El total diario se estima con un
        modelo entrenado a otra granularidad.
      </p>
    </Card>
  );
}
