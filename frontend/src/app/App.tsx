import { useEffect, useState } from "react";
import {
  House,
  Sparkles,
  ChartNoAxesCombined,
  Store,
  History as HistoryIcon,
  Settings as SettingsIcon,
} from "lucide-react";
import type { Section } from "../domain/dashboard";
import { useDashboard } from "../application/useDashboard";
import { dashboardApi } from "../infrastructure/api";
import { Filters } from "../presentation/components/Filters";
import { Card, ErrorState, day } from "../presentation/components/ui";
import {
  Home,
  Recommendations,
  Sales,
  Branches,
} from "../presentation/pages/DashboardPages";
import { History } from "../presentation/pages/History";
import { Settings } from "../presentation/pages/Settings";

const navigation = [
  { name: "Inicio", icon: House },
  { name: "Recomendaciones", icon: Sparkles },
  { name: "Ventas", icon: ChartNoAxesCombined },
  { name: "Sucursales", icon: Store },
  { name: "Historial", icon: HistoryIcon },
  { name: "Configuración", icon: SettingsIcon },
] satisfies { name: Section; icon: typeof House }[];

function initialTheme() {
  try {
    return localStorage.getItem("cafesmart-theme") === "dark";
  } catch {
    return false;
  }
}

export default function App() {
  const [section, setSection] = useState<Section>("Inicio");
  const [dark, setDark] = useState(initialTheme);
  const { catalog, catalogError, state, submit, retry, query } =
    useDashboard(dashboardApi);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    try {
      localStorage.setItem("cafesmart-theme", dark ? "dark" : "light");
    } catch {
      /* El tema funciona durante esta sesión. */
    }
  }, [dark]);
  const data = state.status === "success" ? state.data : null;
  const independentPage =
    section === "Historial" || section === "Configuración";
  return (
    <div className="min-h-screen lg:pl-60">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:bg-surface focus:p-3"
      >
        Saltar al contenido
      </a>
      <aside className="border-b border-line bg-surface p-4 lg:fixed lg:inset-y-0 lg:left-0 lg:w-60 lg:border-b-0 lg:border-r lg:px-5 lg:py-9">
        <div className="flex items-center gap-3 px-2">
          <img src="/CafeSmartIA.svg" alt="CaféSmart AI Logo" className="h-8 w-8 object-contain" />
          <span className="text-xl font-semibold tracking-tight">
            CaféSmart <small className="text-xs text-coffee">AI</small>
          </span>
        </div>
        <nav
          aria-label="Navegación principal"
          className="mt-5 flex flex-wrap gap-1 lg:mt-14 lg:grid lg:gap-2"
        >
          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              aria-current={section === name ? "page" : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition-colors ${section === name ? "bg-sand-soft font-semibold text-ink" : "text-muted hover:bg-canvas hover:text-ink"}`}
              onClick={() => setSection(name)}
            >
              <Icon size={18} />
              {name}
            </button>
          ))}
        </nav>
        <p className="mt-10 hidden border-t border-line px-2 pt-4 text-xs leading-relaxed text-muted lg:block">
          Menú estimado con el historial de ventas de tus cafeterías.
        </p>
      </aside>
      <main
        id="contenido"
        className="mx-auto max-w-375 px-4 py-6 md:px-8 md:py-8"
      >
        <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-2xl font-semibold tracking-tight">CaféSmart</p>
            <p className="mt-1 text-sm text-muted">
              Dashboard de menús y ventas
            </p>
          </div>
          <span className="rounded-full border border-line bg-surface px-3 py-2 text-xs text-muted">
            Evaluación histórica · Nueva York · USD
          </span>
        </header>
        <div className="grid gap-5">
          {catalog && !independentPage && (
            <Filters
              catalog={catalog}
              initial={catalog.ejemplo}
              loading={state.status === "loading"}
              onSubmit={submit}
            />
          )}
          {section === "Historial" ? (
            <History gateway={dashboardApi} />
          ) : section === "Configuración" ? (
            <Settings
              dark={dark}
              onThemeChange={() => setDark((v) => !v)}
              gateway={dashboardApi}
              queryId={data?.consulta_id ?? null}
            />
          ) : catalogError ? (
            <ErrorState message={catalogError} retry={retry} />
          ) : state.status === "error" ? (
            <ErrorState message={state.message} retry={retry} />
          ) : !data ? (
            <Card>
              <p
                role="status"
                aria-live="polite"
                className="py-12 text-center text-muted"
              >
                Preparando estimación…
              </p>
            </Card>
          ) : (
            <>
              <p className="text-sm text-muted" role="status">
                {data.sucursal} · {day(data.fecha)} ·{" "}
                {data.franja ?? "día completo"}
              </p>
              {section === "Inicio" && (
                <Home
                  data={data}
                  goTo={setSection}
                  manual={query?.clima !== null}
                />
              )}
              {section === "Recomendaciones" && <Recommendations data={data} />}
              {section === "Ventas" && (
                <Sales data={data} manual={query?.clima !== null} />
              )}
              {section === "Sucursales" && <Branches data={data} />}
              <p className="text-xs leading-relaxed text-muted">
                Resultado automatizado con datos de 2023. Revisa las cantidades
                antes de tomar decisiones de preparación.
              </p>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
