import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`min-w-0 rounded-2xl border border-line bg-surface p-5 shadow-sm ${className}`}
    >
      {children}
    </section>
  );
}
export const number = (value: number) =>
  new Intl.NumberFormat("es-MX", { maximumFractionDigits: 1 }).format(value);
export const money = (value: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "USD" }).format(
    value,
  );
export const day = (value: string) =>
  new Date(`${value}T12:00:00`).toLocaleDateString("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
export const categoryNames: Record<string, string> = {
  Coffee: "Café",
  Tea: "Té",
  Bakery: "Panadería",
  "Drinking Chocolate": "Chocolate",
};
export function PageTitle({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
        {title}
      </h1>
      {children && <p className="mt-2 text-sm text-muted">{children}</p>}
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry: () => void;
}) {
  return (
    <Card className="mx-auto mt-8 max-w-xl">
      <h2 className="font-semibold">No se pudo completar la consulta</h2>
      <p role="alert" className="my-4 text-sm text-muted">
        {message}
      </p>
      <button className="btn-primary" onClick={retry}>
        Reintentar
      </button>
    </Card>
  );
}
