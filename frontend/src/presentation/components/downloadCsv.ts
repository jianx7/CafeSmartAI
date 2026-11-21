import type { Dashboard } from "../../domain/dashboard";

// Entrecomilla los valores que lo necesitan (comas, comillas o saltos de línea).
function cell(value: string | number): string {
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function salesCsv(data: Dashboard): string {
  const header = [
    "sucursal",
    "horario",
    "fecha",
    "unidades_reales",
    "unidades_estimadas",
    "modelo",
  ];
  const rows = data.tendencia.map((point) => [
    data.sucursal,
    data.franja ?? "Día completo",
    point.fecha,
    point.reales,
    point.estimadas,
    data.modelo,
  ]);
  return [header, ...rows].map((row) => row.map(cell).join(",")).join("\r\n");
}

export function downloadSalesCsv(data: Dashboard): void {
  if (data.tendencia.length === 0) return;
  const slug = data.sucursal
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  const first = data.tendencia[0].fecha;
  const last = data.tendencia[data.tendencia.length - 1].fecha;
  // El BOM inicial hace que Excel abra bien los acentos.
  const blob = new Blob(["\ufeff" + salesCsv(data)], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `ventas_${slug}_${first}_${last}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}