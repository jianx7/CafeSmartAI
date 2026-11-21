import { useState } from "react";
import { ArrowRight, Coffee, CloudSun, TrendingUp } from "lucide-react";
import type { Dashboard, Section } from "../../domain/dashboard";
import {
  Card,
  PageTitle,
  categoryNames,
  day,
  money,
  number,
} from "../components/ui";
import {
  CategoryChart,
  TimeBandChart,
  TopChart,
  TrendChart,
} from "../components/Charts";
import { downloadSalesCsv } from "../components/downloadCsv";

interface Props {
  data: Dashboard;
  goTo: (section: Section) => void;
  manual: boolean;
}
import { productImage } from "../components/productImages";

export function ScenarioNotice({ data }: { data: Dashboard }) {
  if (data.modo !== "escenario") return null;
  return (
    <div
      role="note"
      className="rounded-2xl border border-line bg-sand-soft px-5 py-4 text-sm leading-relaxed"
    >
      <strong>Escenario, no pronóstico validado.</strong> {day(data.fecha)} es
      posterior al dataset. La estimación usa como base las ventas del{" "}
      {data.base_ventas ? day(data.base_ventas.desde) : "último periodo"} al{" "}
      {data.base_ventas ? day(data.base_ventas.hasta) : "disponible"}, más el
      día de la semana y el mes de la fecha elegida.{" "}
      {data.fuente_clima === "entrada"
        ? "Incluye el clima que ingresaste."
        : "Sin clima manual, el modelo no usa variables climáticas."}
    </div>
  );
}

export function Home({ data, goTo, manual }: Props) {
  return (
    <>
      <ScenarioNotice data={data} />
      <div className="grid gap-5 xl:grid-cols-3">
        <Card className="bg-sky-soft">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Resumen de la estimación</h2>
            <TrendingUp size={18} />
          </div>
          <p className="mt-5 text-3xl font-semibold tracking-tight">
            {money(data.ventas_estimadas_usd)}
          </p>
          <p className="mt-2 text-xs text-muted">
            USD · precio medio ponderado del entrenamiento
          </p>
          <div className="mt-5 grid grid-cols-2 gap-4 border-t border-line pt-4">
            <div>
              <span className="text-xs text-muted">Unidades estimadas</span>
              <strong className="mt-1 block text-xl">
                {number(data.prediccion)}
              </strong>
            </div>
            <div>
              <span className="text-xs text-muted">
                {data.modo === "escenario"
                  ? "Frente al promedio base"
                  : "Frente a los 7 días previos"}
              </span>
              <strong className="mt-1 block text-xl">
                {data.variacion_pct === null
                  ? "Sin referencia"
                  : `${data.variacion_pct > 0 ? "+" : ""}${number(data.variacion_pct)} %`}
              </strong>
            </div>
          </div>
        </Card>
        <CategoryChart data={data.categorias} />
        <Card className="flex flex-col bg-sand-soft">
          <span className="flex items-center gap-2 text-xs font-semibold">
            <CloudSun size={17} />
            Clima del escenario
          </span>
          {data.clima ? (
            <>
              <h2 className="mt-4 text-2xl font-semibold">
                {number(data.clima.temperatura_c)} °C
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                Lluvia {number(data.clima.lluvia_mm)} mm · humedad{" "}
                {number(data.clima.humedad_pct)} %
              </p>
            </>
          ) : (
            <>
              <h2 className="mt-4 text-2xl font-semibold">Sin clima</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">
                No hay clima histórico para esta fecha. Usa «Ajustar clima del
                escenario» para simular uno.
              </p>
            </>
          )}
          <p className="my-4 text-sm">
            Prioriza los tipos con más unidades estimadas. {data.clase_etiqueta}{" "}
            frente al historial reciente.
          </p>
          <button
            className="btn-primary mt-auto self-start"
            onClick={() => goTo("Recomendaciones")}
          >
            Ver sugerencias
            <ArrowRight size={15} />
          </button>
        </Card>
      </div>
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold">El menú recomendado</h2>
          <button
            className="text-sm font-medium text-coffee hover:underline"
            onClick={() => goTo("Recomendaciones")}
          >
            Ver todos los tipos →
          </button>
        </div>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {data.menu_top5.map((product) => {
            const photo = productImage(product.producto);
            return (
              <article
                key={product.producto}
                className={`relative isolate overflow-hidden rounded-xl border border-line p-4 ${
                  photo
                    ? "text-white [text-shadow:0_1px_3px_rgba(0,0,0,0.7)]"
                    : "bg-canvas"
                }`}
              >
                {photo && (
                  <>
                    <img
                      src={photo}
                      alt=""
                      loading="lazy"
                      className="absolute inset-0 -z-20 h-full w-full object-cover"
                    />
                    <div
                      aria-hidden="true"
                      className="absolute inset-0 -z-10"
                      style={{
                        backgroundImage:
                          "linear-gradient(to top, rgba(20,12,8,0.9) 0%, rgba(20,12,8,0.6) 55%, rgba(20,12,8,0.3) 100%)",
                      }}
                    />
                  </>
                )}
                <Coffee
                  className={`mb-4 ${photo ? "text-white" : "text-coffee"}`}
                  size={24}
                />
                <p
                  className={`text-xs ${photo ? "text-white/90" : "text-muted"}`}
                >
                  {categoryNames[product.categoria]}
                </p>
                <h3 className="mt-1 min-h-10 text-sm font-semibold">
                  {product.producto}
                </h3>
                <p className="mt-4 text-2xl font-semibold">
                  {number(product.unidades)}
                </p>
                <p
                  className={`text-xs ${photo ? "text-white/90" : "text-muted"}`}
                >
                  unidades estimadas
                </p>
                <span
                  className={`mt-3 inline-block rounded-full px-2.5 py-1 text-xs ${
                    photo
                      ? "bg-white/90 text-[#332d29] [text-shadow:none]"
                      : "bg-sand-soft"
                  }`}
                >
                  Demanda {product.nivel.toLowerCase()}
                </span>
              </article>
            );
          })}
        </div>
      </Card>
      <div className="grid gap-5 lg:grid-cols-2">
        <TimeBandChart data={data.demanda_franjas} />
        <TrendChart data={data.tendencia} manual={manual} />
      </div>
    </>
  );
}

