import { useCallback, useEffect, useState } from "react";
import type {
  Catalog,
  Dashboard,
  DashboardGateway,
  Query,
} from "../domain/dashboard";

type RemoteState =
  | { status: "idle" | "loading" }
  | { status: "success"; data: Dashboard }
  | { status: "error"; message: string };

export function useDashboard(gateway: DashboardGateway) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [catalogError, setCatalogError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [task, setTask] = useState<{ query: Query; version: number } | null>(
    null,
  );
  const [state, setState] = useState<RemoteState>({ status: "idle" });

  useEffect(() => {
    const controller = new AbortController();
    setCatalogError("");
    gateway
      .catalog(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setCatalog(result);
        setTask({ query: result.ejemplo, version: 0 });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setCatalogError(
            error instanceof Error
              ? error.message
              : "No se pudo cargar el catálogo.",
          );
      });
    return () => controller.abort();
  }, [gateway, attempt]);

  useEffect(() => {
    if (!task) return;
    const controller = new AbortController();
    setState({ status: "loading" });
    gateway
      .predict(task.query, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ status: "success", data });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setState({
            status: "error",
            message:
              error instanceof Error ? error.message : "Falló la estimación.",
          });
      });
    return () => controller.abort();
  }, [gateway, task]);

  const submit = useCallback(
    (query: Query) =>
      setTask((previous) => ({ query, version: (previous?.version ?? 0) + 1 })),
    [],
  );
  const retry = () => {
    if (catalog && task) submit(task.query);
    else setAttempt((value) => value + 1);
  };
  return { catalog, catalogError, state, submit, retry, query: task?.query };
}
