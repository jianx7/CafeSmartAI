export type Section =
  | "Inicio"
  | "Recomendaciones"
  | "Ventas"
  | "Sucursales"
  | "Historial"
  | "Configuración";
export type Period = 7 | 14 | 30;
export interface Weather {
  temperatura_c: number;
  lluvia_mm: number;
  humedad_pct: number;
}
export interface Query {
  sucursal: string;
  fecha: string;
  franja: string | null;
  periodo: Period;
  clima: Weather | null;
}
export interface Catalog {
  sucursales: string[];
  franjas: string[];
  fecha_min: string;
  fecha_max: string;
  escenario_hasta: string;
  moneda: string;
  ejemplo: Query;
}
export interface Product {
  producto: string;
  categoria: string;
  unidades: number;
  nivel: "Alta" | "Media" | "Baja";
}
export interface Dashboard {
  consulta_id: number;
  sucursal: string;
  fecha: string;
  franja: string | null;
  prediccion: number;
  clase_etiqueta: string;
  confianza_o_score: number | null;
  menu_top5: Product[];
  productos: Product[];
  tiempo_ms: number;
  modelo: string;
  fuente_clima: string | null;
  clima: Weather | null;
  modo: "historico" | "escenario";
  base_ventas: { desde: string; hasta: string } | null;
  ventas_estimadas_usd: number;
  variacion_pct: number | null;
  categorias: { categoria: string; unidades: number }[];
  demanda_franjas: { franja: string; unidades: number }[];
  tendencia: { fecha: string; reales: number; estimadas: number }[];
  sucursales: {
    sucursal: string;
    unidades_reales: number | null;
    unidades_estimadas: number | null;
  }[];
}
export interface HistoryEntry {
  id: number;
  creada: string;
  entrada: Query;
  prediccion: number;
}
export interface DashboardGateway {
  catalog(signal?: AbortSignal): Promise<Catalog>;
  predict(query: Query, signal?: AbortSignal): Promise<Dashboard>;
  history(signal?: AbortSignal): Promise<HistoryEntry[]>;
  report(id: number, comment: string): Promise<{ id: number; mensaje: string }>;
}