export function Recommendations({ data }: { data: Dashboard }) {
  const [category, setCategory] = useState("Todas");
  const categories = [
    "Todas",
    ...new Set(data.productos.map((p) => p.categoria)),
  ];
  const filtered = data.productos.filter(
    (p) => category === "Todas" || p.categoria === category,
  );
  return (
    <>
      <PageTitle title="Recomendaciones inteligentes">
        Menú ordenado por unidades estimadas para {day(data.fecha)} ·{" "}
        {data.franja ?? "día completo"}.
      </PageTitle>
      <ScenarioNotice data={data} />
      <Card>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-semibold">Todos los tipos de producto</h2>
          <label className="field">
            <span>Categoría</span>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((name) => (
                <option value={name} key={name}>
                  {categoryNames[name] ?? name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tipo de producto</th>
                <th>Categoría</th>
                <th>Unidades estimadas</th>
                <th>Demanda</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.producto}>
                  <td className="font-medium">{p.producto}</td>
                  <td>{categoryNames[p.categoria]}</td>
                  <td>{number(p.unidades)}</td>
                  <td>{p.nivel}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <TopChart products={data.menu_top5} />
      <Card>
        <h2 className="font-semibold">Cómo interpretar el menú</h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">
          El modelo estima tipos de producto del dataset. El nivel compara las
          unidades estimadas con la media de los siete días previos de la misma
          sucursal y horario. La estimación sirve como referencia de preparación
          y requiere revisión del personal.
        </p>
        <p className="mt-3 text-xs text-muted">
          Modelo {data.modelo} · inferencia {data.tiempo_ms} ms · fuente
          climática{" "}
          {data.fuente_clima === "entrada"
            ? "escenario manual"
            : data.fuente_clima === "historico"
              ? "histórico ERA5"
              : "no utilizada"}
          .
        </p>
      </Card>
    </>
  );
}

export function Sales({ data, manual }: { data: Dashboard; manual: boolean }) {
  return (
    <>
      <PageTitle title="Análisis de ventas">
        Comparación retrospectiva de unidades en el periodo de prueba.
      </PageTitle>
      {data.modo === "escenario" ? (
        <Card>
          <h2 className="font-semibold">Sin ventas reales para esta fecha</h2>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            La comparación de unidades reales y estimadas solo existe para el
            periodo de prueba (26 de mayo al 30 de junio de 2023). Elige una
            fecha de ese periodo para verla.
          </p>
        </Card>
      ) : (
        <TrendChart
          data={data.tendencia}
          manual={manual}
          onDownload={() => downloadSalesCsv(data)}
        />
      )}
    </>
  );
}

export function Branches({ data }: { data: Dashboard }) {
  return (
    <>
      <PageTitle title="Sucursales de Nueva York">
        {data.modo === "escenario"
          ? "Unidades estimadas del día completo"
          : "Unidades reales del día completo"}{" "}
        · {day(data.fecha)}.
      </PageTitle>
      <Card>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sucursal</th>
                <th>
                  {data.modo === "escenario"
                    ? "Unidades estimadas"
                    : "Unidades vendidas"}
                </th>
              </tr>
            </thead>
            <tbody>
              {data.sucursales.map((row) => (
                <tr key={row.sucursal}>
                  <td className="font-medium">{row.sucursal}</td>
                  <td>
                    {number(row.unidades_reales ?? row.unidades_estimadas ?? 0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-xs text-muted">
          Para estimar una sucursal, selecciónala en los filtros y pulsa Estimar
          menú.
        </p>
      </Card>
    </>
  );
}
