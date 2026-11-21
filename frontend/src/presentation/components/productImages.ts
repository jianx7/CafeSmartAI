// Carga todas las fotos de src/images y las asocia con el producto del modelo.
const files = import.meta.glob("../../images/*.{jpg,jpeg,png,webp}", {
  eager: true,
  query: "?url",
  import: "default",
}) as Record<string, string>;

// Producto del modelo -> patrón que debe cumplir el nombre del archivo.
const rules: [string, RegExp][] = [
  ["Barista Espresso", /barista/],
  ["Biscotti", /biscotti/],
  ["Brewed Black tea", /black/],
  ["Brewed Chai tea", /chai/],
  ["Brewed Green tea", /green/],
  ["Brewed herbal tea", /herbal/],
  ["Drip coffee", /drip/],
  ["Gourmet brewed coffee", /gourmet/],
  ["Hot chocolate", /chocolate/],
  ["Organic brewed coffee", /organic/],
  ["Pastry", /pastry/],
  ["Premium brewed coffee", /^brewed/],
  ["Scone", /scone/],
];

const byFile = Object.entries(files).map(
  ([path, url]) =>
    [(path.split("/").pop() ?? path).toLowerCase(), url] as const,
);

export function productImage(product: string): string | undefined {
  const rule = rules.find(([name]) => name === product);
  if (!rule) return undefined;
  return byFile.find(([file]) => rule[1].test(file))?.[1];
}